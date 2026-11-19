"""Paired pressure habitats, lighting states, and the isolated life-support circuit."""
from math import pi, sin, cos
import numpy as np
from geometry import Model

def hatch(m,p,x,y,z,r):
    for offset,rad,mat in [(0,1,'steel'),(-.045,.88,'seal'),(-.075,.79,'enamel')]:
        m.rod(p,mat,(x+offset,y,z),(x+offset-.05,y,z),r*rad,40)
    m.rod(p,'graphite',(x-.13,y,z+.07),(x-.15,y,z+.07),r*.36)
    m.rod(p,'teal',(x-.151,y,z+.07),(x-.165,y,z+.07),r*.28)
    for dy in (-.40,.40):
        m.rod(p,'graphite',(x-.16,y+dy*r,z-.23*r),(x-.16,y+dy*r,z+.12*r),.031)
    for t in np.arange(10)*pi/5:
        m.rod(p,'graphite',(x-.048,y+.93*r*cos(t),z+.93*r*sin(t)),(x-.067,y+.93*r*cos(t),z+.93*r*sin(t)),.029,6)

def louver(m,p,x,y,z,w,h):
    m.box(p,'seal',(x,y,z),(w,.075,h))
    for dz in np.linspace(-h*.37,h*.37,6):
        m.box(p,'steel',(x,y-.055,z+dz),(w*.88,.08,.030),.009,tilt=-.25)

def service(m,ys,right,h):
    p='Pressure hull/East service module'
    middle=sum(ys)/2
    m.box(p,'steel',(right,middle,.40),(.98,ys[1]-ys[0]+1.7,.24),.06,.22)
    m.box(p,'enamel',(right,middle,(h+.42)/2),(1.02,ys[1]-ys[0]+1.56,h-.42),.09,.22)
    m.box(p,'titanium',(right,middle,h),(1.10,ys[1]-ys[0]+1.64,.16),.04,.22)
    for y in ys:
        m.box(p,'graphite',(right,y,h+.09),(.67,.88,.075))
        for dy in np.linspace(-.33,.33,8):
            m.box(p,'steel',(right,y+dy,h+.15),(.53,.036,.06),.01)
    louver(m,p,right,middle-(ys[1]-ys[0]+1.56)/2-.01,1.18,.68,.61)

def rosette(m,p,x,y,z,seed):
    """Folded broad leaves with scalloped margins and a higher central whorl."""
    rng=np.random.default_rng(seed)
    for i in range(7):
        a=2*pi*i/7+rng.uniform(-.22,.22)
        L=rng.uniform(.13,.19) if i<5 else .10
        height=rng.uniform(.08,.14) if i<5 else .17
        verts=[]
        for j in range(7):
            t=j/6
            w=.064*(.045+sin(pi*t)**.60)*(1+.14*cos(j*2.7))
            for s in (-1,0,1):
                u=L*t
                v=s*w
                verts.append((x+u*cos(a)-v*sin(a),y+u*sin(a)+v*cos(a),
                              z+height*sin(t*1.85)+.028*t*abs(s)-.017*t*t))
        faces=[(3*j+k,3*j+k+3,3*j+k+4,3*j+k+1) for j in range(6) for k in range(2)]
        m.mesh(p,['leaf','sprout','leafshade','leaf','sprout','leaf','sprout'][i],verts,faces,True)

