"""Desktop teaching rigs. One authoring unit is five centimetres."""
from math import pi, cos, sin
import numpy as np
from geometry import Model, unit

def mat(m):
    m.base('Bench/Antistatic base',8.4,4.65,.18,'graphite',.40)
    for x in (-3.48,3.48):
        m.box('Bench/Metal edge inserts','steel',(x,-2.27,.145),(.68,.042,.045),.008)
    for x in (-3.87,3.87):
        for y in (-1.52,1.52):
            m.rod('Bench/Captive fasteners','seal',(x,y,.17),(x,y,.198),.085,20)
            m.box('Bench/Captive fasteners','steel',(x,y,.199),(.077,.014,.012),.002)

def socket(m,p,x,y,z,mat):
    m.rod(p,'graphite',(x,y+.08,z),(x,y-.02,z),.108)
    m.rod(p,mat,(x,y-.01,z),(x,y-.11,z),.071)
    m.rod(p,'seal',(x,y-.10,z),(x,y-.22,z),.047)

def lamp_meter():
    m=Model('Low voltage DC load experiment',.05)
    mat(m)
    p='DC supply/Enclosure'
    m.box(p,'seal',(-2.60,.16,.32),(2.09,1.74,.25),.06,.16)
    m.box(p,'enamel',(-2.60,.16,.75),(2.07,1.72,.85),.085,.17)
    m.box(p,'titanium',(-2.60,.16,1.18),(2.12,1.76,.115),.035,.16)
    for x in np.linspace(-3.34,-3.01,5):
        m.box(p,'seal',(x,.30,1.241),(.033,.75,.012),.003)
    for x in (-3.42,-1.79):
        for y in (-.49,.80):
            m.rod(p,'graphite',(x,y,1.229),(x,y,1.255),.041,6)
    p='DC supply/Two-position toggle'
    m.box(p,'graphite',(-2.26,.17,1.25),(.76,.75,.07),.03,.10)
    m.rod(p,'steel',(-2.26,.17,1.27),(-2.26,.17,1.39),.17,6)
    m.rod(p,'titanium',(-2.26,.17,1.36),(-2.26,-.02,1.75),.052)
    m.rod(p,'amber',(-2.26,.01,1.66),(-2.26,-.065,1.80),.079)
    for y in (-.11,.46):
        m.box(p,'enamel',(-2.26,y,1.292),(.23,.029,.015),.004)
    for dx,col in [(-.22,'red'),(.22,'seal')]:
        socket(m,'DC supply/Output jacks',-2.60+dx,-.72,.67,col)
    p='Meter/Transparent enclosure'
    x,y=-.17,-.92
    m.box(p,'graphite',(x,y,.32),(1.58,1.0,.21),.055,.12)
    m.box(p,'pcb',(x,y,.49),(1.40,.83,.09))
    m.box(p,'glass',(x,y,.62),(1.63,1.04,.56),.072,.13)
    m.box('Meter/Blank OLED','graphite',(x,y,.86),(1.18,.68,.10),.035,.08)
    m.box('Meter/Blank OLED','screen',(x,y,.921),(.96,.51,.035),.015,.045)
    for dx in (-.66,.66):
        for dy in (-.37,.37):
            m.rod(p,'amber',(x+dx,y+dy,.41),(x+dx,y+dy,.86),.045,12)
            m.rod(p,'steel',(x+dx,y+dy,.86),(x+dx,y+dy,.90),.055,6)
    for s in (-1,1):
        m.box(p,'steel',(x+s*.85,y,.53),(.22,.42,.22),.033)
        m.box(p,'seal',(x+s*1.01,y,.53),(.23,.33,.17),.033)
    for dx,col in [(-.22,'red'),(.22,'seal')]:
        m.pipe('Wiring/Supply to inline meter',col,[(-2.60+dx,-.90,.67),(-2.60+dx,-1.54+dx,.30),(-1.51+dx*.4,-1.54+dx,.30),(-1.49+dx*.4,y+dx*.26,.51),(-1.18,y+dx*.26,.53)],.038,.19)
    p='Experimental lamp/Articulated stand'
    x,y=2.42,-.52
    m.turned(p,'steel',(x,y,.18),(0,0,1),[(0,.70),(.045,.79),(.18,.73),(.24,.56)])
    m.rod(p,'graphite',(x,y,.40),(x,y,.68),.21)
    m.pipe(p,'titanium',[(x,y,.53),(x,y,1.45),(x+.39,y+.20,2.02),(x+.31,y+.29,2.48)],.084)
    for dx in (-.11,.11):
        m.rod(p,'graphite',(x+dx,y,1.41),(x+.40+dx,y+.20,2.03),.043)
    for cx,cy,cz in [(x,y,1.45),(x+.40,y+.20,2.03),(x+.31,y+.29,2.48)]:
        m.rod(p,'steel',(cx,cy-.14,cz),(cx,cy+.14,cz),.13)
        m.rod(p,'amber',(cx,cy-.165,cz),(cx,cy-.13,cz),.069,6)
    p='Experimental lamp/Low voltage LED head'
    origin=np.array([x+.29,y+.29,2.53])
    axis=unit((-.30,-.73,-.39))
    m.turned(p,'enamel',origin,axis,[(0,.18),(.10,.32),(.40,.55),(.46,.57),(.50,.54)])
    m.turned(p,'graphite',origin,axis,[(.49,.54),(.54,.54)])
    m.turned(p,'lamp',origin,axis,[(.537,.47),(.551,.47)])
    m.pipe('Wiring/Meter to lamp','seal',[(.82,-.92,.53),(1.16,-.92,.43),(1.16,-1.32,.24),(2.41,-1.32,.24),(2.41,-1.04,.32)],.045,.14)
    p='Zone cards/Angled magnetic rack'
    m.box(p,'titanium',(.33,1.20,.29),(2.20,.89,.22),.045,.12)
    for j,(dx,col) in enumerate([(-.56,'teal'),(0,'cyan'),(.56,'amber')]):
        m.box(p,'seal',(.33+dx,1.2,.40),(.51,.22,.09))
        m.box(p,'porcelain',(.33+dx,1.26,.72+j*.08),(.49,.064,.79),.026,.048,tilt=-.20)
        m.box(p,col,(.33+dx,1.235,.77+j*.08),(.42,.068,.53),.018,.035,tilt=-.20)
    return m

