"""Style the five original pwO3 120 mm 3MF bodies as a fusion-station cutaway.

Requires NumPy, Pillow, SciPy, VTK, and a C++17 compiler.
Pass the original pwO3_120mm_multicolor.3mf assembly with --source.
"""
import argparse
from functools import partial
from hashlib import sha256
from math import atan2, cos, sin, radians
from pathlib import Path
from xml.parsers import expat
from zipfile import ZipFile

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals, vtkQuadricDecimation

from build import DEFAULT_DIR, bake
from geometry import Model, axis_basis
from interfaces import screw

STEM='pwo3_stellarator_cutaway'
SCALE=.065  # studio units per millimetre
YAW=-2.45
PITCH=-radians(27)
STUDIO_LIGHTS=(('Warm softbox',(-.49,-.69,.82),'FFF4E8',1.17),
               ('Cyan rim',(.91,.66,.74),'48CAE4',.66),
               ('Section fill',(.18,-.90,.42),'DFEEEF',.24))
SURFACES={'vessel':('Vacuum_Vessel','satin_enamel'),'blanket':('Blanket','graphite'),
          'first_wall':('First_Wall','titanium'),'plasma':('Plasma','lcfs')}


def read_assembly(path):
    """Read native mesh indices and verify the single, identity-placed assembly."""
    bodies={}
    by_id={}
    assemblies={}
    build_items=[]
    name=None
    object_id=None
    points=[]
    triangles=[]

    def start(tag,a):
        nonlocal name,object_id
        if tag=='model' and a.get('unit')!='millimeter':
            raise ValueError('Expected the millimetre pwO3 teaching model')
        if tag in ('component','item') and 'transform' in a:
            raise ValueError('This pwO3 reader expects identity component placements')
        if tag=='object':
            name=a['name']
            object_id=a['id']
        elif tag=='vertex':
            points.append((float(a['x']),float(a['y']),float(a['z'])))
        elif tag=='triangle':
            triangles.append((int(a['v1']),int(a['v2']),int(a['v3'])))
        elif tag=='component':
            assemblies.setdefault(object_id,[]).append(a['objectid'])
        elif tag=='item':
            build_items.append(a['objectid'])

    def end(tag):
        if tag=='mesh':
            by_id[object_id]=name
            bodies[name]=np.array(points),np.array(triangles,dtype=np.int32)
            points.clear()
            triangles.clear()

    parser=expat.ParserCreate()
    parser.StartElementHandler=start
    parser.EndElementHandler=end
    with ZipFile(path) as archive, archive.open('3D/3dmodel.model') as f:
        parser.ParseFile(f)
    if (len(build_items)!=1 or sorted(assemblies.get(build_items[0],[]))!=sorted(by_id)
            or set(bodies)!=set(SURFACES)|{'coils'}):
        raise ValueError('Expected one assembly containing the five original pwO3 bodies')
    return bodies


