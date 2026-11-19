"""Teaching hardware for the Mars microgrid and 1U payload. One unit is 25 mm."""
from math import cos, sin, pi, radians
import numpy as np

from geometry import Model

UNIT_M = .025


def place(model, component, parent, origin, rotation=None):
    """Mount a reusable assembly in a local rigid frame, preserving its named parts."""
    basis = np.eye(3) if rotation is None else np.asarray(rotation)
    for part, materials in component.parts.items():
        path = parent + ('/' + part if part else '')
        for mat, blocks in materials.items():
            for vertices, normals, triangles in blocks:
                model.parts[path][mat].append((vertices @ basis.T + origin, normals @ basis.T, triangles))


def rot_y(angle):
    c, s = cos(angle), sin(angle)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def ring(m, p, mat, x, y, z, outer, inner, height, start=0, sweep=360):
    """Annular wall with a real bore and, on partial shells, two cut edges."""
    angles = np.linspace(radians(start), radians(start+sweep), max(3, round(sweep/5))+1)
    profile = [(outer, z), (outer, z+height), (inner, z+height), (inner, z)]
    strips = [np.column_stack((x+r*np.cos(angles), y+r*np.sin(angles), np.full(len(angles), h))) for r,h in profile]
    n = len(angles)
    for i in range(4):
        m.mesh(p, mat, np.vstack([strips[i], strips[(i+1)%4]]),
               [(j,j+1,n+j+1,n+j) for j in range(n-1)], smooth=i in (0,2))
    if sweep < 360:
        for k,face in ((0,(0,1,2,3)),(-1,(3,2,1,0))):
            m.mesh(p,mat,[strip[k] for strip in strips],[face])


def screw(m,p,x,y,z,r=.055):
    m.rod(p,'steel',(x,y,z-.018),(x,y,z+.016),r,16)
    m.rod(p,'seal',(x,y,z+.016),(x,y,z+.020),r*.47,6)


def chip(m,p,x,y,z,w,d):
    m.box(p,'seal',(x,y,z+.042),(w,d,.084),.014)
    for sign in (-1,1):
        for dx in np.linspace(-w*.36,w*.36,5):
            m.box(p,'steel',(x+dx,y+sign*d*.52,z+.026),(.028,.085,.031),.005)


def passives(m,p,x,y,z,count=4):
    for i in range(count):
        xx=x+i*.118
        m.box(p,'titanium',(xx,y,z+.028),(.076,.127,.056),.008)
        m.box(p,'clay',(xx,y,z+.036),(.080,.071,.055),.006)


# The matching pad/pin footprints use the same eccentric key and contact positions.
CONTACTS=[(dx,dy) for dx in (-.322,-.138,.046,.230) for dy in (-.086,.086)]
KEYS=[(-.495,-.15,.076),(.49,.13,.055)]


def connector(plug=False):
    m=Model('Keyed low voltage interface',UNIT_M)
    p='Polarized contact carrier'
    if plug:
        m.box(p,'seal',(0,0,.039),(1.17,.46,.078),.018,.055)
        for x,y in CONTACTS:
            m.turned('Gold spring contacts','gold',(x,y,.006),(0,0,-1),
                     [(0,.053),(.076,.053),(.085,.036),(.153,.036),(.174,.017)],16)
        for x,y,r in KEYS:
            m.turned('Asymmetric guide pins','titanium',(x,y,.025),(0,0,-1),
                     [(0,r),(.175,r),(.218,r*.57)],18)
    else:
        m.box(p,'graphite',(0,0,-.060),(1.20,.50,.12),.021,.065)
        for x,y in CONTACTS:
            m.rod('Recessed contact pads','seal',(x,y,-.005),(x,y,.010),.066,18)
            m.rod('Recessed contact pads','gold',(x,y,.009),(x,y,.019),.046,18)
        for x,y,r in KEYS:
            ring(m,'Keyed guide sockets','titanium',x,y,.002,r+.024,r,.027)
    return m


