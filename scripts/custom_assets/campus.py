"""Six school loads on a shared priority-distribution diorama."""
from math import pi,sin,cos
import numpy as np
from geometry import Model

def building(m,p,x,y,w,d,h,light,bays=4,floors=1,roof='titanium'):
    z=.25
    m.box(p,'steel',(x,y,z+.065),(w+.12,d+.12,.13),.031,.09)
    m.box(p,'enamel',(x,y,z+h/2+.08),(w,d,h),.055,.09)
    for f in range(floors):
        hz=z+.08+h*(f+.52)/floors
        wh=h*.48/floors
        for j in range(bays):
            xx=x+w*((j+.5)/bays-.5)*.90
            ww=w*.77/bays
            m.box(p+'/Windows','graphite',(xx,y-d/2-.007,hz),(ww+.042,.043,wh+.048),.012)
            m.box(p+'/Windows',light,(xx,y-d/2-.031,hz),(ww,.026,wh),.008)
        for j in range(2):
            yy=y+d*((j+.5)/2-.5)*.81
            m.box(p+'/Windows','graphite',(x-w/2-.012,yy,hz),(.040,d*.25+.035,wh+.033),.009)
            m.box(p+'/Windows',light,(x-w/2-.036,yy,hz),(.018,d*.25,wh),.005)
    top=z+h+.08
    m.box(p,'graphite',(x,y,top),(w+.12,d+.12,.092),.025,.09)
    m.box(p,roof,(x,y,top+.071),(w+.16,d+.16,.091),.022,.10)
    return top+.12

def track_line(m,p,x,y,w,d,z,r):
    radius=d/2
    pts=[]
    for dx,offset in [(w/2-radius,-pi/2),(-w/2+radius,pi/2)]:
        for t in np.linspace(offset,offset+pi,26):
            pts.append((x+dx+radius*cos(t),y+radius*sin(t),z))
    pts.append(pts[0])
    for a,b in zip(pts,pts[1:]):
        m.rod(p,'steel',a,b,r,8)