def add_native_mesh(model,path,material,v,f):
    # Keep the original winding faces. Simplify the heavy CAD wall meshes before
    # splitting normals so the GLB retains continuous surfaces and crisp cut faces.
    points=vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(v*SCALE),deep=True))
    cells=vtkCellArray()
    cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(f)+1,3,dtype=np.int64),deep=True),
                  numpy_to_vtkIdTypeArray(np.ascontiguousarray(f,dtype=np.int64).ravel(),deep=True))
    surface=vtkPolyData()
    surface.SetPoints(points)
    surface.SetPolys(cells)
    normals=vtkPolyDataNormals()
    if material=='amber':
        normals.SetInputData(surface)
    else:
        decimator=vtkQuadricDecimation()
        decimator.SetInputData(surface)
        decimator.SetTargetReduction(.85)
        decimator.VolumePreservationOn()
        normals.SetInputConnection(decimator.GetOutputPort())
    normals.SetFeatureAngle(38)
    normals.ConsistencyOff()
    normals.SplittingOn()
    normals.ComputePointNormalsOn()
    normals.Update()
    mesh=normals.GetOutput()
    vertices=vtk_to_numpy(mesh.GetPoints().GetData()).copy()
    direction=vtk_to_numpy(mesh.GetPointData().GetNormals()).copy()
    faces=vtk_to_numpy(mesh.GetPolys().GetConnectivityArray()).reshape(-1,3).copy()
    if not len(faces) or not np.isfinite(direction).all():
        raise ValueError('Unexpected normals or topology change')
    # Some sub-micron source slivers produce a zero averaged normal in VTK.
    bad=np.linalg.norm(direction,axis=1)<.5
    if bad.any():
        adj=faces[bad[faces].any(axis=1)]
        a,b,c=vertices[adj].transpose(1,0,2)
        cross=np.cross(b-a,c-a)
        for index in np.argsort(np.linalg.norm(cross,axis=1)):
            tri,n=adj[index],cross[index]
            size=np.linalg.norm(n)
            if size>0:
                direction[tri[bad[tri]]]=n/size
    if np.any(np.linalg.norm(direction,axis=1)<.99):
        raise ValueError('Unresolved vertex normal in source mesh')
    if material=='amber':
        # The four hard-edged side strips of each rectangular winding are disjoint
        # after normal splitting. Use the brighter orange only on the protective edges.
        n,labels=mesh_components(vertices,faces)
        if n!=4:
            raise ValueError(f'{path} has {n} side strips instead of four')
        a,b,c=vertices[faces].transpose(1,0,2)
        area=np.linalg.norm(np.cross(b-a,c-a),axis=1)
        strip=labels[faces[:,0]]
        broad=np.isin(strip,np.argsort(np.bincount(strip,weights=area))[-2:])
        for mat,mask in [('amber',broad),('orange',~broad)]:
            model.parts[path][mat].append((vertices,direction,faces[mask]))
    else:
        model.parts[path][material].append((vertices,direction,faces))


def add_cut_lips(model,path,verts,faces,angles,radius_mm):
    """Round metal edge bands on the actual annular CAD end faces."""
    for angle in angles:
        phi=radians(angle)
        radial=np.array([cos(phi),sin(phi),0])
        normal=np.array([-sin(phi),cos(phi),0])
        on_plane=(np.abs(verts@normal)<.00006)&(verts@radial>0)
        cap=faces[np.all(on_plane[faces],axis=1)]
        edges=np.vstack((cap[:,[0,1]],cap[:,[1,2]],cap[:,[2,0]]))
        edges,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
        adjacent={}
        for a,b in edges[counts==1]:
            adjacent.setdefault(a,[]).append(b)
            adjacent.setdefault(b,[]).append(a)
        if not adjacent or any(len(v)!=2 for v in adjacent.values()):
            raise ValueError(f'Broken cut profile at {angle} degrees in {path}')
        while adjacent:
            first=next(iter(adjacent))
            current=first
            previous=None
            ordered=[]
            while True:
                ordered.append(current)
                left,right=adjacent.pop(current)
                previous,current=current,right if left==previous else left
                if current==first:
                    break
            points=verts[ordered+[first]]
            length=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
            sample=np.arange(192)*length[-1]/192
            profile=np.column_stack([np.interp(sample,length,points[:,dim]) for dim in range(3)])
            profile=gaussian_filter1d(profile,.70,axis=0,mode='wrap')
            tangent=np.roll(profile,-1,axis=0)-np.roll(profile,1,axis=0)
            tangent/=np.linalg.norm(tangent,axis=1)[:,None]
            side=np.cross(tangent,normal)
            t=np.arange(10)*2*np.pi/10
            ring=(profile[:,None,:]+radius_mm*(np.cos(t)[None,:,None]*normal
                  +np.sin(t)[None,:,None]*side[:,None,:]))*SCALE
            ids=np.arange(len(profile)*len(t)).reshape(len(profile),len(t))
            along=np.roll(ids,-1,axis=0)
            polygons=np.stack([ids,np.roll(ids,-1,axis=1),np.roll(along,-1,axis=1),along],axis=-1)
            model.mesh(path+'/Bevel_Trim','steel',ring.reshape(-1,3),polygons.reshape(-1,4),True)