def teg():
    m=Model('Thermoelectric conversion test bench',.05)
    mat(m)
    x,y=-1.66,.32
    p='Hot stage/Enclosed heater'
    m.box(p,'seal',(x,y,.33),(2.85,2.40,.29),.065,.21)
    m.box(p,'enamel',(x,y,.65),(2.76,2.30,.61),.08,.18)
    m.box(p,'amber',(x,y,.957),(2.19,1.86,.12),.038,.10)
    for dx in (-1.32,1.32):
        for dy in (-1.08,1.08):
            m.rod('Hot stage/Burn guard','steel',(x+dx,y+dy,.64),(x+dx,y+dy,1.14),.060)
    m.pipe('Hot stage/Burn guard','orange',[(x,y-1.08,1.15),(x+1.32,y-1.08,1.15),(x+1.32,y+1.08,1.15),(x-1.32,y+1.08,1.15),(x-1.32,y-1.08,1.15),(x,y-1.08,1.15)],.073,.20)
    for z,matname,w in [(1.06,'porcelain',1.74),(1.126,'graphite',1.66),(1.182,'porcelain',1.74)]:
        m.box('TEG/Ceramic sandwich',matname,(x,y,z),(w,w,.067),.013,.04)
    m.box('Cold stage/Removable fin module','steel',(x,y,1.28),(1.55,1.52,.15))
    for dx in np.linspace(-.72,.72,14):
        m.box('Cold stage/Removable fin module','graphite',(x+dx,y,1.95),(.064,1.47,1.23),.015,.021)
    p='Cold stage/Spare flat plate'
    m.box(p,'seal',(1.72,.92,.25),(2.06,1.76,.12),.035,.13)
    m.box(p,'titanium',(1.72,.92,.36),(1.70,1.52,.13),.025,.06)
    for dx in (-.69,.69):
        for dy in (-.60,.60):
            m.rod(p,'graphite',(1.72+dx,.92+dy,.417),(1.72+dx,.92+dy,.431),.048,20)
    p='Instrumentation/Voltmeter and load'
    m.box(p,'enamel',(1.78,-1.15,.48),(2.47,1.29,.52),.075,.16)
    m.box(p,'graphite',(1.51,-1.20,.75),(1.47,.88,.092),.024,.08)
    m.box(p,'screen',(1.51,-1.22,.80),(1.22,.61,.032),.012,.047)
    for z,r,matname in [(.78,.16,'graphite'),(.83,.13,'steel')]:
        m.rod(p,matname,(2.70,-1.36,z-.06),(2.70,-1.36,z+.03),r)
    m.rod(p,'amber',(2.63,-.94,.80),(2.82,-.94,.80),.080,16)
    for s,col in [(-1,'red'),(1,'seal')]:
        m.pipe('TEG/Electrical leads',col,[(x+s*.22,y-.83,1.12),(x+s*.22,-1.23,.95),(x+s*.22,-1.51+s*.08,.29),(.19+s*.10,-1.51+s*.08,.29),(.19+s*.10,-1.02+s*.10,.53),(.60,-1.02+s*.10,.53)],.037,.17)
    for j,(z,col) in enumerate([(1.02,'amber'),(1.28,'cyan')]):
        q=.15+j*.25
        m.pipe('Instrumentation/Hot and cold temperature probes','steel',[(x+.68,y+q,z),(x+1.11,y+q,z),(x+1.58,y+q,.64),(.28+q,y+q,.26),(.28+q,-.54,.26),(1.15+j*.38,-.54,.52)],.019,.11)
        m.rod('Instrumentation/Hot and cold temperature probes',col,(x+.66,y+q,z),(x+.93,y+q,z),.041)
    return m
