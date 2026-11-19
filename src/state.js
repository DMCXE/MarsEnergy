const $ = id => document.getElementById(id);
const state = {
  phase:'p1', site:'gale', build:'early', viewMode:'synoptic', tab:'loads',
  soilCutaway:true, deviceLabels:false, subsurfaceOn:true, terrainMode:'oblique', terrainFocus:'ref', umbrellaMode:false, leadDrainDone:false, drainDrill:'normal',
  tritiumIgnited:true, crisis:'none', dustTau:0.6, windMs:4.6, shed:false,
  activeUnits:null, b1Off:false, b2Mode:'normal', cOff:false, powerOutage48h:false, preset:'default',
  continuumScale:55, time:0, progress:0, playing:false, direction:'in', cargoMode:'helio'
};

const power = k => k>=1000 ? (k/1000).toLocaleString('en-US',{maximumFractionDigits:3})+' MWe' : k.toLocaleString('en-US')+' kWe';
function unitCount(){
  if(state.phase==='p1'){
    if(state.build==='early'&&state.activeUnits!==null)return state.activeUnits;
    return state.build==='early'?5:25;
  }
  return 1;
}
function capacity(){return PHASES[state.phase].kw*unitCount()}
function backupSupply(){return state.powerOutage48h&&state.phase==='p1'&&state.build==='early'?75:0}
function zoneNominal(z){return state.phase==='p1'&&state.build==='early'?z.early:z.alpha*capacity()/1000}
function demand(z){
  if(z.key==='D'&&state.shed)return 0;
  if(state.phase==='p1'&&state.build==='early'){
    if(z.key==='B1'&&state.b1Off)return 0;
    if(z.key==='B2')return state.b2Mode==='save'?15:(state.b2Mode==='off'?0:z.early);
    if(z.key==='C'&&state.cOff)return 0;
    return z.early;
  }
  return z.alpha*capacity()/1000;
}
function heat(p){
  const input=p.kw/p.efficiency, waste=input-p.kw;
  const flux=.9*5.670374419e-8*(p.cold**4-210**4);
  return {input,waste,area:waste*1000/flux};
}
function fmt(n,d=0){return n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d})}
function inspect(info){
  if(info.terrainKey){state.terrainFocus=info.terrainKey;refreshTerrainReadout()}
  state.selectedHotspot=info;
  $('inspectorTitle').textContent=info.title;
  $('inspectorBody').textContent=info.body;
  $('inspectSite').textContent=info.detail||'';
}
function pin(vp,pt,title,color,body,detail=''){
  vp.addPin(...pt,title,color,{id:title,title,body,detail});
}