def mesh_components(vertices,faces):
    links=coo_matrix((np.ones(faces.size,dtype=bool),
                      (faces.ravel(),np.roll(faces,-1,axis=1).ravel())),
                     shape=(len(vertices),len(vertices))).tocsr()
    return connected_components(links,directed=False)


def coils_and_supports(m,vertices,faces):
    count,labels=mesh_components(vertices,faces)
    if count!=16:
        raise ValueError(f'Expected 16 cutaway coils, got {count}')
    for i in range(count):
        v_ids=np.flatnonzero(labels==i)
        v=vertices[v_ids]
        f=np.searchsorted(v_ids,faces[labels[faces[:,0]]==i])
        add_native_mesh(m,f'pwO3/Coils/Winding_{i+1:02d}','amber',v,f)
        x,y,z=v[np.argmin(v[:,2])]*SCALE
        group=f'Coil_Mounting_Shoes/Shoe_{i+1:02d}'
        m.box(group,'titanium',(x,y,-.17),(.39,.31,.080),.018,.045)
        for dx in (-.135,.135):
            for dy in (-.094,.094):
                m.rod(group,'anodized',(x+dx,y+dy,-.136),(x+dx,y+dy,-.11),.035,6)
        m.turned(group,'steel',(x,y,-.133),(0,0,1),[(0,.103),(.028,.103),(.050,.070)])
        m.rod(group,'titanium',(x,y,-.088),(x,y,z-.053),.059)
        if z>.05:
            # A pair of webs carries the column load into the bolted foot.
            h=min(.28,z-.010)
            for sign in (-1,1):
                tri=np.array([[x+sign*.045,-.13],[x+sign*.162,-.13],[x+sign*.045,h]])
                vv=[(xx,y+dy,zz) for dy in (-.019,.019) for xx,zz in tri]
                faces_web=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
                m.mesh(group,'steel',vv,[face[::-1] for face in faces_web] if sign>0 else faces_web)
        m.turned(group,'graphite',(x,y,z-.072),(0,0,1),[(0,.076),(.033,.112),(.074,.112)])
    return count


def deck(m):
    p='Exhibit/Service_Deck'
    # Rectangular raised deck and foot pads echo the original fusion station plate.
    m.box(p,'anodized',(0,0,-.317),(9.00,9.00,.22),.048,.21)
    m.box(p,'graphite',(0,0,-.223),(8.92,8.92,.044),.014,.18)
    for x in (-4.04,4.04):
        for y in (-3.88,3.88):
            m.box(p,'graphite',(x,y,-.685),(.30,.31,.54),.031)
            m.box(p,'steel',(x,y,-.99),(.71,.64,.13),.028,.09)
            for dx in (-.24,.24):
                screw(m,p,x+dx,y,-.929,.041)
    for x in (-3.88,0,3.88):
        m.box(p,'anodized',(x,0,-.496),(.17,8.00,.17),.019)
    for y in (-4.12,4.12):
        for x in np.linspace(-4.04,4.04,6):
            screw(m,p,x,y,-.202,.049)


