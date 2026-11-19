"""Small hard-surface modeling vocabulary. Authoring coordinates are Z-up."""
from collections import defaultdict
from math import cos, sin, pi, radians
import numpy as np

# name -> sRGB base, metallic, roughness, opacity, emissive strength
MATERIALS = {
    'enamel': ('D3CFBC', .21, .39, 1, 0), 'porcelain': ('E1E0CC', .12, .32, 1, 0),
    'titanium': ('ADB7B8', .71, .32, 1, 0), 'steel': ('93A2A3', .76, .30, 1, 0),
    'graphite': ('353F45', .48, .42, 1, 0), 'seal': ('1E292E', .08, .70, 1, 0),
    'teal': ('509A95', .41, .36, 1, 0), 'cyan': ('48CAE4', .36, .32, 1, 0),
    'amber': ('DF9B47', .52, .37, 1, 0), 'orange': ('FF8F45', .22, .40, 1, 0),
    'gold': ('D5AE67', .78, .28, 1, 0), 'solar': ('243F67', .44, .25, 1, 0),
    'violet': ('9276AD', .32, .38, 1, 0),
    'copper': ('C27E4A', .57, .37, 1, 0),
    'green': ('34D399', .26, .38, 1, 0), 'glass': ('A6D1CD', .16, .16, .29, 0),
    'screen': ('18282E', .38, .18, 1, 0), 'pcb': ('396E63', .23, .48, 1, 0),
    'red': ('A64E40', .12, .52, 1, 0), 'soil': ('9E6C4F', .02, .94, 1, 0),
    'ochre': ('865842', .02, .93, 1, 0), 'stone': ('6E625A', .03, .90, 1, 0),
    'clay': ('8D7970', .02, .94, 1, 0), 'shale': ('534C48', .03, .89, 1, 0),
    'ice': ('A4C4CC', .10, .41, 1, 0), 'frost': ('C4D8D8', .07, .48, 1, 0),
    'vein': ('86ABB7', .14, .38, 1, 0), 'water': ('468A9B', .43, .13, 1, 0),
    'leaf': ('4D9564', .02, .56, 1, 0), 'sprout': ('80AE64', .02, .54, 1, 0),
    'leafshade': ('387651', .02, .58, 1, 0), 'substrate': ('50473C', .01, .96, 1, 0),
    'lamp': ('FFF2CB', .04, .27, 1, 2.4), 'dim': ('B1A68E', .06, .37, 1, .25),
    'unlit': ('3E4849', .23, .44, 1, 0), 'mintlit': ('9CE4C7', .13, .26, 1, .68),
    'coollit': ('82A6B6', .20, .28, 1, .13), 'asphalt': ('546267', .07, .85, 1, 0),
}

def unit(v):
    a = np.asarray(v, dtype=float)
    return a / np.linalg.norm(a)

def axis_basis(axis):
    w = unit(axis)
    u = unit(np.cross((0, 0, 1) if abs(w[2]) < .9 else (0, 1, 0), w))
    return u, np.cross(w, u), w

