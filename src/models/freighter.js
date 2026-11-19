// Concept cargo lander. The same outer mould line appears in flight and at Zone D.
function cargoHull(m, cut=false) {
  const rings=[[.38,.19],[.48,.28],[.51,.40],[.51,3.73],[.50,4.02],[.46,4.28],[.38,4.54],[.26,4.82],[.13,5.05],[.012,5.21]];
  const aperture=[3.32,5.99],alloy=[183,192,195,1.12];
  for(let i=1;i<rings.length;i++){
    const pair=[rings[i-1],rings[i]];
    const open=cut && i===3;
    if(open){
      m.shell(0,0,[[.51,.40],[.51,2.0]],alloy);
      m.shell(0,0,[[.51,2.0],[.51,3.73]],alloy,aperture[1],aperture[0]+tau);
    }else m.shell(0,0,pair,alloy);
    // Dark ceramic windward panels taper with the ogive.
    m.shell(0,0,pair.map(([r,h])=>[r+.006,h]),metal.graphite,-.23,1.52,18);
  }
  for(let j=0;j<17;j++){
    const y=.42+.196*j,sliced=cut&&y>2;
    m.shell(0,0,[[.512,y],[.514,y+.010]],j%4===0?metal.steel:metal.bright,sliced?aperture[1]:0,sliced?aperture[0]+tau:tau,32);
  }
  // Panel latches and rows of thermal tiles on the windward side.
  for(let j=0;j<13;j++){
    const y=.48+j*.245;
    for(let k=0;k<5;k++){
      const a=-.22+k*.342+(j%2)*.075;
      m.shell(0,0,[[.518,y],[.518,y+.212]],[44+(j+k)%4*3,52+(k%3)*2,57,.30],a,a+.30,3);
    }
  }
  for(const side of [-1,1])for(const nose of [false,true]){
    const outline=nose?[[.43,3.95],[.79,3.81],[.77,4.17],[.37,4.52]]:[[.45,.36],[.94,.20],[.91,.85],[.47,1.49]];
    const face=z=>outline.map(([x,y])=>[x*side,y,z]);
    const a=face(-.055),b=face(.055);m.face(a,metal.steel);m.face(b,metal.graphite);
    for(let j=0;j<4;j++)m.face([a[j],a[(j+1)%4],b[(j+1)%4],b[j]],metal.bright);
    m.rod(a[0],a[3],.034,metal.dark,8);
  }
  for(let j=0;j<3;j++){
    const [x,,z]=radial(.235,0,j*tau/3);
    m.shell(x,z,[[.137,.07],[.144,.09],[.079,.31],[.077,.36]],metal.dark,0,tau,16);
    m.shell(x,z,[[.139,.07],[.144,.10]],metal.copper,0,tau,16);
  }
  if(!cut){
    m.box(0,2.87,-.509,.36,.81,.023,metal.steel);
    m.box(0,2.87,-.525,.31,.74,.017,metal.titanium);
    for(const y of [2.63,3.11])m.box(.17,y,-.532,.04,.07,.035,metal.bright);
    return;
  }
  // Open payload deck, tie-down frames and return canisters.
  for(const x of [-.36,.36]){
    m.rod([x,2,.17],[x,3.67,.17],.032,metal.bright,6);
    for(const y of [2.20,2.99])m.rod([x,y,-.18],[x,y,.22],.018,metal.steel,6);
  }
  for(const y of [2.01,2.82,3.66]){
    m.drum(0,y,0,.505,.045,metal.brass);
    for(const x of [-.34,.34])m.rod([x,y,-.27],[x,y+.17,-.27],.019,metal.bright,6);
  }
  for(const y of [2.36,3.14]){
    m.box(0,y-.265,-.025,.60,.074,.49,metal.steel);
    if(state.direction==='out'){
      for(const x of [-.18,.18]){
        m.drum(x,y,-.10,.135,.47,metal.bright,16);
        for(const d of [-.17,.16])m.drum(x,y+d,-.1,.139,.036,metal.teal,16);
      }
    }else if(state.phase==='fusion'){
      for(const d of [-.14,0,.14])m.shell(0,0,[[.18,y+d],[.34,y+d],[.34,y+d+.07],[.18,y+d+.07]],metal.copper);
    }else if(state.phase==='p2'){
      m.rod([-.28,y,-.06],[.28,y,-.06],.19,metal.titanium,18);
      for(const x of [-.21,-.12,.12,.21])m.rod([x,y,-.06],[x+.035,y,-.06],.215,metal.teal,16);
    }else{
      m.box(0,y,-.07,.60,.45,.48,state.phase==='dfr'?metal.steel:metal.ceramic);
      for(const x of [-.23,.23])m.box(x,y,-.07,.038,.47,.49,metal.brass);
      m.box(0,y+.05,-.316,.21,.07,.012,metal.dark);
      for(const x of [-.23,.23])for(const d of [-.14,.14])m.box(x,y+d,-.320,.065,.041,.026,metal.bright);
      if(state.phase==='dfr')for(let j=0;j<5;j++)m.box(-.14+j*.07,y-.07,-.321,.021,.15,.023,metal.titanium);
    }
  }
}