def ground_section(m):
    # A level, symmetric chamfered geological sample, with a planar contact face.
    angles=(np.arange(32)+.5)*2*np.pi/32
    co,si=np.cos(angles),np.sin(angles)
    radius=(abs(co/5.43)**3.0+abs(si/5.15)**3.0)**(-1/3.0)
    levels=[(-1.62,.985,'ochre'),(-1.58,1.0,'ochre'),(-1.29,1.0,'soil'),
            (-1.075,1.0,'soil'),(-1.047,.994,'soil')]
    rings=[np.column_stack((co*radius*r,si*radius*r,np.full_like(co,z))) for z,r,_ in levels]
    n=len(co)
    for j,(_,_,mat) in enumerate(levels[:-1]):
        m.mesh('Scenery/Martian_Ground_Plinth',mat,np.vstack(rings[j:j+2]),
               [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],True)
    for j,mat in [(0,'ochre'),(-1,'soil')]:
        pts=np.vstack((rings[j].mean(axis=0),rings[j]))
        faces=[(0,i+1,(i+1)%n+1) for i in range(n)]
        m.mesh('Scenery/Martian_Ground_Plinth',mat,pts,faces if j==-1 else [f[::-1] for f in faces],True)


def service_port(m):
    p='Exhibit/Deck_Service_Coupling'
    x,y=3.34,.56
    for dy in (-.225,.225):
        m.box(p+'/Slide_Rails','steel',(x,y+dy,-.145),(.96,.11,.12),.019)
    m.box(p,'graphite',(x,y,.006),(.73,.55,.21),.027,.059)
    start=np.array([x-.27,y-.10,.36])
    u,v,w=axis_basis([1,.44,.09])
    m.turned(p,'steel',start,w,[(0,.238),(.062,.266),(.127,.266),(.158,.204),(.63,.204)])
    m.turned(p,'titanium',start,w,[(.60,.211),(.623,.30),(.723,.30),(.752,.278)])
    c=start+w*.757
    m.rod(p,'graphite',c,c+w*.024,.198,36)
    for a in np.arange(8)*np.pi/4:
        q=c+.244*(u*np.cos(a)+v*np.sin(a))
        m.rod(p,'steel',q-w*.009,q+w*.018,.027,6)
    m.pipe('Exhibit/Cable_Loom','teal',[(x-.25,y,.36),(x-.49,y,.36),(x-.49,y,-.102),
                             (x-.49,2.54,-.102),(2.68,2.54,-.102),(2.68,2.54,.02)],.039,.10)


def instrumentation(m):
    p='Exhibit/Diagnostic_Interface'
    x,y=-3.44,2.97
    m.box(p,'anodized',(x,y,-.12),(1.67,1.22,.16),.045,.105)
    m.box(p,'satin_enamel',(x,y,.26),(1.59,1.14,.66),.061,.112)
    m.box(p,'steel',(x,y,.605),(1.63,1.18,.085),.026,.092)
    for dy in np.linspace(-.38,.38,7):
        m.box(p,'anodized',(x-.39,y+dy,.663),(.51,.052,.032),.008)
    # Blank bonded display faces the front edge of the deck.
    m.box(p,'steel',(x+.02,y+.575,.265),(1.14,.066,.40),.020,.065)
    m.box(p,'screen',(x+.02,y+.724,.265),(1.00,.036,.295),.012,.049)
    for dy,col in ((-.17,'green'),(.02,'cyan')):
        m.box(p,col,(x+.80,y+dy,.28),(.025,.103,.054),.008)
    h=p+'/Recessed_Header'
    cx=x+.36
    m.box(h,'anodized',(cx,y,.663),(.70,.51,.035),.011,.053)
    for side in (-1,1):
        m.box(h,'steel',(cx,y+side*.24,.727),(.71,.060,.151),.016,.021)
        m.box(h,'steel',(cx+side*.325,y,.727),(.061,.44,.151),.016,.021)
    for dx in (-.162,-.054,.054,.162):
        for dy in (-.075,.075):
            m.turned(h,'contact_gold',(cx+dx,y+dy,.675),(0,0,1),
                     [(0,.031),(.071,.031),(.086,.018)],12)
    for dx,dy,rad in [(-.244,.127,.035),(.244,-.127,.024)]:
        m.turned(p+'/Asymmetric_Locating_Pins','titanium',(cx+dx,y+dy,.675),(0,0,1),
                 [(0,rad),(.099,rad),(.127,rad*.50)],14)
    for xx in (-.69,.69):
        for yy in (-.46,.46):
            screw(m,p,x+xx,y+yy,.650,.042)
    x2,y2=2.47,2.65
    m.box('Exhibit/Patch_Enclosure','anodized',(x2,y2,-.10),(.66,.58,.20),.029,.071)
    m.box('Exhibit/Patch_Enclosure','enamel',(x2,y2,.063),(.66,.58,.212),.035,.071)
    m.box('Exhibit/Patch_Enclosure','porcelain',(x2,y2,.177),(.68,.60,.056),.016,.065)
    for i,col in enumerate(('teal','graphite')):
        yy=3.92+i*.13
        xx=x-.10+i*.15
        end=x2-.10+i*.15
        z=-.133
        m.pipe('Exhibit/Cable_Loom',col,[(xx,y+.57,.17),(xx,y+.72,.17),(xx,y+.72,z),
               (xx,yy,z),(end,yy,z),(end,y2+.45,z),(end,y2+.45,.012),(end,y2+.26,.012)],.038,.10)
    for xx in (-1.9,-.4,1.1):
        m.box('Exhibit/Cable_Loom','titanium',(xx,3.985,-.102),(.070,.29,.04),.011)


