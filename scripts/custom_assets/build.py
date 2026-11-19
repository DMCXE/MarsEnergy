"""Generate the GLB assets and render their transparent studio plates.

Requires Python 3, NumPy, Pillow, and a C++17 compiler. Examples:
    python scripts/custom_assets/build.py
    python scripts/custom_assets/build.py --asset greenhouse --width 900 --out /tmp/preview
"""
import argparse
from functools import partial
import json
from math import tan, radians
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image

from geometry import MATERIALS, unit
from habitats import greenhouse, backup
from instruments import lamp_meter, teg
from geology import geology
from campus import campus
from interfaces import microgrid, cubesat
from telemetry import cansat_telemetry

DEFAULT_DIR=Path(__file__).resolve().parents[2]/'assets/renders/custom'
SETS={
 'greenhouse': [('p0_b2_greenhouse_cutaway_25kw_12h',partial(greenhouse,True)),('p0_b2_greenhouse_cutaway_15kw_8h',partial(greenhouse,False))],
 'lamp': [('p0_desk_kit_lamp_meter',lamp_meter)],
 'teg': [('p0_desk_kit_teg_heatsink',teg)],
 'backup': [('p1_zone_a_backup_48h_cutaway',backup)],
 'geology': [('p1_zone_c_utopia_ice_well',partial(geology,True)),('p1_zone_c_gale_clay_kiln',partial(geology,False))],
 'campus': [('p2_campus_blackout_diorama',campus)],
 'microgrid': [('p0_microgrid_bus_interface',microgrid)],
 'cubesat': [('p0_cubesat_1u_teg_module',cubesat)],
 'cansat': [('p1_cansat_rocket_telemetry',cansat_telemetry)],
}

def linear(hexcolor):
    rgb=np.array([int(hexcolor[j:j+2],16)/255 for j in (0,2,4)])
    return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)

def gltf_axes(a):
    return np.stack([a[...,0],a[...,2],-a[...,1]],axis=-1)

def packed_parts(model):
    for path,materials in model.parts.items():
        for mat,blocks in materials.items():
            lengths=[len(v) for v,n,t in blocks]
            offsets=np.cumsum([0]+lengths[:-1])
            v=np.concatenate([item[0] for item in blocks])
            n=np.concatenate([item[1] for item in blocks])
            t=np.concatenate([item[2]+off for item,off in zip(blocks,offsets)])
            yield path,mat,v,n,t

def frame(cloud):
    # A 60 mm equivalent lens, 27 degree elevation, identical fit for both members of a pair.
    elevation=radians(27)
    horizontal=unit([-.43,-1,0])
    back=horizontal*np.cos(elevation)+np.array([0,0,np.sin(elevation)])
    right=unit(np.cross([0,0,1],back))
    up=np.cross(back,right)
    basis=np.array([right,up,back])
    coords=cloud@basis.T
    focus=(coords.max(axis=0)+coords.min(axis=0))/2
    rel=coords-focus
    half=np.array([.30,.20])
    distance=np.max(np.abs(rel[:,:2])/(half*.886)+rel[:,2:3])
    focus[2]+=distance
    for _ in range(4):
        depth=(focus[2]-coords[:,2:3])
        projected=(coords[:,:2]-focus[:2])/depth
        center=(projected.max(axis=0)+projected.min(axis=0))/2
        focus[:2]+=center*distance
        projected=(coords[:,:2]-focus[:2])/depth
        change=np.max(np.abs(projected)/half)/.89
        focus[2]+=distance*(change-1)
        distance*=change
    return focus@basis,basis

def camera_quaternion(matrix):
    # Our camera always has positive trace in glTF space.
    w=np.sqrt(1+np.trace(matrix))/2
    return [(matrix[2,1]-matrix[1,2])/(4*w),(matrix[0,2]-matrix[2,0])/(4*w),(matrix[1,0]-matrix[0,1])/(4*w),w]

