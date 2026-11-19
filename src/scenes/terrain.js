// Grids are north-to-south by row and west-to-east by column, sampled every 250 m.
const metresPerUnit=6000/9.2;
function elevation(x,z){
  const grid=DEM[state.site], n=grid.length-1;
  const u=Math.max(0,Math.min(n,(x+4.6)*n/9.2)), v=Math.max(0,Math.min(n,(z+4.6)*n/9.2));
  const i=Math.min(n-1,Math.floor(u)), j=Math.min(n-1,Math.floor(v));
  const fx=u-i, fz=v-j;
  return (1-fz)*(grid[j][i]*(1-fx)+grid[j][i+1]*fx)+fz*(grid[j+1][i]*(1-fx)+grid[j+1][i+1]*fx);
}
// Texture samples are north-up. Local map units run east (+x) and south (+z).
const groundY=(x,z)=>(elevation(x,z)-DEM[state.site][12][12])/metresPerUnit*SITES[state.site].exag;
const asScene=(x,z,h=0)=>[x,groundY(x,z)+h,-z];
const padZone=zones.find(z=>z.key==='D');
const zoneByKey=Object.fromEntries(zones.map(z=>[z.key,z]));
const baseMaterials={
  enamel:[211,207,188,.32], dark:[57,67,68,.52], amber:[223,155,71,.45],
  deck:[131,120,103,.16], steel:[147,162,163,.68], photovoltaic:[53,82,102,.62],
  glass:[104,149,147,.55], white:[225,224,204,.28], service:[80,154,149,.48]
};
const zoneDetails={
  A:'Crew pressure modules share a transfer tunnel and a protected utilities entry.',
  B1:'The assay laboratory has a sample airlock, an instrument mast and an external equipment bay.',
  B2:'Two ribbed growing halls connect to a shared climate-control and service module.',
  C:'Storage tanks, a pump skid and a sampling station form the proposed water pilot.',
  D:'A Starship-like cargo lander stands beside a lattice service tower. Its two cantilevered handling arms flank the hull. Cargo racks and a rover connect the apron to the access road. This Mars terminal is a concept.',
  E:'The generating yard includes a distribution bay and an auxiliary photovoltaic field.'
};
const surfaceTextures={};
function decodeSurfaceTexture(site,source){
  const img=new Image();
  img.onload=()=>{
    const c=document.createElement('canvas');c.width=img.width;c.height=img.height;
    const ctx=c.getContext('2d');ctx.drawImage(img,0,0);
    const rgba=ctx.getImageData(0,0,c.width,c.height).data;
    const samples=new Uint8Array(c.width*c.height),hist=new Uint32Array(256);
    for(let i=0;i<samples.length;i++){samples[i]=rgba[i*4];hist[samples[i]]++}
    function percentile(f){
      let count=0;
      for(let i=0;i<256;i++){count+=hist[i];if(count>=samples.length*f)return i}
      return 255;
    }
    const low=percentile(.02),span=Math.max(1,percentile(.98)-low);
    const lut=Array.from({length:256},(_,i)=>.62+.55*Math.min(1,Math.max(0,(i-low)/span)));
    surfaceTextures[site]={samples,width:c.width,height:c.height,lut};
  };
  img.src=source;
}
function terrainOffsets(x,z){
  const east=x*metresPerUnit/1000,north=-z*metresPerUnit/1000;
  const bearing=(Math.atan2(east,north)*180/Math.PI+360)%360;
  const dir=['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'][Math.round(bearing/22.5)%16];
  return {km:Math.hypot(east,north),bearing,dir};
}
function distanceText(a,b){
  const d=terrainOffsets(a.x-b.x,a.z-b.z);
  return d.km.toFixed(2)+' km '+d.dir;
}
function terrainOrigin(vp){
  if(vp===views.terrain&&state.terrainMode==='detail'){
    const z=zoneByKey[state.terrainFocus]||{x:0,z:0};
    return asScene(z.x,z.z,z.key==='D'?.62:.16);
  }
  return [0,0,0];
}
function moduleBarrel(m,x,y,z,length,radius,finish){
  const a=[x-length/2,y+radius,z], b=[x+length/2,y+radius,z];
  m.rod(a,b,radius,finish,18);
  for(const end of [-1,1]){
    const ex=x+end*length/2;
    m.rod([ex,y+radius,z],[ex+end*.08,y+radius,z],radius,baseMaterials.enamel,18,radius*.66);
  }
  for(let j=1;j<5;j++){
    const px=x-length/2+j*length/5;
    m.rod([px-.012,y+radius,z],[px+.012,y+radius,z],radius*1.035,baseMaterials.steel,16);
  }
}
function habitatYard(m){
  moduleBarrel(m,0,.06,-.17,.73,.18,baseMaterials.enamel);
  moduleBarrel(m,.05,.06,.21,.62,.17,baseMaterials.enamel);
  m.rod([-.18,.18,-.1],[-.18,.18,.19],.073,baseMaterials.dark);
  m.box(.49,.12,-.17,.18,.20,.22,baseMaterials.steel);
  for(const k of [-1,0,1])m.box(k*.17,.22,.381,.055,.055,.026,baseMaterials.dark);
}
function scienceYard(m){
  m.box(0,.075,0,.81,.14,.51,baseMaterials.deck);
  m.box(-.11,.25,0,.52,.29,.40,baseMaterials.enamel);
  m.box(-.11,.414,0,.57,.04,.43,baseMaterials.steel);
  m.box(.23,.19,.01,.18,.22,.25,baseMaterials.dark);
  m.rod([-.33,.42,-.15],[-.33,.91,-.15],.018,baseMaterials.steel);
  m.rod([-.45,.82,-.15],[-.21,.82,-.15],.014,baseMaterials.amber);
  for(const dx of [-.26,-.10,.06])m.box(dx,.29,.202,.094,.078,.018,baseMaterials.glass);
}
function farmYard(m){
  for(const z of [-.20,.20]){
    const p=(x,a)=>[x,.09+.28*Math.sin(a),z+.16*Math.cos(a)];
    m.surface(1,18,(u,v)=>p((v-.5)*.79,u*Math.PI),baseMaterials.glass);
    for(const x of [-.39,-.23,-.07,.09,.25,.39]){
      const arc=Array.from({length:9},(_,i)=>p(x,i*Math.PI/8));
      for(let i=1;i<arc.length;i++)m.rod(arc[i-1],arc[i],.013,baseMaterials.enamel,5);
    }
    for(const x of [-.395,.395])m.face(Array.from({length:13},(_,i)=>p(x,i*Math.PI/12)),baseMaterials.steel);
  }
  m.box(.46,.12,0,.13,.21,.73,baseMaterials.enamel);
}
function waterYard(m){
  for(const x of [-.23,.14]){
    pressureVessel(m,x,-.05,.04,.148,.46,baseMaterials.steel);
    m.drum(x,.22,-.05,.155,.034,baseMaterials.service,16);
    m.pipe([[x,.12,.04],[x,.12,.23],[.36,.12,.23],[.36,.12,.09]],.024,baseMaterials.service);
  }
  m.box(.35,.125,0,.19,.18,.29,baseMaterials.enamel);
  m.rod([-.32,.04,.28],[-.32,.48,.28],.022,baseMaterials.amber);
}

