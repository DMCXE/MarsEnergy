"""Matching terrain sections with continuous bedding and a modeled melt cavity."""
from math import radians, sin, cos, pi
import numpy as np
from geometry import Model, unit, axis_basis

RADIUS=3.56
SURFACE=2.75

def cavity(z):
    return float(np.interp(z,[0,.43,.51,.66,.87,1.06,1.27,1.48,1.66,2.76],
                             [0,0,.30,.53,.62,.54,.34,.17,.126,.126]))

def bed_offset(z,x,y):
    return (.105*sin(1.24*x+.83*y+.26*z)+.043*sin(3.1*y-1.68*x+.60*z)+.040*x)*min(1,abs(z-SURFACE)*3,z*4)

def layer(m,p,mat,z0,z1,well=False,radius=RADIUS):
    # Subdivide both radial section faces so bedding continues through the cut.
    angles=np.linspace(radians(-35),radians(215),81)
    def ring(z,t):
        inner=cavity(z) if well else 0
        r=inner+(radius-inner)*t
        vs=[]
        for a in angles:
            x,y=r*cos(a),r*sin(a)
            vs.append([x,y,z+bed_offset(z,x,y)*t])
        return np.array(vs)
    steps=np.linspace(0,1,12)
    low=[ring(z0,t) for t in steps]
    high=[ring(z1,t) for t in steps]
    def strip(a,b,reverse=False,smooth=False):
        n=len(a)
        f=[(i,i+n,i+n+1,i+1) for i in range(n-1)]
        m.mesh(p,mat,np.vstack([a,b]),[q[::-1] for q in f] if reverse else f,smooth)
    # Upper/lower boundaries, annular wall, inner bore and two exposed rock faces.
    for i in range(len(steps)-1):
        strip(high[i],high[i+1]); strip(low[i],low[i+1],True)
    strip(low[-1],high[-1],True,True)
    if well and (cavity(z0)>0 or cavity(z1)>0):
        strip(low[0],high[0],False,True)
    for i,reverse in [(0,False),(-1,True)]:
        strip(np.array([r[i] for r in low]),np.array([r[i] for r in high]),reverse)

def rock(m,p,c,r,mat,seed):
    rng=np.random.default_rng(seed)
    verts=[]
    for t,rad,z in [(0,.88,0),(.19,1,.23),(.35,.51,.63)]:
        for j in range(7):
            a=2*pi*j/7+t
            k=r*rad*rng.uniform(.84,1.13)
            verts.append((c[0]+k*cos(a),c[1]+k*sin(a)*.78,c[2]+z*r*rng.uniform(.84,1.16)))
    m.mesh(p,mat,verts,[tuple(reversed(range(7))),tuple(range(14,21))]+[(i+j*7,(i+1)%7+j*7,(i+1)%7+(j+1)*7,i+(j+1)*7) for j in (0,1) for i in range(7)])

def geology(ice):
    m=Model('Utopia melt well' if ice else 'Gale clay kiln')
    layers=([(0,.29,'vein'),(.29,.43,'ice'),(.43,.51,'frost'),(.51,.66,'ice'),(.66,.87,'ice'),(.87,1.06,'ice'),(1.06,1.12,'frost'),(1.12,1.27,'ice'),(1.27,1.48,'ice'),(1.48,1.66,'vein'),(1.66,1.73,'ochre'),(1.73,2.14,'soil'),(2.14,2.20,'ochre'),(2.20,2.75,'soil')]
            if ice else [(0,.32,'shale'),(.32,.45,'clay'),(.45,.72,'stone'),(.72,.80,'ochre'),(.80,1.08,'clay'),(1.08,1.19,'shale'),(1.19,1.57,'stone'),(1.57,1.67,'clay'),(1.67,1.96,'ochre'),(1.96,2.11,'stone'),(2.11,2.26,'clay'),(2.26,2.75,'soil')])
    for i,(lo,hi,mat) in enumerate(layers):
        p='Geological section/'+('Buried ice' if ice and lo<1.66 else 'Regolith' if lo>=2.26 or ice else 'Sedimentary beds')
        layer(m,p,mat,lo,hi,ice)
    rng=np.random.default_rng(941)
    for i in range(56):
        a=rng.uniform(-.53,3.71)
        r=rng.uniform(2.65,3.45)
        rock(m,'Geological section/Surface clasts',(r*cos(a),r*sin(a),SURFACE-.014),rng.uniform(.045,.17),'ochre' if i%4 else 'clay',i)
    if ice:
        well(m)
    else:
        kiln(m)
    return m