def write_glb(model,parts,filename,eye,basis,center):
    nodes=[{'name':model.name,'children':[],'extras':model.state}]
    meshes=[]; views=[]; access=[]; binary=bytearray()
    groups={'':0}
    def node(path):
        if path not in groups:
            parent,_,name=path.rpartition('/')
            parent_id=node(parent)
            groups[path]=len(nodes)
            nodes[parent_id]['children'].append(len(nodes))
            nodes.append({'name':name,'children':[]})
        return groups[path]
    def buffer(a,component,kind,target,bounds=False):
        while len(binary)%4: binary.append(0)
        idx=len(views)
        views.append(dict(buffer=0,byteOffset=len(binary),byteLength=a.nbytes,target=target))
        binary.extend(a.tobytes())
        item=dict(bufferView=idx,componentType=component,count=len(a),type=kind)
        if bounds: item.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        access.append(item)
        return len(access)-1
    mats=[]; matids={}
    for name in dict.fromkeys(p[1] for p in parts):
        hexcol,metal,rough,alpha,em=MATERIALS[name]
        color=linear(hexcol)
        item={'name':name,'pbrMetallicRoughness':{'baseColorFactor':[*color,alpha],'metallicFactor':metal,'roughnessFactor':rough},'doubleSided':True}
        if alpha<1: item['alphaMode']='BLEND'
        if em:
            item['emissiveFactor']=(color*min(1,em)).tolist()
            if em>1: item['extensions']={'KHR_materials_emissive_strength':{'emissiveStrength':em}}
        matids[name]=len(mats); mats.append(item)
    limits={}
    for path,mat,v,n,t in parts:
        lo,hi=v.min(axis=0),v.max(axis=0)
        while path:
            if path in limits:
                low,high=limits[path]
                limits[path]=np.minimum(low,lo),np.maximum(high,hi)
            else:
                limits[path]=lo,hi
            path=path.rpartition('/')[0]
    origins={path:(low+high)/2 for path,(low,high) in limits.items()}
    origins['']=center
    for path,mat,v,n,t in parts:
        owner=node(path)
        if 'mesh' not in nodes[owner]:
            nodes[owner]['mesh']=len(meshes)
            meshes.append({'name':path,'primitives':[]})
        data=np.concatenate([gltf_axes((v-origins[path])*model.meters),gltf_axes(n)],axis=1).astype('<f4')
        used,remap=np.unique(t,return_inverse=True)
        t=remap.reshape(t.shape)
        unique,inverse=np.unique(data[used],axis=0,return_inverse=True)
        indices=inverse.reshape(-1)[t].reshape(-1)
        small=len(unique)<65536
        primitive={'attributes':{'POSITION':buffer(np.ascontiguousarray(unique[:,:3]),5126,'VEC3',34962,True),
                                 'NORMAL':buffer(np.ascontiguousarray(unique[:,3:]),5126,'VEC3',34962)},
                   'indices':buffer(indices.astype('<u2' if small else '<u4'),5123 if small else 5125,'SCALAR',34963),
                   'material':matids[mat]}
        meshes[nodes[owner]['mesh']]['primitives'].append(primitive)
    for path,idx in groups.items():
        if path:
            parent=path.rpartition('/')[0]
            nodes[idx]['translation']=gltf_axes((origins[path]-origins[parent])*model.meters).tolist()
    camera=len(nodes)
    nodes.append({'name':'Studio camera 60 mm','camera':0,'translation':gltf_axes((eye-center)*model.meters).tolist(),
                  'rotation':camera_quaternion(gltf_axes(basis).T)})
    lights=[]
    if model.lights:
        # A downward area fixture is approximated by one broad glTF spotlight per bay/tier.
        for i in range(0,len(model.lights),6):
            samples=np.array(model.lights[i:i+6])
            pos=samples[:,:3].mean(axis=0)
            lights.append({'name':'Horticultural LED','type':'spot','color':[1,.88,.60],
                           'intensity':float(samples[:,3].sum()*6),'range':1.45*model.meters,
                           'spot':{'innerConeAngle':.68,'outerConeAngle':1.32}})
            lamp_path=min((p for p in origins if p.startswith('Grow lights/')),key=lambda p: np.linalg.norm(origins[p]-pos))
            nodes[groups[lamp_path]]['children'].append(len(nodes))
            nodes.append({'name':f'Grow light {i//6+1:02d}','translation':gltf_axes((pos-origins[lamp_path])*model.meters).tolist(),
                          'rotation':[-2**-.5,0,0,2**-.5],
                          'extensions':{'KHR_lights_punctual':{'light':len(lights)-1}}})
    for n in nodes:
        if n.get('children')==[]: del n['children']
    doc={'asset':{'version':'2.0','generator':'MarsEnergy STEM asset models'},'scene':0,'scenes':[{'nodes':[0,camera]}],
         'nodes':nodes,'meshes':meshes,'materials':mats,'cameras':[{'type':'perspective','perspective':{'yfov':float(2*np.arctan(.2)),'znear':.001,'aspectRatio':1.5}}],
         'bufferViews':views,'accessors':access,'buffers':[{'byteLength':len(binary)}]}
    if any('extensions' in m for m in mats): doc['extensionsUsed']=['KHR_materials_emissive_strength']
    if lights:
        doc.setdefault('extensionsUsed',[]).append('KHR_lights_punctual')
        doc['extensions']={'KHR_lights_punctual':{'lights':lights}}
    s=json.dumps(doc,separators=(',',':')).encode()
    s+=b' '*(-len(s)%4); binary+=bytes(-len(binary)%4)
    with filename.open('wb') as f:
        f.write(struct.pack('<4sIII4s',b'glTF',2,28+len(s)+len(binary),len(s),b'JSON'))
        f.write(s); f.write(struct.pack('<I4s',len(binary),b'BIN\0')); f.write(binary)