def node_module(kind,band,seated):
    m=Model(kind,UNIT_M)
    p='Cassette housing'
    m.box(p,'graphite',(0,0,.087),(1.34,1.29,.174),.033,.11)
    m.box(p,'enamel',(0,0,.424),(1.28,1.23,.63),.059,.127)
    m.box(p,'steel',(0,0,.738),(1.33,1.28,.104),.028,.14)
    m.box(p,band,(0,0,.795),(1.31,1.25,.095),.022,.14)
    m.box(p,'porcelain',(0,0,.849),(1.21,1.15,.055),.015,.115)
    for side in (-1,1):
        m.box(p,'steel',(side*.58,-.54,.47),(.085,.18,.33),.023)
        for y in (-.43,.43):
            screw(m,p,side*.49,y,.875,.044)
    m.box(p,'graphite',(0,-.617,.47),(.57,.039,.15),.012)
    m.box(p,'mintlit' if seated else 'unlit',(-.17,-.644,.47),(.105,.025,.059),.008)
    for dx in (.03,.15):
        m.box(p,'steel',(dx,-.643,.47),(.059,.020,.028),.004)
    place(m,connector(True),'Underside connector',(0,-.40,0))
    p='Functional head'
    if kind=='Life support':
        ring(m,p,'graphite',0,0,.877,.41,.303,.105)
        m.rod(p,'seal',(0,0,.872),(0,0,.899),.308)
        for i in range(7):
            a=2*pi*i/7
            m.box(p,'steel',(.15*cos(a),.15*sin(a),.934),(.235,.085,.043),.014,rot=a+.48)
        m.rod(p,'teal',(0,0,.924),(0,0,.98),.10)
    elif kind=='Water processing':
        for x in (-.287,.287):
            m.turned(p,'steel',(x,.02,.867),(0,0,1),[(0,.196),(.14,.196),(.19,.148),(.224,.079)])
            ring(m,p,'teal',x,.02,.99,.20,.182,.053)
        m.pipe(p,'cyan',[(-.287,.02,1.08),(-.287,.02,1.30),(.287,.02,1.30),(.287,.02,1.08)],.045,.089)
    elif kind=='Greenhouse':
        m.box(p,'seal',(0,0,.915),(.83,.72,.091),.023,.08)
        for y in (-.20,0,.20):
            m.box(p,'teal',(0,y,.975),(.66,.11,.056),.012)
        m.box(p,'glass',(0,0,1.042),(.83,.70,.245),.074,.10)
        for x in (-.30,.30):
            m.pipe(p,'steel',[(x,-.37,.927),(x,-.37,1.17),(x,.37,1.17),(x,.37,.927)],.025,.065)
    else:
        m.box(p,'graphite',(0,0,.907),(.87,.76,.081),.021,.09)
        for x in (-.27,0,.27):
            m.box(p,'steel',(x,0,.966),(.11,.67,.05),.013)
        for y in (-.25,.25):
            m.pipe(p,'amber',[(-.31,y,.977),(-.31,y,1.11),(.31,y,1.11),(.31,y,.977)],.039,.068)
    return m


def microgrid():
    m=Model('2035 Mars microgrid interface demonstrator',UNIT_M)
    m.state={'interface':'2035 educational low-voltage DC demonstrator','releasedNode':'D cargo','withdrawal_mm':15}
    m.base('Bench/Anodized training plate',10.60,3.55,.21,'graphite',.37)
    for x in (-4.67,4.67):
        m.box('Bench/Edge protectors','steel',(x,-1.73,.17),(.61,.049,.063),.012)
    p='Distribution/Insulated busway'
    m.box(p,'seal',(.49,-.28,.29),(8.65,2.15,.16),.05,.19)
    for y,w,mat in [(-1.08,.22,'green'),(-.78,.077,'cyan'),(-.53,.20,'orange')]:
        m.box(p,'titanium',(.39,y,.398),(8.92,w+.065,.088),.012)
        m.box('Distribution/'+mat+' bus',mat,(.39,y,.456),(8.90,w,.09),.018)
    for x in (-2.95,-1.20,.57,2.37,4.56):
        for y in (-1.08,-.53):
            screw(m,p,x,y,.504,.046)
    for y in (.28,.91):
        m.box(p,'steel',(.48,y,.40),(8.62,.105,.19),.016)
    xs=(-2.20,-.36,1.48,3.32)
    for i,(x,kind,band) in enumerate(zip(xs,('Life support','Water processing','Greenhouse','Cargo'),('green','cyan','violet','amber'))):
        y=.25
        p=f'Four receiver slots/Slot {i+1}'
        m.box(p,'titanium',(x,y,.49),(1.59,1.53,.23),.04,.16)
        m.box(p,'seal',(x,y,.62),(1.39,1.32,.078),.025,.11)
        for side in (-1,1):
            m.box(p,'steel',(x+side*.718,y,.70),(.087,1.18,.287),.022,.036)
            m.box(p,band,(x+side*.722,y-.39,.85),(.074,.22,.035),.010)
        for yy,mat in [(-1.08,'green'),(-.53,'orange'),(-.78,'cyan')]:
            m.box(p,mat,(x+.48+(yy+1.08)*.45,(yy-.25)/2,.45),(.07,-.22-yy,.052),.01)
        place(m,connector(),p+'/Standard receptacle',(x,y-.40,.658))
        z=.679+(.015/UNIT_M if i==3 else 0)
        place(m,node_module(kind,band,i<3),f'Hot plug nodes/{kind}',(x,y,z))
    p='Distribution/Power combining terminal'
    m.box(p,'steel',(-4.22,-.04,.43),(1.47,2.67,.26),.06,.17)
    m.box(p,'enamel',(-4.22,-.04,.82),(1.40,2.59,.70),.08,.16)
    m.box(p,'porcelain',(-4.22,-.04,1.18),(1.42,2.63,.13),.04,.18)
    for yy in np.linspace(.03,.91,7):
        m.box(p,'graphite',(-4.22,yy,1.254),(.80,.053,.025),.007)
    for x in (-4.72,-3.72):
        for y in (-1.06,.98):
            screw(m,p,x,y,1.25)
    for i,col in enumerate(('green','cyan','amber')):
        m.box(p,col,(-4.50+i*.28,-.80,1.259),(.14,.14,.036),.012)
    m.turned(p,'steel',(-4.22,-1.34,.83),(0,-1,0),[(0,.21),(.095,.21),(.12,.155)],20)
    m.rod(p,'seal',(-4.22,-1.44,.83),(-4.22,-1.47,.83),.122)
    return m