def well(m):
    z=SURFACE
    p='Melt well/Coaxial casing'
    # Expose the inner supply line through the same removed sector as the terrain.
    angles=np.linspace(radians(-35),radians(215),50)
    for r,mat,z0 in [(.123,'steel',1.34),(.102,'enamel',1.32),(.077,'graphite',1.29)]:
        rings=[[(rad*cos(t),rad*sin(t),h) for t in angles] for rad,h in [(r,z0),(r,3.46),(r-.013,3.46),(r-.013,z0)]]
        n=len(angles)
        for j in range(4):
            m.mesh(p,mat,rings[j]+rings[(j+1)%4],[(i,i+1,n+i+1,n+i) for i in range(n-1)],j in (0,2))
        for i in (0,-1):
            m.mesh(p,mat,[r[i] for r in rings],[(0,1,2,3)])
    m.rod(p,'teal',(0,0,.92),(0,0,3.59),.041)
    for h in (1.72,2.22,3.46):
        m.rod(p,'steel',(0,0,h),(0,0,h+.06),.146)
    # Water fills the lower bulb, leaving a visible headspace below the ice roof.
    m.turned('Melt well/Liquid reservoir','water',(0,0,0),(0,0,1),[(.443,.032),(.51,.29),(.66,.52),(.87,.61),(.965,.58)],56)
    p='Drilling rig/Lattice derrick'
    for dx in (-1,1):
        for dy in (-1,1):
            a=(dx*.57,.34+dy*.49,z+.02)
            b=(dx*.24,.34+dy*.19,z+1.74)
            m.box(p,'graphite',(a[0],a[1],z+.05),(.28,.26,.10))
            m.rod(p,'steel',a,b,.060)
    for h in [0,.53,1.04,1.58]:
        f=h/1.74
        w=.57-.33*f
        d=.49-.30*f
        m.pipe(p,'amber' if h==1.58 else 'graphite',[(-w,.34-d,z+.08+h),(w,.34-d,z+.08+h),(w,.34+d,z+.08+h),(-w,.34+d,z+.08+h),(-w,.34-d,z+.08+h)],.032,.07)
        if h<1.5:
            for side in (-1,1):
                m.rod(p,'steel',(side*w,.34-d,z+.08+h),(-side*(w-.095),.34-d+.085,z+.58+h),.025)
                m.rod(p,'steel',(side*w,.34-d,z+.08+h),(side*(w-.095),.34+d-.085,z+.58+h),.025)
    m.box(p,'enamel',(0,.34,z+1.80),(.78,.65,.18))
    m.rod(p,'graphite',(0,.11,z+.84),(0,.11,z+1.74),.085)
    for i,(x,y) in enumerate(((1.39,1.57),(2.25,.56))):
        m.tank(f'Surface storage/Insulated vessel {i+1}',x,y,z+.07,.43,1.09)
        m.pipe('Water circuit/Storage header','teal',[(x,y,z+1.25),(x,y,z+1.43),(x+.49,y,z+1.43),(x+.49,y,z+.24),(1.03,.26,z+.24)],.052)
    m.box('Pump skid/Base','graphite',(.97,.30,z+.12),(1.25,.71,.19))
    m.rod('Pump skid/Pump','titanium',(.69,.30,z+.39),(1.23,.30,z+.39),.21)
    m.pipe('Water circuit/Wet return','cyan',[(0,0,3.51),(0,0,3.68),(.53,0,3.68),(.53,.30,z+.39),(.78,.30,z+.39)],.055)
    m.pipe('Heat recovery/Inlet','orange',[(0,.05,3.40),(-.88,.05,3.40),(-.88,.05,z+.26),(-1.35,.05,z+.26),(-1.35,-.51,z+.26)],.084)
    m.flange('Heat recovery/Inlet',(-1.35,-.52,z+.26),(0,-1,0),.165)