def render(model,parts,filename,eye,basis,renderer,temp,width,samples):
    mats=list(MATERIALS)
    with (temp/'scene').open('wb') as file:
        file.write(struct.pack('<4I',sum(len(t) for *_,t in parts),len(mats),len(model.lights),samples))
        np.concatenate([eye,basis.ravel()]).astype('<f4').tofile(file)
        for name,(col,m,r,a,e) in MATERIALS.items():
            np.array([*linear(col),m,r,a,e,float(name in ('soil','ochre','stone','shale','clay','ice','frost','vein','substrate'))],'<f4').tofile(file)
        np.array(model.lights,'<f4').tofile(file)
        for path,mat,v,n,t in parts:
            values=np.concatenate([v[t].reshape(-1,9),n[t].reshape(-1,9),np.full((len(t),1),mats.index(mat))],axis=1)
            values.astype('<f4').tofile(file)
    h=width*2//3
    subprocess.run([str(renderer),str(temp/'scene'),str(temp/'rgba'),str(width),str(h)],check=True)
    Image.frombytes('RGBA',(width,h),(temp/'rgba').read_bytes()).save(filename)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset',choices=list(SETS),action='append')
    parser.add_argument('--out',type=Path,default=DEFAULT_DIR)
    parser.add_argument('--width',type=int,default=2400)
    parser.add_argument('--samples',type=int,default=12)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tempdir:
        temp=Path(tempdir)
        renderer=temp/'studio'
        compiler=[os.environ.get('CXX','c++')]
        if sys.platform=='darwin' and 'CXX' not in os.environ:
            sdk=Path(subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip())
            compiler+=['-isystem',str(sdk/'usr/include/c++/v1')]
        subprocess.run([*compiler,'-std=c++17','-O3','-pthread',str(Path(__file__).with_name('studio.cpp')),'-o',str(renderer)],check=True)
        for key in args.asset or SETS:
            models=[(name,f()) for name,f in SETS[key]]
            scenes=[(name,m,list(packed_parts(m))) for name,m in models]
            clouds=[np.vstack([v for _,_,v,_,_ in parts]) for _,_,parts in scenes]
            eye,basis=frame(np.vstack(clouds))
            # Compare states in the same local coordinate system, including their common camera.
            merged=np.vstack(clouds)
            center=(merged.max(axis=0)+merged.min(axis=0))/2
            for name,model,parts in scenes:
                print(name,flush=True)
                write_glb(model,parts,args.out/(name+'.glb'),eye,basis,center)
                render(model,parts,args.out/(name+'.png'),eye,basis,renderer,temp,args.width,args.samples)

if __name__=='__main__':
    main()