def campus():
    m=Model('School blackout priority diorama',2)
    m.base('Site/Plinth',10.9,7.0,.25,'enamel',.62)
    # Distribution routes sit in shallow dark channels and terminate at each building.
    for x,y,col in [(-3.77,-1.70,'green'),(-1.05,-1.70,'green'),(1.70,-1.70,'green'),(-3.10,1.56,'cyan'),(.25,1.58,'cyan'),(3.65,1.70,'graphite')]:
        route={'green':-.52,'cyan':-.25,'graphite':.02}[col]
        pts=[(-4.84,route,.273),(x,route,.273),(x,y,.273)]
        m.pipe('Site/Buried cable channels','graphite',pts,.055,.06)
        m.pipe('Site/Priority circuits',col,[(a,b,c+.028) for a,b,c in pts],.031,.06)
    m.box('Site/Distribution cabinet','graphite',(-4.83,-.24,.42),(.45,.96,.32))
    m.box('Site/Distribution cabinet','steel',(-4.83,-.24,.59),(.47,.98,.067))
    for yy,mat in [(-.52,'green'),(-.25,'cyan'),(.02,'seal')]:
        m.box('Site/Distribution cabinet',mat,(-4.83,yy,.63),(.26,.10,.037),.008)
    p='Essential/Broadcast station'
    x,y=-3.77,-1.75
    top=building(m,p,x,y,1.83,1.35,.83,'mintlit',3)
    m.box(p,'graphite',(x-.34,y,top+.10),(.56,.47,.19))
    for sx,sy in [(-.24,-.17),(.24,-.17),(0,.24)]:
        m.rod(p,'steel',(x+sx,y+sy,top),(x+sx*.16,y+sy*.16,top+1.20),.029)
    for h in (.28,.57,.84):
        f=1-h/1.34
        m.rod(p,'steel',(x-.24*f,y-.17*f,top+h),(x+.24*f*.75,y-.17*f*.75,top+h+.23),.019)
    m.rod(p,'steel',(x,y,top+.94),(x,y,top+1.48),.026)
    for dx in (-.22,.22):
        m.box(p,'enamel',(x+dx,y,top+1.15),(.116,.10,.51),.026,tilt=.06)
    p='Essential/Drinking water pump house'
    x,y=-1.05,-1.70
    top=building(m,p,x,y,1.56,1.21,.63,'mintlit',2)
    for dx in (-.40,.40):
        m.tank(p+'/Filter vessels',x+dx,y+.07,top,.22,.50,'teal')
        m.pipe(p+'/Filter vessels','teal',[(x+dx,y+.07,top+.56),(x+dx,y-.36,top+.56),(x+dx,y-.36,top+.12)],.047)
    p='Essential/Infirmary'
    x,y=1.70,-1.70
    top=building(m,p,x,y,2.00,1.52,.92,'mintlit',3,roof='porcelain')
    m.box(p,'teal',(x,y-.79,.88),(.67,.06,.80))
    m.box(p,'mintlit',(x,y-.835,.79),(.43,.029,.46))
    m.box(p,'teal',(x,y-1.00,1.19),(1.07,.61,.095),.026)
    for dx in (-.44,.44):
        m.rod(p,'steel',(x+dx,y-1.22,.25),(x+dx,y-1.22,1.17),.026)
    for w,d in [(.61,.19),(.19,.61)]:
        m.box(p,'teal',(x,y+.03,top+.018),(w,d,.037),.006)
    p='Reduced/Classroom block'
    x,y=-3.03,1.58
    top=building(m,p,x,y,2.91,1.60,1.60,'coollit',6,2)
    m.box(p,'steel',(x,y-.83,1.13),(2.99,.16,.075))
    m.box(p,'enamel',(x+.71,y+.14,top+.10),(.82,.71,.22))
    for dx in np.linspace(-.34,.17,3):
        m.box(p,'graphite',(x+dx,y+.17,top+.038),(.17,.42,.065))
    p='Reduced/Science laboratory'
    x,y=.31,1.56
    top=building(m,p,x,y,2.21,1.56,1.17,'coollit',4)
    for dx in (-.57,0,.57):
        m.box(p,'steel',(x+dx,y,top+.16),(.43,1.08,.25),.035)
        m.box(p,'screen',(x+dx,y-.01,top+.30),(.36,.92,.055),.016,tilt=.09)
    for dy in (-.32,.27):
        m.rod(p,'steel',(x+.86,y+dy,top),(x+.86,y+dy,top+.57),.084)
        m.rod(p,'graphite',(x+.86,y+dy,top+.54),(x+.86,y+dy,top+.61),.12)
    p='Disconnected/Sports hall'
    x,y=3.60,1.54
    top=building(m,p,x,y,2.23,1.78,.93,'screen',4,roof='graphite')
    for dx in np.linspace(-1.08,1.08,8):
        m.arch(p+'/Barrel roof','steel',x+dx-.016,x+dx+.016,y,top-.97,1.38,1.40,48,132)
    m.arch(p+'/Barrel roof','graphite',x-1.14,x+1.14,y,top-.97,1.35,1.38,48,132)
    p='Disconnected/Field and floodlights'
    x,y=3.96,-1.36
    m.box(p,'asphalt',(x,y,.281),(2.18,2.54,.061),.016,.30)
    for d in (1.22,1.43,1.63):
        track_line(m,p,x,y,1.97,d,.319,.012)
    for yy in (-2.53,-.19):
        m.rod(p,'graphite',(4.78,yy,.29),(4.78,yy,1.58),.039)
        m.box(p,'graphite',(4.78,yy,1.60),(.49,.16,.23),.023,tilt=-.25)
        m.box(p,'unlit',(4.78,yy-.085,1.59),(.37,.018,.15),.007,tilt=-.25)
    return m
