"""Static CanSat payload exhibit and portable ground telemetry receiver."""
from math import cos, sin, pi, radians
import numpy as np

from geometry import Model
from interfaces import UNIT_M, place, ring, screw, rot_y, chip, passives


def fairing():
    m=Model('Upper fairing exhibit',UNIT_M)
    r=1.63
    start,sweep=-47,240
    p='Open payload bay'
    ring(m,p,'enamel',0,0,0,r,r-.090,5.05,start,sweep)
    for z,h,mat in [(0,.17,'graphite'),(.20,.065,'steel'),(1.30,.105,'steel'),
                    (3.44,.093,'steel'),(4.83,.21,'graphite')]:
        ring(m,p+'/Sectioned frames',mat,0,0,z,r+.012,r-.16,h,start,sweep)
    for deg in (start,start+sweep):
        a=radians(deg)
        m.rod(p+'/Cut edge trim','titanium',((r-.035)*cos(a),(r-.035)*sin(a),.06),
              ((r-.035)*cos(a),(r-.035)*sin(a),4.95),.046)
    for deg in (20,85,150):
        a=radians(deg)
        m.rod(p+'/Inner stringers','steel',((r-.14)*cos(a),(r-.14)*sin(a),.16),
              ((r-.14)*cos(a),(r-.14)*sin(a),4.89),.055)
    p='Nose fairing'
    origin=(0,0,5.05)
    # A display shell with continuous conical bands above the empty section.
    stations=[(0,1.63),(.16,1.63),(.36,1.60),(.62,1.54),(.89,1.45),
              (1.15,1.34),(1.43,1.21),(1.71,1.06),(1.98,.89),(2.29,.68),
              (2.54,.49),(2.81,.27),(3.04,.078),(3.09,.027)]
    for i in range(len(stations)-1):
        mat='orange' if 3<=i<=4 else 'amber' if i==5 else 'enamel'
        if i==len(stations)-2: mat='steel'
        m.turned(p,mat,origin,(0,0,1),stations[i:i+2],64)
    ring(m,p,'steel',0,0,5.10,1.648,1.62,.066)
    return m


