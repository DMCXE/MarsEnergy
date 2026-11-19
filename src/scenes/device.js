function sampleGround(m,section){
  // A clipped geological sample exposes the lower service hardware in section.
  const industrial=state.phase==='p2'||state.phase==='fusion';
  const ring=(a,r,y)=>{
    const edge=1+.033*Math.sin(3*a+.7)+.019*Math.cos(7*a);
    return [r*edge*Math.cos(a),industrial ? -.72+(y+.72)*.30 : y,r*.82*edge*Math.sin(a)];
  };
  const open=section&&!industrial;
  const n=48, start=open?1.38:0,end=open?tau+.1:tau;
  const layers=[[-1.78,metal.strata],[-1.54,metal.rock],[-1.48,metal.strata],[-1.20,metal.rock],[-1.13,metal.strata],[-.83,metal.rock],[-.72,metal.ground]];
  for(let j=0;j<n;j++){
    const a=start+(end-start)*j/n,b=start+(end-start)*(j+1)/n;
    for(let k=1;k<layers.length;k++){
      const low=layers[k-1][0],high=layers[k][0];
      const relief=(angle,y)=>y+.026*Math.sin(4*angle+.65*y);
      m.face([ring(b,3.35,relief(b,low)),ring(a,3.35,relief(a,low)),ring(a,3.35,relief(a,high)),ring(b,3.35,relief(b,high))],layers[k][1]);
    }
    const top=angle=>ring(angle,3.35,-.72+.026*Math.sin(4*angle-.468));
    m.face([[0,-.72,0],top(b),top(a)],metal.ground);
  }
  if(open)for(const angle of [start,end])for(let i=1;i<layers.length;i++){
    const lo=layers[i-1][0],hi=layers[i][0];
    const face=[[0,lo,0],ring(angle,3.35,lo),ring(angle,3.35,hi),[0,hi,0]];
    m.face(angle===start?face:face.reverse(),layers[i][1]);
  }
  // Scattered clasts and dust on the display section; these are not site DEM data.
  for(let j=0;j<105;j++){
    const a=start+(end-start)*((j*.618034+.237)%1),r=1.1+2.05*((j*.38197+.153*j*j)%1);
    const [x,y,z]=ring(a,r,-.708),s=.026+.055*((j*.3141)%1);
    const peak=[x+s*.17,y+s*.57,z-s*.1];
    const corners=Array.from({length:5},(_,i)=>{
      const phi=a+i*tau/5, length=s*(.72+.26*Math.cos(j+i*1.8));
      return [x+length*Math.cos(phi),y-.007,z+length*.76*Math.sin(phi)];
    });
    for(let i=0;i<5;i++)m.face([peak,corners[(i+1)%5],corners[i]],j%3?metal.rock:metal.strata);
  }
}
function radiatorWing(m,a,canopy,dust){
  const pt=(u,v,w=0)=>{
    const r=.38+u*(2.48-.22*v), off=canopy?(v-.5)*1.0:w;
    return [r*Math.cos(a)-off*Math.sin(a),canopy?1.74-.15*u+w:.45+v*(1.52+.34*u)+.13*u,r*Math.sin(a)+off*Math.cos(a)];
  };
  const finish=canopy&&dust>2?metal.rock:metal.graphite;
  m.face([pt(0,0),pt(1,0),pt(1,1),pt(0,1)],finish);
  m.face([pt(0,1,.016),pt(1,1,.016),pt(1,0,.016),pt(0,0,.016)],finish);
  for(const v of [0,1])m.rod(pt(0,v),pt(1,v),.041,metal.titanium);
  for(const u of [0,1])m.rod(pt(u,0),pt(u,1),.034,metal.steel);
  for(const side of [-.008,.023])for(let row=0;row<3;row++){
    const lo=row/3+.017,hi=(row+1)/3-.017;
    const tint=state.umbrellaMode&&dust>2?metal.rock:[[66,76,80,.43],[59,69,74,.43],[73,81,83,.43]][row];
    m.face([pt(.025,lo,side),pt(.973,lo,side),pt(.973,hi,side),pt(.025,hi,side)],tint);
  }
  for(let i=1;i<12;i++){
    const u=i/12;
    for(const side of [-.021,.036])m.rod(pt(u,.025,side),pt(u,.975,side),.013,metal.steel,5);
  }
  m.pipe([pt(.02,.14,.047),pt(.9,.14,.047),pt(.9,.91,.047)],.027,metal.brass);
  m.rod(radial(.38,-.13,a),pt(.77,.03),.052,metal.titanium);
  m.rod(radial(.34,.17,a),pt(.38,.05),.036,metal.steel);
}
function heatPipePlant(m){
  pressureVessel(m,0,0,-1.66,.52,1.62,metal.titanium);
  flange(m,0,-.45,0,.64);
  m.drum(0,.27,0,.33,.88,metal.ceramic);
  for(let i=0;i<4;i++){
    const a=i*tau/4+.25,[x,,z]=radial(.39,0,a);
    m.drum(x,.68,z,.158,.54,metal.titanium);
    for(let j=0;j<5;j++)m.drum(x,.54+j*.065,z,.183,.028,metal.dark,16);
    m.pipe([radial(.27,-1.2,a),radial(.57,-1.02,a),radial(.57,.25,a),[x,.34,z],[x,.51,z]],.065,metal.brass);
  }
  flange(m,0,1.04,0,.50);
  for(let i=0;i<6;i++)radiatorWing(m,i*tau/6+.16,state.umbrellaMode,state.dustTau);
  m.drum(0,1.39,0,.29,.62,metal.steel);
  m.pipe([[.32,-.33,.21],[1.15,-.33,.55],[1.62,-1.15,.85],[2.13,-1.15,.85]],.08,metal.copper);
  m.rod([2.04,-1.15,.85],[2.15,-1.15,.85],.135,metal.steel,16);
  m.pipe([[-1.5,-.66,.95],[-1.5,-.66,.52],[-.37,-.66,.52],[-.37,-.53,.22]],.046,metal.dark);
  serviceCabinet(m,-1.5,-.71,.95);
  m.feature([0,1.05,0],'Converter head','Heat pipes connect the shielded module to the conversion head. The ribbed housings identify the converter assemblies.');
  m.feature(radial(2, state.umbrellaMode?1.62:1.57,.16),'Radiator wing','Dark emitter faces, edge rails and a return manifold form a deployable panel. The diagonal struts support the deployed span.');
  if(state.soilCutaway)m.feature([.4,-1.2,.25],'Buried module','The exposed side shows the emplacement concept and heat-service connection. The ground section is illustrative.');
}
function serviceRail(m,points){
  for(const p of points)m.rod(p,vadd(p,[0,.43,0]),.025,metal.brass,7);
  for(const h of [.21,.43])m.pipe(points.map(p=>vadd(p,[0,h,0])),.022,metal.brass);
}
function heatExchangerBank(m,x,z,y,count){
  for(let i=0;i<count;i++){
    const px=x+i*.25;
    m.box(px,y+.65,z,.09,1.3,1.10,metal.graphite);
    for(let j=0;j<6;j++)m.box(px,y+.13+j*.2,z,.112,.021,1.13,metal.steel);
    m.rod([px,y,z+.47],[px,y+1.32,z+.47],.038,metal.titanium);
  }
  for(const h of [.05,1.23])m.rod([x-.1,y+h,z+.47],[x+(count-1)*.25+.1,y+h,z+.47],.075,metal.copper);
}
function braytonPlant(m){
  deck(m,0,0,-.27,5.2,3.4);
  const x=-1.18,z=-.27;
  pressureVessel(m,x,z,-.17,.77,2.73,metal.ceramic);
  flange(m,x,1.68,z,.84);
  flange(m,x,2.48,z,.31);
  // Protective jacket panels and attachment shoes.
  for(let i=0;i<8;i++){
    const a=i*tau/8;
    const pt=(r,h)=>[x+r*Math.cos(a),h,z+r*Math.sin(a)];
    m.rod(pt(.81,.07),pt(.89,-.18),.089,metal.steel);
    m.rod(pt(.778,.44),pt(.778,1.55),.017,metal.titanium,6);
  }
  pressureVessel(m,.45,-.9,-.15,.40,1.9,metal.steel,state.soilCutaway);
  if(state.soilCutaway){
    for(let i=0;i<9;i++){
      const a=i*tau/9, root=[.45+.24*Math.cos(a),.27,-.9+.24*Math.sin(a)];
      m.rod(root,vadd(root,[0,1.15,0]),.044,metal.brass,8);
    }
    m.drum(.45,.27,-.9,.32,.08,metal.dark);
    m.drum(.45,1.42,-.9,.32,.08,metal.dark);
  }
  flange(m,.45,1.25,-.9,.46);
  for(const [height,mat] of [[1.98,metal.titanium],[.73,metal.copper]]){
    m.pipe([[x+.52,height,z],[x+.9,height,z],[.45,height,-.36],[.45,height-.32,-.68]],.13,mat);
  }
  // Shaft-line housings on a common skid; collars identify the casing breaks.
  const y=.42,axisZ=.81,left=.12,right=2.24;
  m.box(1.18,-.015,axisZ,2.45,.13,1.00,metal.dark);
  for(const px of [.46,1.78])m.box(px,.17,axisZ,.27,.38,.68,metal.steel);
  const spool=(a,b,r1,r2,mat)=>m.rod([a,y,axisZ],[b,y,axisZ],r1,mat,26,r2);
  spool(left,.68,.29,.50,metal.titanium);spool(.68,1.06,.50,.32,metal.titanium);
  spool(1.06,1.30,.26,.26,metal.dark);spool(1.30,right,.33,.33,metal.teal);
  for(const px of [.18,.48,.70,.95,1.34,2.20])spool(px,px+.045,px<1.06?.46:.36,px<1.06?.46:.36,metal.steel);
  for(let i=0;i<14;i++){
    const a=i*tau/14, yy=y+.34*Math.cos(a),zz=axisZ+.34*Math.sin(a);
    m.rod([1.44,yy,zz],[2.15,yy,zz],.026,metal.titanium,6);
  }
  m.pipe([[.45,.95,-.51],[.45,.95,.02],[.30,.95,.48],[.30,.66,.72]],.092,metal.titanium);
  heatExchangerBank(m,1.07,-1.04,-.15,5);
  m.pipe([[.85,.55,.47],[1.05,.55,.12],[1.05,-.05,-.57]],.075,metal.copper);
  m.pipe([[2.14,1.08,-.57],[2.37,1.08,-.27],[2.37,.20,.34],[2.13,.20,.60]],.067,metal.steel);
  serviceRail(m,[[-2.35,-.17,.43],[-2.35,-.17,1.44],[-1.36,-.17,1.44],[-.42,-.17,1.44]]);
  serviceCabinet(m,1.92,-.17,-.24,.75);
  m.feature([x,1.70,z],'Helium vessel','The removable head, circumferential flange and jacket surround the primary heat source.');
  m.feature([.45,1.35,-.9],'Intermediate exchanger','The paired transfer lines connect the primary vessel to an independent conversion loop.');
  m.feature([1.59,.66,.90],'Brayton power block','Turbomachinery and generator share a shaft-line skid. The fins, coupling guard and mounting feet show the separate serviceable housings.');
}
function dualFluidPlant(m){
  deck(m,0,0,-.16,4.85,3.35);
  // Retaining walls and a bearing slab support the receivers below the deck.
  m.box(1.48,-1.60,.48,1.43,.11,1.02,metal.concrete);
  m.box(1.48,-.91,-.01,1.43,1.35,.11,metal.concrete);
  m.box(.83,-.91,.47,.10,1.35,1.0,metal.concrete);
  const x=-.43,z=-.22;
  const start=state.soilCutaway?1.62:0,end=state.soilCutaway?tau-.22:tau;
  m.shell(x,z,[[.68,-.26],[.95,.04],[1.00,.25],[1.00,1.7],[.95,1.88],[.66,2.06],[.22,2.16]],metal.titanium,start,end,42);
  m.shell(x,z,[[.98,.22],[1.035,.22],[1.035,.32],[.98,.32]],metal.dark,start,end);
  m.shell(x,z,[[.97,1.65],[1.055,1.65],[1.055,1.77],[.97,1.77]],metal.steel,start,end);
  if(state.soilCutaway){
    m.drum(x,.85,z,.58,1.73,metal.graphite);
    for(let j=0;j<8;j++){
      const a=j*tau/8;
      const px=x+.56*Math.cos(a),pz=z+.56*Math.sin(a);
      m.rod([px,.14,pz],[px,1.63,pz],.083,state.leadDrainDone?metal.steel:metal.ceramic);
    }
  }
  for(const r of [.41,.32,.23])m.drum(x,2.16+(.41-r),z,r,.09,metal.dark);
  const supply=state.drainDrill==='blackout'?metal.red:metal.teal;
  for(let i=0;i<2;i++){
    const px=1.30+i*.54;
    pressureVessel(m,px,.48,-1.61,.24,.92,metal.steel);
    m.pipe([[x+.38,-.16,z+.18],[x+.38,-.54,.25],[px,-.74,.48],[px,-.87,.48]],.082,state.leadDrainDone?metal.brass:metal.titanium);
  }
  pressureVessel(m,1.26,-.65,-.04,.39,1.94,metal.graphite);
  flange(m,1.26,1.40,-.65,.46);
  m.pipe([[x+.47,1.91,z],[.44,1.91,z],[.64,1.59,-.13],[1.26,1.59,-.31]],.13,metal.titanium);
  m.pipe([[1.26,.38,-.34],[1.26,.38,.24],[.73,.38,.48],[x+.64,.38,.35]],.12,metal.copper);
  heatExchangerBank(m,-1.65,-1.15,-.04,5);
  m.pipe([[-1.58,1.16,-.68],[-1.94,1.16,-.57],[-1.94,.46,-.22],[-1.31,.46,-.22]],.067,metal.copper);
  serviceCabinet(m,1.65,-.04,1.04,1);
  m.box(1.65,.51,1.295,.29,.056,.04,supply);
  m.pipe([[1.64,.10,1.16],[1.24,.10,1.16],[.52,.10,.74],[.35,.32,.60]],.049,supply);
  serviceRail(m,[[-2.13,-.05,.0],[-2.13,-.05,1.42],[-1.37,-.05,1.42]]);
  m.feature([x+.38,1.44,z+.54],'Two-fluid vessel','The section separates the inner channel bundle from the outer jacket. Stainless cladding covers the insulated exterior.');
  m.feature([1.26,1.42,-.65],'Heat exchanger','Insulated flow and return lines link the vessel and heat exchanger above the support deck.');
  if(state.soilCutaway)m.feature([1.56,-1.25,.48],'Drain receivers','Paired insulated receivers sit below the vessel. The standby drill changes the highlighted drain path.');
  else m.feature([1.65,.52,1.29],'Standby cabinet','A distinct service supply supports the freeze-protection scenario.');
}
function fusionStation(m){
  const y=.55,major=1.23, cut=state.soilCutaway;
  deck(m,0,0,-.26,4.95,4.05);
  const arc=(start,end,r,h,mat,tube)=>{
    m.surface(12,54,(u,v)=>{
      const a=start+(end-start)*u,b=v*tau;
      return radial(r+tube*Math.cos(b),h+tube*Math.sin(b),a);
    },mat);
  };
  arc(cut?1.64:0,cut?tau-.15:tau,major,y,metal.steel,.48);
  if(cut)arc(-.15,1.64,major,y,state.tritiumIgnited?metal.glass:metal.graphite,.27);
  m.drum(0,.70,0,.32,2.0,metal.dark);
  for(let k=0;k<9;k++)m.drum(0,.02+k*.18,0,.34,.082,metal.copper,28);
  // Extrude each D-shaped coil in its radial plane. Small axial bands show the winding pack.
  for(let i=0;i<14;i++){
    const a=i*tau/14,skip=cut&&i>0&&i<4;
    const profile=[[.53,-.71],[.90,-.77],[1.39,-.70],[1.83,-.46],[2.00,-.13],[2.04,.28],[1.89,.70],[1.55,.98],[1.12,1.08],[.65,.99],[.53,.86]];
    if(!skip){
      for(let j=0;j<profile.length;j++){
        const pt=(k,outer,offset)=>{
          const [r,h]=profile[k%profile.length],rr=1.22+(r-1.22)*outer;
          const v=radial(rr,y+h*outer,a);
          return [v[0]-offset*Math.sin(a),v[1],v[2]+offset*Math.cos(a)];
        };
        for(const [lo,hi,mat] of [[-.095,-.065,metal.steel],[-.065,.065,metal.brass],[.065,.095,metal.steel]]){
          m.face([pt(j,1.12,lo),pt(j+1,1.12,lo),pt(j+1,1.12,hi),pt(j,1.12,hi)],mat);
          m.face([pt(j,.91,hi),pt(j+1,.91,hi),pt(j+1,.91,lo),pt(j,.91,lo)],mat);
        }
        for(const side of [-.095,.095])m.face([pt(j,.91,side),pt(j+1,.91,side),pt(j+1,1.12,side),pt(j,1.12,side)],metal.titanium);
      }
    }
    if(i%2===0){const [x,,z]=radial(1.65,0,a);m.box(x,-.03,z,.32,.33,.34,metal.dark,a)}
  }
  for(const h of [-.11,1.53])arc(cut?1.62:0,cut?tau-.16:tau,1.74,h,metal.copper,.073);
  const a=.56,port=radial(2.40,.54,a);
  m.rod(radial(1.63,.54,a),port,.196,metal.titanium,24);
  m.rod(port,radial(2.48,.54,a),.24,metal.dark,24);
  m.rod(radial(2.48,.54,a),radial(2.52,.54,a),.194,metal.steel,24);
  const tip=radial(2.53,.54,a);
  for(let j=0;j<8;j++){
    const b=j*tau/8, shift=[-.207*Math.cos(b)*Math.sin(a),.207*Math.sin(b),.207*Math.cos(b)*Math.cos(a)];
    m.rod(vadd(port,shift),vadd(tip,shift),.025,metal.bright,6);
  }
  for(const i of [0,3,6,9,12]){
    const b=i*tau/14+.16;
    m.pipe([radial(1.85,.19,b),radial(2.12,.19,b),radial(2.12,-.12,b),radial(1.94,-.12,b+.2)],.041,metal.teal);
  }
  heatExchangerBank(m,-1.92,-1.53,-.16,4);
  m.pipe([[-1.23,.54,-.22],[-2.19,.54,-.22],[-2.19,1.09,-.92],[-1.91,1.09,-1.05]],.083,metal.steel);
  serviceCabinet(m,-1.72,-.16,1.12,.83);
  m.feature(radial(1.7,1.44,2.1),'Field coils','D-shaped toroidal-field coils wrap the vacuum vessel. Curved casings, winding packs and support shoes are visible around the ring.');
  m.feature(radial(1.24,.71,cut?.85:2.4),'Vacuum vessel','The ring chamber sits inside the magnet assembly. Section view removes a sector of the casing and coils to expose the chamber region.');
  m.feature(port,'Service port','The reinforced port provides a maintenance and diagnostic interface through the vessel shell.');
}