def solar_wing():
    m=Model('Photovoltaic wing',UNIT_M)
    m.box('Carrier','graphite',(1.53,0,0),(3.06,3.54,.115),.035,.145)
    for x in np.linspace(.40,2.65,4):
        for y in np.linspace(-1.28,1.28,4):
            m.box('Photovoltaic cells','solar',(x,y,.069),(.689,.776,.032),.009,.075)
            for off in (-.15,.15):
                m.box('Cell metallization','steel',(x+off,y,.087),(.011,.66,.008),.002)
        for y in (-1.65,1.65):
            m.box('Interconnect tabs','gold',(x,y,.089),(.112,.14,.012),.003)
    return m


def cubesat():
    m=Model('1U thermoelectric teaching payload',UNIT_M)
    m.state={'frameEnvelope_mm':[100,100,100],'stack':'Three-level PC/104-style teaching layout'}
    m.base('Display/Chamfered plinth',4.86,4.86,.20,'enamel',.38)
    base=.35
    p='1U frame/Four corner rails'
    for x in (-1.84,1.84):
        for y in (-1.84,1.84):
            m.box('Display/Isolators','graphite',(x,y,.265),(.46,.46,.17),.031)
            m.box(p,'titanium',(x,y,base+2),(.32,.32,4),.033,.038)
            m.box(p,'graphite',(x*.957,y*.957,base+2),(.18,.18,3.55),.019)
            for z in (base+.32,base+3.68):
                inward=-np.sign(y)
                m.rod(p,'graphite',(x,y+inward*.157,z),(x,y+inward*.172,z),.068,12)
            m.turned('Deploy hardware/Spring feet','steel',(x,y,base+4),(0,0,1),[(0,.112),(.045,.112),(.055,.069),(.17,.069),(.19,.096),(.226,.092)])
            for dz in (.080,.110,.14):
                ring(m,'Deploy hardware/Spring feet','graphite',x,y,base+4+dz,.082,.065,.012)
    for z in (base+.12,base+3.88):
        p='1U frame/Perimeter rails'
        for s in (-1,1):
            m.box(p,'steel',(0,s*1.84,z),(3.68,.245,.24),.035)
            m.box(p,'steel',(s*1.84,0,z),(.245,3.68,.24),.035)
    p='1U frame/Rear shear braces'
    for sign in (-1,1):
        m.rod(p,'graphite',(sign*1.73,1.85,base+.23),(-sign*1.73,1.85,base+3.79),.082,8)
    for x in (-1.47,1.47):
        for y in (-1.33,1.33):
            p='Payload stack/Spacers and tie rods'
            m.rod(p,'titanium',(x,y,base+.12),(x,y,base+3.53),.068,12)
            for z in (base+.42,base+1.99,base+3.23):
                m.rod(p,'gold',(x,y,z-.095),(x,y,z+.095),.117,6)
    z=base+.43
    p='Payload stack/Lower thermal stage'
    m.box(p,'graphite',(0,0,z),(3.45,3.15,.16),.03,.15)
    m.box(p,'orange',(-.67,-.33,z+.185),(1.57,1.62,.23),.048,.18)
    m.box(p,'graphite',(-.67,-.33,z+.305),(1.32,1.40,.09),.025)
    for offset,mat,width in [(0,'porcelain',1.40),(.087,'graphite',1.34),(.15,'porcelain',1.40)]:
        m.box(p+'/Ceramic TEG',mat,(-.67,-.33,z+.39+offset),(width,1.40,.08),.015)
    m.box(p+'/Cold-side radiator','steel',(-.67,-.33,z+.64),(1.31,1.29,.13),.02)
    for xx in np.linspace(-1.24,-.10,10):
        m.box(p+'/Cold-side radiator','graphite',(xx,-.33,z+.89),(.067,1.27,.44),.014)
    p='Payload stack/Emergency cell'
    m.turned(p,'teal',(.94,-1.10,z+.44),(0,1,0),[(0,.30),(.08,.34),(2.13,.34),(2.20,.30)])
    for y in (-.72,.72):
        m.rod(p,'graphite',(.94,y-.07,z+.44),(.94,y+.07,z+.44),.36)
        m.box(p,'steel',(.94,y,z+.15),(.84,.19,.12),.025)
    m.rod(p,'titanium',(.94,-1.19,z+.44),(.94,-1.09,z+.44),.193)
    p='Payload stack/Power and telemetry board'
    mid=base+2.02
    m.box(p,'pcb',(0,.05,mid),(3.44,3.04,.106),.02,.17)
    chip(m,p,-.63,-.44,mid+.058,.60,.52)
    chip(m,p,.36,-.58,mid+.058,.41,.36)
    for y in (-1.13,-.88,.29):
        passives(m,p,-1.01,y,mid+.058,8)
    # Fine copper traces terminate at plated vias and component pads.
    for i in range(6):
        x=-1.19+i*.10
        yy=.43+i*.073
        path=[(x,-.13,mid+.061),(x,.14,mid+.061),(x+.22,.36,mid+.061),
              (x+.22,yy,mid+.061),(.76,yy,mid+.061)]
        m.pipe(p+'/Signal traces','teal',path,.012,.018,8)
        m.rod(p+'/Signal traces','gold',(.76,yy,mid+.061),(.76,yy,mid+.074),.026,12)
    for x in (-.85,-.29):
        m.box(p,'graphite',(x,1.04,mid+.16),(.41,.43,.20),.032)
        ring(m,p,'copper',x,1.04,mid+.255,.147,.085,.071)
    for x in (.25,.60):
        m.turned(p,'titanium',(x,.06,mid+.065),(0,0,1),[(0,.112),(.21,.112),(.224,.094)])
    for x in (-1.47,1.47):
        for y in (-1.33,1.33):
            screw(m,p,x,y,mid+.113,.105)
    p='Payload stack/Gold stack-through header'
    for level in (z+.16,mid-.10,mid+.12,base+3.16):
        m.box(p,'seal',(-1.565,-.06,level),(.25,1.70,.135),.024)
    for y in np.linspace(-.81,.69,16):
        for x in (-1.618,-1.512):
            m.rod(p,'gold',(x,y,z+.18),(x,y,base+3.27),.034,4)
    p='Payload stack/Upper antenna deck'
    m.box(p,'pcb',(0,.26,base+3.26),(3.40,2.66,.096),.018,.15)
    for x in (-1.47,1.47):
        m.box(p,'pcb',(x,-1.19,base+3.26),(.39,.58,.096),.017,.07)
        screw(m,p,x,-1.33,base+3.34,.096)
    m.box(p,'enamel',(-.40,.23,base+3.36),(1.67,1.12,.14),.038,.13)
    for offset in (0,.16):
        m.pipe(p+'/Folded antenna','titanium',[(-1.40,-.63+offset,base+3.37),(-1.40,1.04,base+3.52),(.98,1.04-offset,base+3.52),(.98,-.38,base+3.52),(-.83,-.38+offset,base+3.52)],.031,.10)
    for x in (-1.42,.98):
        m.box(p,'amber',(x,.25,base+3.50),(.14,.17,.14),.018)
    hinge=(1.99,0,base+3.95)
    place(m,solar_wing(),'Deploy hardware/Solar wing',hinge,rot_y(radians(-26)))
    for y in (-1.17,-.72,.72,1.17):
        m.rod('Deploy hardware/Hinge knuckles','titanium',(1.99,y-.14,hinge[2]),(1.99,y+.14,hinge[2]),.137)
    m.rod('Deploy hardware/Hinge knuckles','gold',(1.99,-1.45,hinge[2]),(1.99,1.45,hinge[2]),.062)
    p='Payload stack/Teaching DC interface'
    m.box(p,'enamel',(-.27,-1.71,base+.46),(1.52,.29,.72),.039,.09)
    place(m,connector(),p+'/Standard receptacle',(-.27,-1.87,base+.47),[[1,0,0],[0,0,-1],[0,1,0]])
    for x,col in ((.63,'red'),(.77,'seal')):
        m.pipe('Payload stack/Managed harness',col,[(x,-1.10,z+.46),(x,-1.34,z+.46),(x+.40,-1.34,z+.62),(x+.40,-1.29,mid-.11)],.038,.105)
    return m
