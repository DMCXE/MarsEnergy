function freightTower(m){
  const cx=-.39,cz=.04,w=.20,d=.28,top=1.65;
  m.box(cx,.075,cz,.34,.15,.43,baseMaterials.deck);
  const corners=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([x,z])=>[cx+x*w/2,cz+z*d/2]);
  for(const [x,z] of corners)m.box(x,top/2,z,.032,top,.032,metal.bright);
  for(let j=0;j<6;j++){
    const low=.13+j*.24,high=low+.24;
    for(let k=0;k<4;k++){
      const [x,z]=corners[k],[xx,zz]=corners[(k+1)%4];
      m.rod([x,low,z],[xx,high,zz],.011,baseMaterials.steel,4);
      m.rod([xx,low,zz],[x,high,z],.011,baseMaterials.steel,4);
    }
    m.box(cx,high,cz,w+.045,.025,d+.045,metal.dark);
  }
  m.box(cx,top,cz,.28,.065,.38,baseMaterials.amber);
  m.box(cx+.125,.99,cz,.075,.32,.35,metal.graphite);
  for(const side of [-1,1]){
    const root=[cx+.14,1.045,cz+side*.135],tip=[.17,1.045,side*.171];
    m.rod(root,tip,.026,baseMaterials.amber,5,.017);
    m.rod([root[0],.928,root[2]],tip,.020,baseMaterials.steel,5,.012);
    m.box(.12,1.065,side*.163,.14,.033,.032,metal.dark);
  }
  const first=m.vertices.length;cargoHull(m);
  for(let i=first;i<m.vertices.length;i++){
    const v=m.vertices[i];v[0]=.034+v[0]*.247;v[1]=.107+v[1]*.247;v[2]=v[2]*.247;
  }
}

function freightTerminal(m){
  m.drum(0,.05,0,.53,.10,baseMaterials.deck,8);
  const points=r=>Array.from({length:8},(_,i)=>radial(r,.11,(i+.5)*tau/8));
  const outer=points(.49), inner=points(.455);
  for(let i=0;i<8;i++)m.face([outer[i],inner[i],inner[(i+1)%8],outer[(i+1)%8]],baseMaterials.amber);
  // Four registration corners make a landing target readable from orbit and ground.
  for(const dx of [-1,1])for(const dz of [-1,1]){
    m.box(dx*.16,.114,dz*.19,.088,.012,.023,baseMaterials.white);
    m.box(dx*.195,.114,dz*.16,.023,.012,.085,baseMaterials.white);
  }
  freightTower(m);
  m.box(-.65,.12,-.20,.28,.13,.15,baseMaterials.enamel);
  for(const xx of [-.74,-.56])for(const zz of [-.29,-.11])
    m.rod([xx,.078,zz-.022],[xx,.078,zz+.022],.059,baseMaterials.dark,10);
  for(const dx of [-.22,.05,.32]){
    m.box(dx,.12,-.70,.22,.18,.27,baseMaterials.enamel);
    for(const side of [-.07,.07])m.box(dx+side,.12,-.70,.018,.19,.275,baseMaterials.amber);
  }
  for(const a of [.2,2.2,4.2]){
    const [x,,z]=radial(.57,0,a);m.rod([x,.05,z],[x,.22,z],.018,baseMaterials.steel);
    m.drum(x,.23,z,.032,.035,baseMaterials.amber,8);
  }
}