def greenhouse(full):
    m=Model('B2 greenhouse',1.5)
    m.state={'electricLoad_kWe':25 if full else 15,'photoperiod_h':12 if full else 8}
    m.base('Foundation/Chamfered apron',9.6,5.85)
    ys=(-1.22,1.26)
    for hall,y in enumerate(ys):
        p='Pressure hull/'+('Sectioned front hall' if hall==0 else 'Enclosed rear hall')
        z,r=.53,1.20
        m.box(p,'graphite',(-.50,y,.33),(7.10,2.43,.20),.05,.14)
        m.box(p,'titanium',(-.50,y,.46),(7.04,2.41,.15),.04,.12)
        ribs=np.linspace(-3.94,2.96,6)
        for j,(a,b) in enumerate(zip(ribs,ribs[1:])):
            start=120 if hall==0 else 0
            for rad,thick,mat in [(r-.075,.024,'glass'),(r,.033,'glass')]:
                m.arch(p+'/Glazing',mat,a,b,y,z,rad-thick,rad,start,180)
            for angle in ([122,150,177] if hall==0 else [3,48,90,132,177]):
                m.arch(p+'/Glazing frames','steel',a,b,y,z,r-.01,r+.018,angle-1,angle+1)
        for x in ribs:
            for dy in (-1,1):
                m.box(p+'/Rib footings','steel',(x,y+dy*1.16,.56),(.19,.25,.13),.020)
                for dx in (-.063,.063):
                    m.rod(p+'/Rib footings','graphite',(x+dx,y+dy*1.20,.621),(x+dx,y+dy*1.20,.65),.023,6)
            m.arch(p+'/Six structural ribs','enamel',x-.045,x+.045,y,z,r-.045,r+.075,0,180)
        for x in (-3.97,2.99):
            # End bulkheads close the pressure envelope, independent of the longitudinal cut.
            for mat,rad,dep in [('steel',r,.055),('enamel',r-.07,.065)]:
                angles=np.linspace(0,pi,49)
                yz=[(y-rad*cos(t),z+rad*sin(t)) for t in angles]
                vs=[(xx,yy,zz) for xx in (x-dep,x+dep) for yy,zz in yz]
                n=len(yz)
                m.mesh(p+'/End bulkheads',mat,vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
        hatch(m,p+'/Access lock',-4.05,y,.92,.36)
        for bay,x in enumerate([-3.00,-1.32,.36,2.04]):
            rack=f'Cultivation/Hall {hall+1} rack {bay+1}'
            for dx in (-.75,.75):
                for dy in (-.40,.40):
                    m.box(rack,'steel',(x+dx,y+dy,1.075),(.047,.047,1.13),.009)
            for dy in (-.40,.40):
                m.box(rack,'steel',(x,y+dy,1.64),(1.55,.043,.048),.009)
            for dx in (-.60,.60):
                m.box(rack,'titanium',(x+dx,y,1.64),(.043,.83,.043),.008)
            for level,zz in enumerate((.62,1.04)):
                m.box(rack,'titanium',(x,y,zz-.03),(1.58,.90,.075))
                m.box(rack,'graphite',(x,y,zz+.035),(1.55,.87,.10))
                m.box(rack,'seal',(x,y,zz+.084),(1.45,.78,.023),.008)
                plants=f'{rack}/Seedlings'
                for ix in range(4):
                    for iy in range(2):
                        px,py=x+(ix-1.5)*.35,y+(iy-.5)*.38
                        m.rod(rack,'graphite',(px,py,zz+.093),(px,py,zz+.113),.094,16)
                        rosette(m,plants,px,py,zz+.111,bay*28+ix*2+iy)
                light=f'Grow lights/Hall {hall+1} bay {bay+1} tier {level+1}'
                lh=zz+.38
                on=full or (bay+level)%2==0
                diffuser='lamp' if full else 'dim' if on else 'unlit'
                for ly in (-.34,.21):
                    m.box(light,'graphite',(x,y+ly,lh+.035),(1.56,.13,.056),.012)
                    m.box(light,diffuser,(x,y+ly-.014,lh-.010),(1.48,.145,.056),.014)
                    for dx in (-.60,.60):
                        m.rod(light,'steel',(x+dx,y+ly,lh+.055),(x+dx,y+ly,1.62 if level else 1.03),.010,8)
                    if on:
                        for dx in (-.51,0,.51):
                            m.lights.append((x+dx,y+ly,lh-.05,.78 if full else .055))
    service(m,ys,3.54,1.90)
    for y in (-1.78,-.65,.49,1.63):
        m.box('Environmental control/Access panels','steel',(4.069,y,1.17),(.046,.92,1.00))
        m.box('Environmental control/Access panels','porcelain',(4.093,y,1.17),(.036,.80,.89))
    for offset,mat in [(0,'teal'),(.15,'cyan')]:
        m.pipe('Environmental control/Nutrient supply and return',mat,[(3.55+offset,-2.37,1.45),(3.55+offset,-2.60,1.45),(3.55+offset,-2.60,.39),(2.58-offset,-2.60,.39),(2.58-offset,-2.20,.39)],.056)
    return m

def backup():
    m=Model('Zone A isolated backup')
    m.state={'battery_MWh':1.0,'battery_h':13.3,'PEM_MWh':2.6,'PEM_h':34.7,'mainGridBreaker':'open'}
    m.base('Foundation/Chamfered apron',10.5,5.8)
    ys=(-1.22,1.30)
    for j,y in enumerate(ys):
        p='Pressure hull/'+('Sectioned utility bay' if not j else 'Habitation module')
        z,r=1.59,1.28
        for k in range(6):
            a=-4.38+k*1.32
            lo,hi=(99,339) if not j else (0,360)
            for rad,thick,mat in [(r,.06,'enamel'),(r-.064,.055,'graphite'),(r-.121,.043,'titanium')]:
                m.arch(p+'/Shell laminates',mat,a,a+1.32,y,z,rad-thick,rad,lo,hi)
            m.arch(p+'/Reinforcing hoops','steel',a-.03,a+.045,y,z,r-.15,r+.045,lo,hi)
        for x in [-4.39,3.54]:
            m.rod(p,'steel',(x-.045,y,z),(x+.045,y,z),r,64)
            m.rod(p,'enamel',(x-.066,y,z),(x+.066,y,z),r-.075,64)
        hatch(m,p+'/Access lock',-4.46,y,z,.68)
        for x in (-3.55,-.6,2.65):
            m.box(p,'graphite',(x,y,.38),(.36,1.86,.38),.055,.15)
    m.rod('Pressure hull/Transfer tunnel','steel',(.23,-.6,1.41),(.23,.68,1.41),.53,36)
    for x in (-2.77,1.13):
        p='Pressure hull/Habitation roof fittings'
        m.rod(p,'graphite',(x,1.30,2.80),(x,1.30,2.91),.35,36)
        m.turned(p,'titanium',(x,1.30,2.91),(0,0,1),[(0,.36),(.036,.36),(.078,.31),(.092,.23)])
        for dx in (-.15,.15):
            m.box(p,'graphite',(x+dx,1.30,3.004),(.035,.20,.029),.007)
    service(m,ys,4.09,2.37)
    m.box('Equipment bay/Deck','steel',(-.38,-1.34,.99),(7.82,2.17,.17),.055,.12)
    for i,x in enumerate((-3.70,-2.93,-2.16)):
        p=f'Battery bank/Drawer column {i+1}'
        m.box(p,'graphite',(x,-1.37,1.65),(.72,.78,1.18))
        for z in np.linspace(1.23,2.03,5):
            m.box(p,'steel',(x,-1.79,z),(.65,.09,.17),.018)
            m.box(p,'seal',(x,-1.85,z),(.31,.044,.065),.012)
            m.box(p,'mintlit',(x+.233,-1.85,z),(.093,.038,.036),.007)
    for i,x in enumerate((-1.34,-.37)):
        p=f'PEM generation/Fuel cell stack {i+1}'
        m.box(p,'enamel',(x,-1.40,1.71),(.88,.88,1.28),.065)
        louver(m,p,x,-1.856,1.72,.66,.69)
        m.box(p,'amber',(x,-1.87,2.15),(.59,.045,.056),.009)
    for i,(x,r,h,col) in enumerate(((.55,.36,1.27,'green'),(1.31,.36,1.27,'green'),(2.00,.25,1.01,'cyan'),(2.57,.25,1.01,'cyan'))):
        p='Gas storage/'+('Hydrogen' if i<2 else 'Oxygen')
        m.tank(p,x,-1.39,1.08,r,h,col)
        m.pipe(p+'/Manifold','steel',[(x,-1.39,1.08+h),(x,-1.39,2.56),(x,-.99,2.56),(-.42,-.99,2.56),(-.42,-1.27,2.29)],.031)
    p='Dedicated life support/Power bus'
    m.pipe(p,'green',[(-3.76,-1.86,1.13),(-3.76,-2.14,1.13),(2.98,-2.14,1.13),(2.98,-2.14,1.88),(2.98,1.27,1.88)],.061)
    for x in np.arange(-3.35,3,.64):
        m.box(p,'graphite',(x,-2.14,1.13),(.056,.146,.145),.013)
    m.box('Dedicated life support/Circulation fan','graphite',(3.12,-1.19,1.53),(.65,.71,.86))
    m.rod('Dedicated life support/Circulation fan','steel',(3.12,-1.54,1.60),(3.12,-1.62,1.60),.27)
    for t in np.arange(6)*pi/3:
        m.rod('Dedicated life support/Circulation fan','graphite',(3.12,-1.64,1.60),(3.12+.23*cos(t),-1.64,1.60+.23*sin(t)),.023)
    p='External grid/Open knife disconnect'
    m.box(p,'graphite',(3.16,-2.48,.36),(.85,.40,.16))
    for x in (2.90,3.42):
        m.rod(p,'porcelain',(x,-2.48,.42),(x,-2.48,.60),.082)
        m.rod(p,'amber',(x,-2.48,.58),(x,-2.48,.66),.055)
    m.rod(p,'orange',(2.90,-2.48,.65),(3.13,-2.48,.91),.045)
    return m