def kiln(m):
    z=SURFACE
    p='Solids feed/Sampling scoop'
    # Open bucket with back, cheeks, cutting lip, and individual teeth.
    x,y=-2.12,.15
    m.box(p,'graphite',(x,y,z+.09),(1.08,.87,.15))
    m.box(p,'amber',(x,y,z+.47),(.92,.65,.12),tilt=.32)
    for dx in (-.44,.44):
        vs=[(x+dx+sx,y+yy,z+hh) for sx in (-.035,.035) for yy,hh in [(-.35,.30),(.34,.42),(.34,1.00),(-.19,.64)]]
        m.mesh(p,'steel',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    m.box(p,'amber',(x,y+.32,z+.67),(.92,.09,.53))
    for dx in np.linspace(-.37,.37,5):
        m.box(p,'titanium',(x+dx,y-.40,z+.325),(.10,.24,.07),.011,tilt=.26)
    p='Solids feed/Inclined screw conveyor'
    a=np.array([-1.93,.45,z+.50]); b=np.array([-.70,.65,z+1.33])
    m.rod(p,'graphite',a,b,.15)
    u,v,w=axis_basis(b-a)
    points=[a+(b-a)*t+.166*(u*cos(12*pi*t)+v*sin(12*pi*t)) for t in np.linspace(0,1,108)]
    for i in range(len(points)-1):
        m.rod(p,'titanium',points[i],points[i+1],.030,8)
    for t in (0,.5,1):
        c=a+(b-a)*t
        m.rod(p,'amber',c-.04*w,c+.04*w,.201)
    p='Thermal processor/Rotary kiln'
    y=.70
    for x in (-.42,.87):
        m.box(p,'graphite',(x,y,z+.29),(.36,1.05,.54),.035,.08)
        m.box(p,'steel',(x,y,z+.47),(.42,1.12,.14))
    m.turned(p,'copper',(-.75,y,z+.97),(1,0,0),[(0,.34),(.11,.49),(.23,.52),(1.80,.52),(1.94,.47),(2.01,.31)],48)
    for x in (-.51,-.38,.34,.90,1.05):
        m.rod(p,'graphite' if x in (-.38,.90) else 'amber',(x,y,z+.97),(x+.075,y,z+.97),.545,48)
    m.flange(p,(1.29,y,z+.97),(1,0,0),.325)
    m.pipe('Water recovery/Vapour riser','steel',[(.81,y,z+1.39),(.81,y,z+1.87),(.20,y,z+1.87)],.076)
    m.turned('Water recovery/Condenser','steel',(-.38,y,z+1.78),(1,0,0),[(0,.14),(.08,.23),(.76,.23),(.85,.14)])
    for x in np.linspace(-.26,.31,6):
        m.rod('Water recovery/Condenser','titanium',(x,y,z+1.78),(x+.028,y,z+1.78),.265)
    m.tank('Water recovery/Storage vessel',2.57,1.13,z+.02,.44,1.48,'teal')
    m.pipe('Water recovery/Condensate line','teal',[(.02,y+.20,z+1.78),(.02,1.42,z+1.78),(2.57,1.42,z+1.78),(2.57,1.13,z+1.78),(2.57,1.13,z+1.49)],.052)
    m.pipe('Solids discharge/Chute','graphite',[(1.26,y,z+.95),(1.67,y,z+.95),(1.96,.20,z+.43)],.143)
    tail='Solids discharge/Dry tailings'
    rock(m,tail,(2.13,-.06,z-.017),.54,'ochre',182)
    for i in range(24):
        rng=np.random.default_rng(i+48)
        x,y=rng.normal(2.14,.26),rng.normal(.08,.22)
        rock(m,'Solids discharge/Dry tailings',(x,y,z),rng.uniform(.10,.29),'ochre' if i%3 else 'clay',i+96)
