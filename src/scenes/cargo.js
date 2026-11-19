const earthRadius=1,marsRadius=1.524,transferA=(earthRadius+marsRadius)/2;
const eccentricity=(marsRadius-earthRadius)/(marsRadius+earthRadius);
const transferDays=365.25*transferA**1.5/2;
const earthMotion=2*Math.PI/365.25,marsMotion=earthMotion/marsRadius**1.5;
function flight(fraction,returning){
  const start=returning?Math.PI:0;
  const mean=start+Math.PI*fraction;
  let E=mean;
  for(let i=0;i<6;i++)E-=(E-eccentricity*Math.sin(E)-mean)/(1-eccentricity*Math.cos(E));
  const days=fraction*transferDays;
  return {
    craft:[transferA*(Math.cos(E)-eccentricity),transferA*Math.sqrt(1-eccentricity**2)*Math.sin(E)],
    earth:(returning?2*Math.PI-earthMotion*transferDays:0)+earthMotion*days,
    mars:(returning?Math.PI:Math.PI-marsMotion*transferDays)+marsMotion*days
  };
}

const cargoLoad=()=>cargoLoads[state.phase==='p1'&&state.build==='alpha'?'alpha':state.phase];
const dayMs=86400000, j2000=Date.UTC(2000,0,1,12), synodic=tau/(earthMotion-marsMotion);
const rad=Math.PI/180, wrapAngle=x=>((x%tau)+tau)%tau;
const dateFormat=new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
const flightDate=t=>dateFormat.format(new Date(j2000+t*dayMs));
function launchWindow(){
  const ready=(Date.UTC(cargoLoad().ready,0,1)-j2000)/dayMs;
  // Find a circular-orbit phase alignment after the scenario's readiness date.
  const relative0=(-4.55343205-100.46457166)*rad, rate=earthMotion-marsMotion;
  function next(after,angle){return after+wrapAngle(relative0-rate*after-angle)/rate}
  const delivery=next(ready,Math.PI-marsMotion*transferDays)+Number($('cargoWindow').value)*synodic;
  return state.direction==='out'?next(delivery+transferDays,earthMotion*transferDays-Math.PI):delivery;
}
let launchEpoch=0;
function syncCargo(){
  const back=state.direction==='out', load=cargoLoad();
  $('cargoTitle').textContent=back?'Mars to Earth':'Earth to Mars';
  $('cargoPadLink').textContent='Inspect Zone D · '+SITES[state.site].name+' ↗';
  $('cargoLoadTitle').textContent=load.label+(back?' · return':'');
  $('manifest').replaceChildren(...load[state.direction].map(name=>{const li=document.createElement('li');li.textContent=name;return li}));
  launchEpoch=launchWindow();
  $('departPort').textContent=back?'Depart Mars':'Depart Earth';
  $('arrivalPort').textContent=back?'Encounter Earth':'Encounter Mars';
  $('departDate').textContent=flightDate(launchEpoch);$('arrivalDate').textContent=flightDate(launchEpoch+transferDays);
  $('windowNote').textContent='Illustrative UTC dates. Readiness starts in '+load.ready+'. A circular, coplanar Hohmann model uses J2000 mean longitudes and repeats every '+Math.round(synodic)+' days. Return departs at the first alignment after the selected delivery arrives. Operational dates need an ephemeris-based mission design.';
  $('cargoCaption').textContent=({helio:'Transfer orbit · heliocentric',vehicle:'Freighter · open payload deck',earth:'Earth · daylight atlas',mars:'Mars · surface transfer',both:'Transfer orbit / Mars surface link'})[state.cargoMode];
  syncFlight();
}
const planetMaps={}, globeCache=new Map();
function loadPlanet(name,src){
  const image=new Image();image.onload=()=>{
    const c=document.createElement('canvas');c.width=image.width;c.height=image.height;
    const ctx=c.getContext('2d');ctx.drawImage(image,0,0);
    planetMaps[name]=ctx.getImageData(0,0,c.width,c.height);
  };image.src=src;
}
function globeBitmap(name,size,lon,lat,light){
  const tex=planetMaps[name];if(!tex)return null;
  const key=[name,size,lon,lat,light.join(',')].join('/');
  if(globeCache.has(key))return globeCache.get(key);
  const c=document.createElement('canvas');c.width=c.height=size;
  const ctx=c.getContext('2d'), img=ctx.createImageData(size,size), out=img.data;
  const sl=Math.sin(lat),cl=Math.cos(lat),radius=size/2-1,blue=name==='earth';
  for(let j=0;j<size;j++)for(let i=0;i<size;i++){
    const x=(i+.5-size/2)/radius,y=(size/2-j-.5)/radius,r2=x*x+y*y;
    if(r2>=1)continue;
    const z=Math.sqrt(1-r2),phi=Math.asin(Math.max(-1,Math.min(1,y*cl+z*sl)));
    const lng=lon+Math.atan2(x,z*cl-y*sl);
    const tx=Math.floor(wrapAngle(lng+Math.PI)/tau*tex.width)%tex.width;
    const ty=Math.min(tex.height-1,Math.floor((.5-phi/Math.PI)*tex.height));
    const k=4*(j*size+i),a=4*(ty*tex.width+tx),inc=x*light[0]+y*light[1]+z*light[2];
    const diffuse=.21+.99*Math.sqrt(Math.max(0,inc)),rim=(1-z)**3*(.32+.68*Math.max(0,inc));
    out[k]=tex.data[a]*diffuse+rim*(blue?35:101);
    out[k+1]=tex.data[a+1]*diffuse+rim*(blue?116:54);
    out[k+2]=tex.data[a+2]*diffuse+rim*(blue?188:34);
    out[k+3]=Math.min(255,(1-Math.sqrt(r2))*radius*255);
  }
  ctx.putImageData(img,0,0);
  if(globeCache.size>=28)globeCache.delete(globeCache.keys().next().value);
  globeCache.set(key,c);return c;
}
function globeAt(vp,name,point,r,lon,lat,light){
  const p=vp.project(...point);if(!p)return null;
  const sr=r*p.scale,large=sr>42;
  // Quantize to keep the CPU renderer responsive during a camera turn.
  const step=large?.018:.12;
  lon=Math.round(lon/step)*step;lat=Math.round(lat/step)*step;
  const size=large?Math.min(420,Math.max(128,Math.ceil(sr*2/24)*24)):72;
  const img=globeBitmap(name,size,lon,lat,light);
  if(img)vp.prims.push({type:'image',img,sx:p.sx,sy:p.sy,w:sr*2,h:sr*2,z:p.z-.02});
  else vp.addSphere(...point,r,name==='earth'?'#598cb1':'#bd7958');
  return {...p,r:sr,lon,lat};
}
function globeSurface(g,lon,lat){
  const d=lon-g.lon,cl=Math.cos(lat);
  return {x:g.sx+g.r*cl*Math.sin(d),y:g.sy-g.r*(Math.sin(lat)*Math.cos(g.lat)-cl*Math.cos(d)*Math.sin(g.lat)),
    visible:Math.sin(lat)*Math.sin(g.lat)+cl*Math.cos(d)*Math.cos(g.lat)>0};
}
function screenPin(vp,x,y,z,title,color,body,detail=''){
  vp.labels.push({sx:x,sy:y,z,title,color,data:{id:'cargo-'+title,title,body,detail}});
}
const atlasLight=normal([-.58,.42,.75]);
function drawGlobe(vp,cx,R,name='mars'){
  const site=SITES[state.site],mars=name==='mars',back=state.direction==='out';
  const lon=(mars?site.lon-14:10)*rad+vp.yaw+.25;
  const lat=Math.max(-1.49,Math.min(1.49,(mars?site.lat+8:19)*rad+vp.pitch+.64));
  const g=globeAt(vp,name,[cx,0,0],R,lon,lat,atlasLight);if(!g)return;
  if(!mars){
    screenPin(vp,g.sx-g.r*.55,g.sy-g.r*.58,g.z,'Earth', '#a3daf0',back?'End of the heliocentric return leg. Recovery would require a separate mission.':'Departure planet. The route begins after departure from Earth vicinity.');
    return;
  }
  // Local map +x east, -z north. Convert the planning offset to a planetary coordinate.
  const padLat=site.lat*rad-padZone.z*metresPerUnit/3389500;
  const padLon=site.lon*rad+padZone.x*metresPerUnit/(3389500*Math.cos(site.lat*rad));
  const pad=globeSurface(g,padLon,padLat);
  if(!pad.visible)return;
  const dx=g.r*.72,dy=-g.r*.99,ox=g.sx+dx,oy=g.sy+dy;
  const arc=Array.from({length:25},(_,i)=>{
    const t=i/24;return {sx:ox+(pad.x-ox)*t+.26*g.r*Math.sin(t*Math.PI),sy:oy+(pad.y-oy)*t-.16*g.r*Math.sin(t*Math.PI)};
  });
  vp.prims.push({type:'tube',proj:back?arc.reverse():arc,widthPx:2,color:'#a9d9d9',dash:[4,4],z:g.z-.06});
  screenPin(vp,ox,oy,g.z-.08,'Staging orbit','#9ad8df','Concept orbital handoff for the separate surface leg.');
  screenPin(vp,pad.x,pad.y,g.z-.09,'D · Proposed pad','#ffd39a',(back?'Surface origin at ':'Surface delivery to ')+site.name+'. '+zoneDetails.D,distanceText(padZone,{x:0,z:0})+' of '+site.ref);
}
let freighterCache,shipIcon;
function freighter(cut){
  const key=cut?'bay/'+state.phase+'/'+state.direction:'external';
  if(freighterCache?.key===key)return freighterCache;
  const m=new DeviceMesh();cargoHull(m,cut);m.key=key;
  m.visibility=deviceVisibility(m.vertices,m.indices);
  return freighterCache=m;
}
function cargoShipIcon(){
  if(shipIcon)return shipIcon;
  const v=Object.create(Viewport3D.prototype);
  Object.assign(v,{canvas:{id:'shipIcon'},w:100,h:152,dpr:1.5,dist:8,yaw:-.30,pitch:-.08,fov:890});
  v.cy=Math.cos(v.yaw);v.sy=Math.sin(v.yaw);v.cp=Math.cos(v.pitch);v.sp=Math.sin(v.pitch);
  return shipIcon=renderMeshPlate(v,freighter(false),1,'shipPlate',[0,2.60,0]);
}
function cargoSky(vp){
  const {ctx,w,h}=vp,g=ctx.createRadialGradient(w*.46,h*.47,0,w*.48,h*.5,Math.max(w,h)*.65);
  g.addColorStop(0,'#213440');g.addColorStop(.63,'#101e2b');g.addColorStop(1,'#09131c');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  for(let i=1;i<100;i++){
    const fraction=v=>v-Math.floor(v);
    const x=fraction(Math.sin(i*19.813)*41574)*w,y=fraction(Math.sin(i*71.71)*61263)*h;
    ctx.fillStyle=i%6===0?'#80909a':'#4a5e70';ctx.fillRect(x,y,i%6===0?1.35:.9,1);
  }
}
function drawCargoMacroScene(vp,mode=state.cargoMode){
  cargoSky(vp);
  if(mode==='earth'||mode==='mars'){drawGlobe(vp,0,3.65,mode);return}
  if(mode==='vehicle'){
    const model=freighter(true),origin=[0,2.62,0],scale=1.30;
    const plate=renderMeshPlate(vp,model,scale,'vehicleFrame',origin),w=vp.vehicleFrame.width;
    vp.ctx.drawImage(plate,(vp.w-w)/2,0,w,vp.h);
    for(const [y,title,body] of [[3.03,'Payload deck',cargoLoad()[state.direction].join(' · ')],[.83,'Aft flap','Movable external surface on the concept lander.']]){
      pin(vp,vmul(vsub([y>1?-.36:.79,y,-.29],origin),scale),title,'#f0c294',body);
    }
    return;
  }
  const dual=mode==='both',cx=dual?-2:0,size=dual?1.46:2.56;
  const pt=(x,z)=>[cx+x*size,0,z*size],polar=(r,a)=>pt(r*Math.cos(a),r*Math.sin(a));
  for(const r of [earthRadius,marsRadius])for(let i=0;i<104;i++){
    vp.addLine(polar(r,i*tau/104),polar(r,(i+1)*tau/104),r===1?'#507487':'#86634f',1.25);
  }
  const back=state.direction==='out',f=flight(state.progress,back),path=t=>pt(...flight(t,back).craft);
  // Split exactly at the spacecraft, even when the user scrubs between samples.
  function leg(a,b,color,dash){
    if(b-a<.00001)return;
    const n=Math.ceil(96*(b-a));vp.addTube(Array.from({length:n+1},(_,i)=>path(a+(b-a)*i/n)),dash?2.1:3.25,color,dash);
  }
  leg(0,state.progress,'#8de0d5');leg(state.progress,1,'#f1b473',[5,5]);
  const sun=vp.project(cx,0,0);
  if(sun)vp.prims.push({type:'sun',sx:sun.sx,sy:sun.sy,r:sun.scale*size*.117,z:sun.z});
  const ep=polar(1,f.earth),mp=polar(marsRadius,f.mars),ship=path(state.progress);
  function sunlight(angle){
    const x=-Math.cos(angle),z=-Math.sin(angle),depth=x*vp.sy+z*vp.cy;
    return [x*vp.cy-z*vp.sy,-depth*vp.sp,-depth*vp.cp].map(n=>Math.round(n*8)/8);
  }
  globeAt(vp,'earth',ep,.16*size,-.27,.26,sunlight(f.earth));
  globeAt(vp,'mars',mp,.122*size,SITES[state.site].lon*rad,.18,sunlight(f.mars));
  if(state.progress>.04&&!dual)pin(vp,path(0),'Departure','#97cdc8','The loaded vehicle left '+(back?'Mars':'Earth')+' at this point.',flightDate(launchEpoch));
  const end=path(1),endProj=vp.project(...end);
  if(endProj&&state.progress<.96){
    const sz=.057*size;
    for(let j=0;j<4;j++){
      const point=k=>[end[0]+sz*Math.cos(k*tau/4),end[1]+sz*Math.sin(k*tau/4),end[2]];
      vp.addLine(point(j),point(j+1),'#ffcd92',2);
    }
    pin(vp,end,'Encounter','#ffca93','The destination planet and freighter reach this point together at the end of the transfer.');
  }
  const sp=vp.project(...ship),a=vp.project(...path(Math.max(0,state.progress-.002))),b=vp.project(...path(Math.min(1,state.progress+.002)));
  if(sp&&a&&b){
    // Offset the enlarged ship symbol so the origin or destination stays visible at rendezvous.
    const h=Math.max(45,Math.min(95,sp.scale*1.4)),lift=h*.78;
    const above=sp.sy>lift+45,sy=sp.sy+(above?-lift:lift),sx=sp.sx;
    vp.prims.push({type:'line',a:sp,b:{sx,sy},color:'#a7ddd1',width:1,z:sp.z-.74});
    vp.prims.push({type:'image',img:cargoShipIcon(),sx,sy,w:h*100/152,h,angle:Math.atan2(b.sy-a.sy,b.sx-a.sx)+Math.PI/2,z:sp.z-.8});
    screenPin(vp,sx,sy,sp.z-.82,'Freighter','#98e1d2',cargoLoad()[state.direction].join(' · '));
    vp.prims.push({type:'sphere',sx:sp.sx,sy:sp.sy,sr:3,fill:'#95dfd2',z:sp.z-.85});

  }
  pin(vp,ep,'Earth','#91d6f6','Earth moves on a circular 1 AU reference orbit.');
  pin(vp,mp,'Mars','#ffae7d','Mars moves on a circular 1.524 AU reference orbit.',SITES[state.site].name+' · proposed surface pad');
  if(dual)drawGlobe(vp,2.83,1.20);
  const ctx=vp.ctx;ctx.font='11px ui-monospace, monospace';
  let x=15;
  for(const [text,color,dash] of [['Flown','#8de0d5',[]],['Ahead','#f1b473',[4,3]]]){
    ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash(dash);ctx.beginPath();ctx.moveTo(x,vp.h-18);ctx.lineTo(x+20,vp.h-18);ctx.stroke();ctx.fillStyle='#c5d3d9';ctx.fillText(text,x+26,vp.h-14);x+=77;
  }
  ctx.setLineDash([]);
}