class Model:
    def __init__(self, name, meters=1):
        self.name, self.meters = name, meters
        self.parts = defaultdict(lambda: defaultdict(list))
        self.lights = []
        self.state = {}

    def mesh(self, part, mat, verts, faces, smooth=False):
        vertices = np.asarray(verts, float)
        tris = []
        for f in faces:
            tris.extend((f[0], f[i], f[i+1]) for i in range(1, len(f)-1))
        tris = np.asarray(tris, int)
        cross = np.cross(vertices[tris[:, 1]] - vertices[tris[:, 0]], vertices[tris[:, 2]] - vertices[tris[:, 0]])
        valid = np.linalg.norm(cross, axis=1) > 1e-10
        tris, cross = tris[valid], cross[valid]
        if smooth:
            normals = np.zeros_like(vertices)
            for i in range(3):
                np.add.at(normals, tris[:, i], cross)
            normals /= np.maximum(1e-20, np.linalg.norm(normals, axis=1)[:, None])
        else:
            vertices = vertices[tris].reshape(-1, 3)
            normals = np.repeat(cross / np.linalg.norm(cross, axis=1)[:, None], 3, axis=0)
            tris = np.arange(len(vertices)).reshape(-1, 3)
        self.parts[part][mat].append((vertices, normals, tris))

    def box(self, part, mat, c, size, bevel=.035, clip=None, rot=0, tilt=0):
        """Clipped plan corners and two edge bevels, with optional X tilt and Z yaw."""
        x,y,z = np.asarray(size)/2
        b = min(bevel, x*.35, y*.35, z*.42)
        k = min(clip if clip is not None else max(b*1.4,.006), x*.75, y*.75)
        verts=[]
        for inset,h in [(b,-z),(0,-z+b),(0,z-b),(b,z)]:
            a,d,t=x-inset,y-inset,max(.001,k-inset*.58)
            for px,py in [(-a+t,-d),(a-t,-d),(a,-d+t),(a,d-t),(a-t,d),(-a+t,d),(-a,d-t),(-a,-d+t)]:
                yy=py*cos(tilt)-h*sin(tilt)
                verts.append((c[0]+px*cos(rot)-yy*sin(rot),c[1]+px*sin(rot)+yy*cos(rot),c[2]+py*sin(tilt)+h*cos(tilt)))
        faces=[tuple(reversed(range(8))),tuple(range(24,32))]
        for j in range(3):
            faces.extend((8*j+i,8*j+(i+1)%8,8*j+8+(i+1)%8,8*j+8+i) for i in range(8))
        self.mesh(part,mat,verts,faces)

    def turned(self, part, mat, origin, axis, profile, sides=40):
        """A turned solid described by ordered (axial distance, radius) stations."""
        u,v,w=axis_basis(axis)
        a=np.arange(sides)*2*pi/sides
        circle=np.outer(np.cos(a),u)+np.outer(np.sin(a),v)
        rings=[np.asarray(origin)+h*w+r*circle for h,r in profile]
        faces=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i)
               for j in range(len(rings)-1) for i in range(sides)]
        self.mesh(part,mat,np.concatenate(rings),faces,smooth=sides>8)
        for ring,reverse in [(rings[0],True),(rings[-1],False)]:
            if np.linalg.norm(ring[0]-ring[1])>1e-9:
                self.mesh(part,mat,ring,[list(reversed(range(sides))) if reverse else list(range(sides))])

    def rod(self, part, mat, a, b, r, sides=20):
        delta=np.subtract(b,a)
        self.turned(part,mat,a,delta,[(0,r),(np.linalg.norm(delta),r)],sides)

    def pipe(self, part, mat, points, r, bend=None, sides=14):
        """Continuous round tube with tangent-rounded elbows."""
        pts=np.asarray(points,float)
        path=[pts[0]]
        for a,b,c in zip(pts,pts[1:],pts[2:]):
            radius=min(bend or r*3,np.linalg.norm(a-b)*.4,np.linalg.norm(c-b)*.4)
            p,q=b+unit(a-b)*radius,b+unit(c-b)*radius
            for t in np.linspace(0,1,7):
                path.append((1-t)**2*p+2*t*(1-t)*b+t*t*q)
        path.append(pts[-1])
        tangents=np.array([unit(np.subtract(path[min(i+1,len(path)-1)],path[max(0,i-1)])) for i in range(len(path))])
        prev=axis_basis(tangents[0])[0]
        verts=[]
        for p,w in zip(path,tangents):
            u=unit(prev-w*np.dot(w,prev))
            v=np.cross(w,u)
            verts.extend(p+r*(u*cos(t)+v*sin(t)) for t in np.arange(sides)*2*pi/sides)
            prev=u
        faces=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i)
               for j in range(len(path)-1) for i in range(sides)]
        self.mesh(part,mat,verts,faces,True)
        self.mesh(part,mat,verts,[tuple(reversed(range(sides))),tuple(range(len(verts)-sides,len(verts)))])

    def arch(self, part, mat, x0,x1,y,z,r0,r1,start,end):
        """Capped longitudinal shell sector. Angle zero points toward the viewer (-Y)."""
        angles=np.linspace(radians(start),radians(end),max(3,int((end-start)/4)+1))
        n=len(angles)
        rings=[[(x,y-r*cos(t),z+r*sin(t)) for t in angles] for x,r in [(x0,r1),(x1,r1),(x1,r0),(x0,r0)]]
        for j in range(4):
            vs=rings[j]+rings[(j+1)%4]
            self.mesh(part,mat,vs,[(i,i+n,i+n+1,i+1) for i in range(n-1)],smooth=j in (0,2))
        for i,seq in [(0,(0,3,2,1)),(-1,(0,1,2,3))]:
            self.mesh(part,mat,[ring[i] for ring in rings],[seq])

    def flange(self, part, c, axis, r, bolts=6):
        u,v,w=axis_basis(axis)
        c=np.asarray(c)
        self.rod(part,'steel',c-.042*w,c+.042*w,r,32)
        for t in np.arange(bolts)*2*pi/bolts:
            p=c+.045*w+r*.78*(cos(t)*u+sin(t)*v)
            self.rod(part,'graphite',p,p+.024*w,r*.10,6)

    def tank(self,part,x,y,z,r,h,band='teal'):
        self.turned(part,'porcelain',(x,y,z),(0,0,1),[(0,.61*r),(.05*h,.86*r),(.12*h,r),(.86*h,r),(.93*h,.89*r),(.975*h,.58*r),(h,.22*r)])
        for f in (.19,.78):
            self.turned(part,band,(x,y,z),(0,0,1),[(h*f,r*1.02),(h*(f+.045),r*1.02)])
        self.rod(part,'graphite',(x,y,z+h),(x,y,z+h+.10),r*.19)
        for dx in (-.54,.54):
            self.box(part,'graphite',(x+dx*r,y,z+.04),(r*.27,r*.80,.17))

    def base(self,part,w,d,h=.24,mat='enamel',clip=.48):
        self.box(part,'graphite',(0,0,h*.28),(w-.07,d-.07,h*.56),h*.10,clip)
        self.box(part,mat,(0,0,h*.68),(w,d,h*.64),h*.10,clip)
        for x in (-1,1):
            for y in (-1,1):
                self.rod(part,'steel',(x*(w/2-.42),y*(d/2-.34),h-.01),(x*(w/2-.42),y*(d/2-.34),h+.018),.069,12)