def cutaway(source):
    bodies=read_assembly(source)
    original=Model('pwO3 native cutaway',.001/SCALE)
    ground_section(original)
    deck(original)
    service_port(original)
    instrumentation(original)
    count=coils_and_supports(original,*bodies['coils'])
    for name,(label,mat) in SURFACES.items():
        path='pwO3/'+label
        add_native_mesh(original,path,mat,*bodies[name])
        if name=='vessel':
            add_cut_lips(original,path,*bodies[name],(0,120),.22)
        if name=='first_wall':
            add_cut_lips(original,path,*bodies[name],(40,80),.14)
    # Match the legacy Y-up viewport direction in the Z-up studio frame.
    # Turn the entire exhibit together so the studio lights stay camera-relative.
    back=np.array([-sin(YAW),-cos(YAW)])
    yaw=atan2(-1,-.43)-atan2(back[1],back[0])
    rot=np.array([[cos(yaw),-sin(yaw),0],[sin(yaw),cos(yaw),0],[0,0,1]])
    m=Model('P3A pwO3 stellarator cutaway',original.meters)
    for path,materials in original.parts.items():
        for mat,blocks in materials.items():
            m.parts[path][mat]=[(v@rot.T,n@rot.T,t) for v,n,t in blocks]
    m.surface_finishes={'soil':'regolith','ochre':'regolith','titanium':'brushed','steel':'brushed'}
    m.state={'sourceAssembly':source.name,'sourceSHA256':sha256(source.read_bytes()).hexdigest(),
             'sourceUnit':'millimeter','sourceCoilCountInCutaway':count,
             'sourceTriangles':{k:len(f) for k,(v,f) in bodies.items()},
             'displayRotationZRadians':float(yaw),'cameraReference':'10_fusion_station',
             'cameraReferenceYaw':YAW,'cameraElevationDeg':27,'equivalentFocalLengthMM':60,'vesselOpeningDeg':120,
             'displayHardware':'Illustrative deck, supports, enclosures and cable harness'}
    return m


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='path to pwO3_120mm_multicolor.3mf')
    parser.add_argument('--out',type=Path,default=DEFAULT_DIR)
    parser.add_argument('--width',type=int,default=2400)
    parser.add_argument('--samples',type=int,default=24)
    args=parser.parse_args()
    bake([[(STEM,partial(cutaway,args.source))]],args.out,args.width,args.samples,
         camera_elevation=-PITCH,floor_origin=True,studio_lights=STUDIO_LIGHTS)