def packed_canopy(m,z):
    p='Recovery/Folded parachute'
    # Sewn gores wrap around the same folded bundle. Pleats run into the top seam.
    n=96
    profile=[(.01,.75),(.066,.92),(.16,.95),(.25,.89),(.32,.93),(.42,.85),
             (.50,.70),(.57,.48),(.58,.23),(.55,.04)]
    gores=8
    for g in range(gores):
        angles=np.linspace(2*pi*g/gores,2*pi*(g+1)/gores,n//gores+1)
        vertices=[]
        for dz,rad in profile:
            for a in angles:
                folds=1+.061*cos(16*a+.53*dz)+.057*sin(5*a+2.0*dz)
                rho=rad*folds
                texture=.050*(rad+.25)*cos(16*a+.63)+.018*sin(3*a)
                vertices.append((rho*cos(a),rho*sin(a)*.82,z+dz+texture))
        count=len(angles)
        faces=[(k*count+i,k*count+i+1,(k+1)*count+i+1,(k+1)*count+i)
               for k in range(len(profile)-1) for i in range(count-1)]
        m.mesh(p,'orange' if g%4!=1 else 'porcelain',vertices,faces,True)
    m.rod(p,'orange',(0,0,z+.531),(0,0,z+.55),.055,16)
    for x in (-.36,.36):
        m.pipe('Recovery/Soft pack straps','amber',[(x,-.66,z+.04),(x,-.68,z+.32),(x,-.43,z+.51),(x,0,z+.60),(x,.43,z+.52),(x,.64,z+.32),(x,.64,z+.06)],.043,.10)
        m.box('Recovery/Soft pack straps','graphite',(x,-.66,z+.27),(.15,.085,.12),.014)
    m.pipe('Recovery/Visible pull loop','porcelain',[(-.60,-.52,z+.27),(-.76,-.78,z+.22),(-.91,-.87,z-.18),(-1.06,-.78,z-.36),(-1.14,-.61,z-.20),(-.97,-.54,z+.03)],.036,.13)


def cansat():
    m=Model('Atmospheric sensor CanSat',UNIT_M)
    r,h=1.32,4.60
    p='Canister/Observation window'
    # Top and bottom collars stay continuous. Only the inspection window is removed.
    ring(m,p,'titanium',0,0,.08,r-.035,r-.107,.46)
    ring(m,p,'enamel',0,0,.54,r-.035,r-.107,3.47,-52,253)
    ring(m,p,'enamel',0,0,4.01,r-.035,r-.107,.48)
    for z in (0,h-.12):
        ring(m,'Canister/Rolled rims','steel',0,0,z,r,r-.124,.12)
    for z in (.42,4.12):
        ring(m,'Canister/Telemetry bands','teal',0,0,z,r-.023,r-.044,.104)
    for z in (.55,3.95):
        ring(m,p,'steel',0,0,z,r-.025,r-.12,.058,-52,253)
    m.rod('Canister/Base closure','graphite',(0,0,.04),(0,0,.12),r-.10,56)
    m.rod('Canister/Recovery deck','titanium',(0,0,h-.14),(0,0,h-.065),r-.10,56)
    for z in (.70,2.10,3.37):
        p='Electronics/'+{.70:'Battery board',2.10:'Telemetry board',3.37:'Sensor board'}[z]
        m.rod(p,'pcb',(0,0,z),(0,0,z+.094),1.12,56)
        for a in np.radians([0,120,240]):
            x,y=.93*cos(a),.93*sin(a)
            m.rod('Electronics/Standoffs','gold',(x,y,z+.094),(x,y,min(z+1.38,4.41)),.062,6)
            screw(m,p,x,y,z+.098,.079)
        chip(m,p,-.30,-.20,z+.098,.43,.37)
        passives(m,p,.13,-.32,z+.098,4)
        for i in range(6):
            m.rod(p,'gold',(i*.13-.32,-.75,z+.093),(i*.13-.32,-.75,z+.113),.030,12)
    p='Electronics/Compact battery'
    m.turned(p,'teal',(.41,-.50,.85),(0,0,1),[(0,.23),(.05,.27),(1.00,.27),(1.06,.22)])
    for z in (1.03,1.66):
        ring(m,p,'graphite',.41,-.50,z,.28,.25,.091)
    m.pipe(p,'red',[(.41,-.50,1.90),(.41,-.50,1.97),(.71,-.42,1.97),(.71,-.42,2.12)],.032,.05)
    p='Electronics/Pressure and temperature sensors'
    m.box(p,'titanium',(.23,-.43,3.66),(.45,.40,.31),.048)
    m.rod(p,'graphite',(.23,-.43,3.81),(.23,-.43,3.835),.064)
    m.turned(p,'steel',(-.49,-.69,3.54),(0,-.92,.39),[(0,.095),(.14,.095),(.17,.047),(.35,.047),(.39,.026)])
    for z in (2.30,2.45):
        m.box('Electronics/Radio package','graphite',(0,.07,z),(.86,.70,.14),.024)
    m.pipe('Electronics/Telemetry loom','cyan',[(.79,-.45,2.18),(.92,-.46,2.34),(.92,-.46,3.25),(.74,-.49,3.48)],.032,.09)
    packed_canopy(m,h-.05)
    return m


def receiver():
    m=Model('Portable ground telemetry receiver',UNIT_M)
    p='Enclosure'
    for x in (-1.38,1.38):
        for y in (-.83,.83):
            m.box(p+'/Feet','seal',(x,y,.10),(.46,.39,.20),.045)
    m.box(p,'graphite',(0,0,.30),(3.62,2.34,.31),.07,.21)
    m.box(p,'enamel',(0,0,.83),(3.54,2.27,1.00),.10,.20)
    m.box(p,'graphite',(0,0,1.34),(3.58,2.31,.12),.034,.20)
    m.box(p,'porcelain',(0,0,1.44),(3.62,2.34,.14),.049,.21)
    for x in (-1.47,1.47):
        for y in (-.91,.91):
            screw(m,p,x,y,1.513,.066)
    p='Front panel/Blank OLED'
    m.box(p,'steel',(-.31,-1.153,.86),(2.34,.12,.77),.042,.09)
    m.box(p,'seal',(-.31,-1.222,.86),(2.17,.072,.66),.027)
    m.box(p,'screen',(-.31,-1.265,.86),(1.96,.027,.48),.009)
    for i,mat in enumerate(('mintlit','cyan','unlit')):
        m.rod('Front panel/Status lamps',mat,(1.14+i*.19,-1.143,1.06),(1.14+i*.19,-1.177,1.06),.046)
    m.turned('Front panel/Replay control','graphite',(1.28,-1.12,.72),(0,-1,0),[(0,.21),(.18,.21),(.203,.185)])
    m.rod('Front panel/Replay control','steel',(1.28,-1.32,.72),(1.28,-1.344,.72),.128)
    p='Removable telemetry antenna'
    m.turned(p,'steel',(.96,.47,1.51),(0,0,1),[(0,.24),(.09,.24),(.12,.177),(.28,.177)])
    m.turned(p,'gold',(.96,.47,1.77),(0,0,1),[(0,.135),(.13,.135),(.15,.105)],8)
    m.turned(p,'graphite',(.96,.47,1.89),(0,0,1),[(0,.14),(.20,.14),(.47,.082)])
    m.turned(p,'titanium',(.96,.47,2.35),(0,0,1),[(0,.064),(1.19,.064),(1.21,.044),(2.02,.044),(2.04,.031),(2.49,.031)])
    m.rod(p,'graphite',(.96,.47,4.82),(.96,.47,4.92),.048)
    for x in np.linspace(-1.25,-.17,7):
        m.box('Enclosure/Top grille','graphite',(x,.35,1.527),(.060,.70,.025),.009)
    for x in (-1.10,.19):
        m.box('Portable handle/Anchors','steel',(x,-.53,1.55),(.26,.27,.14),.03)
    m.pipe('Portable handle/Grip','graphite',[(-1.10,-.53,1.60),(-1.10,-.53,1.85),(.19,-.53,1.85),(.19,-.53,1.60)],.086,.12)
    return m


def cansat_telemetry():
    m=Model('CanSat separation and telemetry exhibit',UNIT_M)
    m.state={'canisterDiameter_mm':66,'canisterHeight_mm':115,'display':'Static separated payload and ground station'}
    place(m,fairing(),'Upper rocket fairing',(-2.22,1.00,1.02),rot_y(radians(-27)))
    place(m,cansat(),'Separated CanSat',(-.30,-1.35,.30),rot_y(radians(-11)))
    place(m,receiver(),'Ground receiver',(3.97,-.32,0))
    return m