const deviceBuilders={p1:heatPipePlant,p2:braytonPlant,dfr:dualFluidPlant,fusion:fusionStation};
let lastDeviceMesh;

function deviceMesh(){
  const key=[state.phase,state.soilCutaway,state.umbrellaMode,state.dustTau>2,state.drainDrill,state.tritiumIgnited].join('/');
  if(lastDeviceMesh?.key===key)return lastDeviceMesh;
  const model=new DeviceMesh();
  sampleGround(model,state.soilCutaway);
  deviceBuilders[state.phase](model);
  model.visibility=deviceVisibility(model.vertices,model.indices);
  model.key=key;
  lastDeviceMesh=model;
  return model;
}

function drawDeviceScene(vp,scale=1){
  const model=deviceMesh(),ctx=vp.ctx,w=vp.w,h=vp.h;
  const ambient=ctx.createRadialGradient(w*.47,h*.39,0,w*.49,h*.47,Math.max(h*.85,w*.58));
  ambient.addColorStop(0,'#3c4140');ambient.addColorStop(.57,'#232d31');ambient.addColorStop(1,'#121b20');
  ctx.fillStyle=ambient;ctx.fillRect(0,0,w,h);
  const plate=renderMeshPlate(vp,model,scale),cw=vp.deviceFrame.width;
  ctx.save();
  ctx.translate(w*.5,h*.81);ctx.scale(1,.17);
  const soft=ctx.createRadialGradient(0,0,0,0,0,h*.45);
  soft.addColorStop(0,'rgba(0,0,0,.52)');soft.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=soft;ctx.fillRect(-h*.45,-h*.45,h*.9,h*.9);
  ctx.restore();
  ctx.drawImage(plate,(w-cw)/2,0,cw,h);
  if(state.deviceLabels)for(const part of model.parts)pin(vp,vmul(part.point,scale),part.title,'#dbc29a',part.body);
}