function powerYard(m){
  const count=unitCount(),cols=Math.ceil(Math.sqrt(count)),rows=Math.ceil(count/cols);
  const step=count>5?.21:.29;
  for(let i=0;i<count;i++){
    const x=(i%cols-(cols-1)/2)*step, z=(Math.floor(i/cols)-(rows-1)/2)*step;
    if(count>1){
      m.drum(x,.17,z,.063,.29,baseMaterials.enamel,8);
      for(const rot of [0,Math.PI/2])m.box(x,.30,z,step*.88,.15,.023,baseMaterials.dark,rot);
    }else if(state.phase==='fusion'){
      m.drum(x,.10,z,.42,.16,baseMaterials.deck);
      for(let k=0;k<14;k++){
        const a=k*tau/14,[px,,pz]=radial(.30,.24,a);
        m.box(px,.24,pz,.18,.26,.09,baseMaterials.steel,a);
      }
      m.drum(x,.27,z,.095,.33,baseMaterials.amber);
    }else{
      pressureVessel(m,-.16,0,.02,.215,.65,baseMaterials.enamel);
      m.box(.23,.18,.02,.29,.30,.49,baseMaterials.steel);
      m.pipe([[-.15,.50,0],[.12,.50,0],[.23,.30,0]],.059,baseMaterials.steel);
    }
  }
  for(let i=0;i<3;i++){
    const z=-.78,x=(i-1)*.32;
    m.rod([x,.01,z],[x,.14,z],.029,baseMaterials.steel);
    const p=(dx,dz)=>[x+dx,.16+dz*.36,z+dz];
    m.face([p(-.147,-.19),p(.147,-.19),p(.147,.19),p(-.147,.19)],baseMaterials.photovoltaic);
    for(const j of [-.09,0,.09])m.rod(p(j,-.19),p(j,.19),.007,baseMaterials.steel,4);
  }
  m.box(.65,.14,.14,.20,.25,.29,baseMaterials.steel);
}
const yards={A:habitatYard,B1:scienceYard,B2:farmYard,C:waterYard,D:freightTerminal,E:powerYard};
function ribbon(m,points,width,mat,height=.035){
  for(let j=1;j<points.length;j++){
    const [ax,az]=points[j-1],[bx,bz]=points[j],dx=bx-ax,dz=bz-az,len=Math.hypot(dx,dz);
    if(!len)continue;
    const sx=-dz/len*width/2,sz=dx/len*width/2,n=Math.ceil(len/.14);
    for(let i=0;i<n;i++){
      const corner=(f,side)=>asScene(ax+f*dx+sx*side,az+f*dz+sz*side,height);
      m.face([corner(i/n,-1),corner(i/n,1),corner((i+1)/n,1),corner((i+1)/n,-1)],mat);
    }
  }
}
// Draw a shallow level service apron with side faces down to the sampled ground.
function serviceApron(m,z){
  const size={A:[.62,.46],B1:[.48,.33],B2:[.58,.45],C:[.51,.40],D:[.77,.90],E:[.80,.99]}[z.key];
  const [w,d]=size;
  const outline=[[-w+.13,-d],[w-.13,-d],[w,-d+.13],[w,d-.13],[w-.13,d],[-w+.13,d],[-w,d-.13],[-w,-d+.13]];
  const base=outline.map(([dx,dz])=>asScene(z.x+dx,z.z+dz,-.014));
  const height=Math.max(groundY(z.x,z.z),...base.map(p=>p[1]))+.022;
  const top=base.map(p=>[p[0],height,p[2]]);
  m.face(top,[151,130,106,.08]);
  for(let i=0;i<8;i++){const j=(i+1)%8;m.face([base[i],base[j],top[j],top[i]],[117,98,81,.06])}
  return height;
}
let baseMeshCache;
function baseMesh(){
  const key=['terrain',state.site,state.phase,unitCount(),state.subsurfaceOn,!!surfaceTextures[state.site]].join('/');
  if(baseMeshCache?.key===key)return baseMeshCache;
  const m=new DeviceMesh(),n=DEM[state.site].length-1,span=9.2;
  const mat=[187,141,109,-1],indices=[];
  for(let j=0;j<=n;j++)for(let i=0;i<=n;i++){
    const x=-4.6+i*span/n,z=-4.6+j*span/n,d=.18;
    const norm=normal([groundY(x-d,z)-groundY(x+d,z),2*d,groundY(x,z+d)-groundY(x,z-d)]);
    indices.push(m.vertex(asScene(x,z),norm,mat));
    if(i&&j){const v=indices.length-1,k=v-n-2;m.indices.push(k,v-1,v,k,v,k+1)}
  }
  // Map edge represents the extent of the extract, with no implied subsurface geology.
  const bottom=Math.min(...m.vertices.map(p=>p[1]))-.14;
  for(let i=0;i<n;i++)for(const [a,b] of [[i,i+1],[n*(n+1)+i,n*(n+1)+i+1],[i*(n+1),(i+1)*(n+1)],[i*(n+1)+n,(i+1)*(n+1)+n]]){
    const p=m.vertices[a].slice(0,3),q=m.vertices[b].slice(0,3);
    m.face([p,q,[q[0],bottom,q[2]],[p[0],bottom,p[2]]],[109,82,69,.03]);
  }
  // Schematic access corridors meet a shared junction south of the survey marker.
  const lane=[143,122,101,.04],trace=[88,153,152,.42];
  const junction=[-.04,.48], fork=[-1.53,-.62];
  const road=[[2.35,-1],[1.63,-.78],[1.26,.05],junction,[-.70,.85]];
  ribbon(m,road,.075,lane);
  ribbon(m,[junction,[.40,.68],[.55,1.55]],.060,lane);
  ribbon(m,[junction,fork,[-2.30,-1.55],[-2.90,-2.05]],.06,lane);
  if(state.subsurfaceOn){
    const trunk=[[-2.90,-2.05],[-2.55,-1.86],[-1.42,-.72],[.06,.32]];
    ribbon(m,trunk,.031,trace,.065);
    for(const path of [[trunk[1],[-2.30,-1.55]],[trunk[3],[-.70,.85]],[trunk[3],[.40,.68],[.55,1.55]],[trunk[3],[1.35,-.02],[1.73,-.89],[2.35,-1]]])ribbon(m,path,.030,trace,.065);
  }
  for(const zone of zones){
    const baseHeight=serviceApron(m,zone),first=m.vertices.length;
    if(zone===padZone)m.padHeight=baseHeight;
    yards[zone.key](m);
    const size=.99;
    // Local foundations follow the mapped terrain. Symbols are deliberately enlarged.
    for(let i=first;i<m.vertices.length;i++){
      const p=m.vertices[i];
      p[0]=zone.x+p[0]*size;p[1]=baseHeight+p[1]*size;p[2]=-(zone.z+p[2]*size);p[5]*=-1;
    }
  }
  m.key=key;m.texture=surfaceTextures[state.site];m.visibility=deviceVisibility(m.vertices,m.indices);
  return baseMeshCache=m;
}
function terrainInfo(key){
  const site=SITES[state.site],centre={x:0,z:0},z=zoneByKey[key];
  if(!z)return {id:'terrain-ref',terrainKey:'ref',title:site.ref,body:site.kind+' · '+site.coord,
    detail:'Map origin · '+fmt(elevation(0,0))+' m relative to the Martian areoid.'};
  const assigned=z.key==='E'?power(capacity())+' installed':power(demand(z))+' assigned';
  const relation=z===padZone?'Habitat '+distanceText(zoneByKey.A,z)+' from pad.':'Pad separation '+terrainOffsets(z.x-padZone.x,z.z-padZone.z).km.toFixed(2)+' km.';
  return {id:'terrain-'+key,terrainKey:key,title:z.key+' · '+(z===padZone?'Proposed cargo pad':z.name),
    body:zoneDetails[key]+(key==='C'?' '+site.water:''),
    detail:distanceText(z,centre)+' of '+site.ref+' · '+relation+' '+assigned+' · '+fmt(elevation(z.x,z.z))+' m.'};
}
function refreshTerrainReadout(){
  const info=terrainInfo(state.terrainFocus),site=SITES[state.site];
  $('terrainSelect').options[0].text=site.ref;
  $('terrainSelect').value=state.terrainFocus;
  $('terrainDetail').textContent=info.body+' '+info.detail;
  $('terrainMeasure').textContent='Proposed pad · '+distanceText(padZone,{x:0,z:0})+' of '+site.ref;
  for(const b of document.querySelectorAll('[data-terrain-mode]'))b.setAttribute('aria-pressed',b.dataset.terrainMode===state.terrainMode);
}
function selectTerrain(key){
  state.terrainFocus=key;
  inspect(terrainInfo(key));
}
function drawMapHud(vp,project,focus){
  const ctx=vp.ctx,w=vp.w,h=vp.h;
  const mid=project(focus),north=project(vadd(focus,[0,0,.40]));
  if(mid&&north){
    const angle=Math.atan2(north.sy-mid.sy,north.sx-mid.sx);
    ctx.save();ctx.translate(w-28,31);ctx.rotate(angle+Math.PI/2);
    ctx.fillStyle='#f3e7d2';ctx.beginPath();ctx.moveTo(0,-10);ctx.lineTo(4,5);ctx.lineTo(0,2);ctx.lineTo(-4,5);ctx.closePath();ctx.fill();ctx.restore();
    ctx.fillStyle='#f4e3ca';ctx.font='bold 11px system-ui';ctx.textAlign='center';ctx.fillText('N',w-28+Math.cos(angle)*19,31+Math.sin(angle)*19);
  }
  const delta=vmul([vp.cy,0,-vp.sy],1000/metresPerUnit);
  const tip=project(vadd(focus,delta));
  if(mid&&tip){
    const px=Math.hypot(tip.sx-mid.sx,tip.sy-mid.sy);
    const unit=px>150?.25:px>90?.5:1,len=px*unit;
    ctx.save();ctx.font='11px ui-monospace, monospace';ctx.textAlign='left';
    ctx.fillStyle='rgba(13,24,29,.85)';ctx.fillRect(9,h-36,len+20,30);
    ctx.fillStyle='#f1e7d6';ctx.fillText(unit===1?'1 km':Math.round(unit*1000)+' m',17,h-20);
    ctx.strokeStyle='#e9ddc8';ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(17,h-17);ctx.lineTo(17,h-12);ctx.lineTo(17+len,h-12);ctx.lineTo(17+len,h-17);ctx.stroke();ctx.restore();
  }
  ctx.textAlign='left';
}
function drawTerrainBaseScene(vp,scale=1){
  const site=SITES[state.site],model=baseMesh(),focus=terrainOrigin(vp);
  const ctx=vp.ctx,w=vp.w,h=vp.h;
  const bg=ctx.createLinearGradient(0,0,0,h);bg.addColorStop(0,'#283236');bg.addColorStop(1,'#142025');
  ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  const plate=renderMeshPlate(vp,model,scale,'baseFrame',focus);
  const cw=vp.baseFrame.width;
  ctx.drawImage(plate,(w-cw)/2,0,cw,h);
  const world=p=>vmul(vsub(p,focus),scale),project=p=>vp.project(...world(p));
  const plot=(x,z,dy=0)=>world(asScene(x,z,dy));
  const centre=plot(0,0,.045),pad=plot(padZone.x,padZone.z,.13);
  // A dotted map measurement joins the reference and pad. Access roads are separate ground features.
  for(let i=0;i<20;i++){
    const f=i/20,t=(i+.48)/20;
    vp.addLine(plot(padZone.x*f,padZone.z*f,.095),plot(padZone.x*t,padZone.z*t,.095),'#39291b',3.5,null,.78,.005);
    vp.addLine(plot(padZone.x*f,padZone.z*f,.095),plot(padZone.x*t,padZone.z*t,.095),'#ffe4af',1.7);
  }
  const color=state.site==='gale'?'#b7edf0':'#ddd3b8';
  for(let i=0;i<36;i++){
    const a=tau*i/36,b=tau*(i+1)/36;
    vp.addLine(plot(.18*Math.cos(a),.18*Math.sin(a),.05),plot(.18*Math.cos(b),.18*Math.sin(b),.05),'#213036',4,null,1,.005);
    vp.addLine(plot(.18*Math.cos(a),.18*Math.sin(a),.05),plot(.18*Math.cos(b),.18*Math.sin(b),.05),color,2);
  }
  vp.addLine(plot(-.24,0,.06),plot(.24,0,.06),color,1.3);
  vp.addLine(plot(0,-.24,.06),plot(0,.24,.06),color,1.3);
  // Keep callouts for visible points only, especially in the facility close-up.
  function mark(point,label,tint,key){
    const p=vp.project(...point);
    if(p&&p.sx>4&&p.sy>4&&p.sx<w-4&&p.sy<h-4)vp.addPin(...point,label,tint,terrainInfo(key));
  }
  mark(centre,site.ref,color,'ref');
  for(const zone of zones){
    const primary=zone===padZone,selected=state.terrainFocus===zone.key;
    const expanded=vp.w>520&&state.viewMode==='terrain';
    mark(primary?pad:plot(zone.x,zone.z,.35),primary?'D · Proposed pad':(expanded||selected?zone.key+' · '+zone.name:zone.key),primary?'#ffc284':zone.color,zone.key);
  }
  if(vp===views.terrain&&state.terrainMode==='detail'&&state.terrainFocus==='D'){
    const at=(x,y,z)=>world([padZone.x+x*.99,model.padHeight+y*.99,-padZone.z-z*.99]);
    pin(vp,at(-.24,1.045,.16),'Chopstick arms','#efc486','Two braced handling arms extend from the carriage on the lattice tower.','Proposed Zone D ground equipment · enlarged symbol');
    pin(vp,at(.04,1.30,0),'Cargo lander','#b7dce1','Starship-like concept lander on the freight apron.','Proposed Zone D vehicle · enlarged symbol');
  }
  drawMapHud(vp,project,focus);
}
