// Device meshes use a local display coordinate system. Dimensions are illustrative.
const tau = Math.PI * 2;
const metal = {
  titanium: [173,183,184,.84], steel: [100,114,121,.88], bright: [208,216,209,.93],
  dark: [53,63,69,.72], graphite: [43,53,59,.28], ceramic: [216,205,179,.25],
  brass: [198,143,78,.74], copper: [169,102,69,.75], teal: [64,119,121,.52],
  red: [163,77,51,.4], rock: [134,88,66,.03], strata: [101,72,61,.02],
  ground: [158,108,79,.05], concrete: [128,127,115,.14], glass: [92,143,145,.72]
};
const vadd=(a,b)=>a.map((x,i)=>x+b[i]);
const vsub=(a,b)=>a.map((x,i)=>x-b[i]);
const vmul=(a,s)=>a.map(x=>x*s);
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const normal=a=>vmul(a,1/(Math.hypot(...a)||1));
const mixPoint=(a,b,t)=>a.map((x,i)=>x+(b[i]-x)*t);
const radial=(r,y,a)=>[r*Math.cos(a),y,r*Math.sin(a)];

class DeviceMesh {
  constructor(){this.vertices=[];this.indices=[];this.parts=[]}
  vertex(p,n,material){
    this.vertices.push([...p,...n,...material]);
    return this.vertices.length-1;
  }
  face(points,material){
    const n=normal(cross(vsub(points[1],points[0]),vsub(points[2],points[0])));
    const ids=points.map(p=>this.vertex(p,n,material));
    for(let i=1;i<ids.length-1;i++)this.indices.push(ids[0],ids[i],ids[i+1]);
  }
  surface(rows,cols,at,material){
    const first=this.vertices.length;
    for(let j=0;j<=rows;j++)for(let i=0;i<=cols;i++){
      const u=i/cols,v=j/rows;
      const du=vsub(at(u+.0001,v),at(u-.0001,v));
      const dv=vsub(at(u,Math.min(1,v+.0001)),at(u,Math.max(0,v-.0001)));
      this.vertex(at(u,v),normal(cross(dv,du)),material);
      if(i&&j){
        const d=first+j*(cols+1)+i,a=d-cols-2;
        this.indices.push(a,d-1,d,a,d,a+1);
      }
    }
  }
  box(x,y,z,w,h,d,mat,yaw=0){
    const c=Math.cos(yaw),s=Math.sin(yaw);
    const pts=[[-1,-1,-1],[1,-1,-1],[1,-1,1],[-1,-1,1],[-1,1,-1],[1,1,-1],[1,1,1],[-1,1,1]].map(([a,b,k])=>[x+(a*w*c-k*d*s)/2,y+b*h/2,z+(a*w*s+k*d*c)/2]);
    for(const side of [[0,1,2,3],[7,6,5,4],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]])this.face(side.map(i=>pts[i]),mat);
  }
  // A surface of revolution follows a radius/height profile from bottom to top.
  shell(x,z,profile,mat,start=0,end=tau,steps=32){
    for(let j=1;j<profile.length;j++){
      const [r0,y0]=profile[j-1], [r1,y1]=profile[j];
      this.surface(1,steps,(u,v)=>{
        const a=start+(end-start)*u,r=r0+(r1-r0)*v;
        return [x+r*Math.cos(a),y0+(y1-y0)*v,z+r*Math.sin(a)];
      },mat);
    }
  }
  drum(x,y,z,r,h,mat,steps=32){
    this.shell(x,z,[[.0001,y-h/2],[r,y-h/2],[r,y+h/2],[.0001,y+h/2]],mat,0,tau,steps);
  }
  rod(a,b,r,mat,steps=10,rEnd=r){
    const axis=normal(vsub(b,a));
    const e=normal(cross(Math.abs(axis[1])>.88?[1,0,0]:[0,1,0],axis)), f=cross(e,axis);
    const circle=(u,v,rr)=>vadd(mixPoint(a,b,v),vadd(vmul(e,rr*Math.cos(tau*u)),vmul(f,rr*Math.sin(tau*u))));
    this.surface(1,steps,(u,v)=>circle(u,v,r+(rEnd-r)*v),mat);
    for(const [v,rr] of [[0,r],[1,rEnd]]){
      const rim=Array.from({length:steps},(_,i)=>circle(i/steps,v,rr));
      this.face(v?rim.reverse():rim,mat);
    }
  }
  pipe(pts,r,mat){
    // Round each elbow and transport the cross-section along its centreline.
    const p=[pts[0]];
    for(let i=1;i<pts.length-1;i++){
      const a=pts[i-1],b=pts[i],c=pts[i+1];
      const radius=Math.min(r*2.8,Math.hypot(...vsub(a,b))*.34,Math.hypot(...vsub(c,b))*.34);
      const enter=vadd(b,vmul(normal(vsub(a,b)),radius)),exit=vadd(b,vmul(normal(vsub(c,b)),radius));
      for(let j=0;j<=4;j++){const t=j/4;p.push(mixPoint(mixPoint(enter,b,t),mixPoint(b,exit,t),t))}
    }
    p.push(pts.at(-1));let prevSide;
    const rings=p.map((pt,i)=>{
      const tangent=normal(vsub(p[Math.min(i+1,p.length-1)],p[Math.max(i-1,0)]));
      let side=prevSide?vsub(prevSide,vmul(tangent,dot(prevSide,tangent))):cross(tangent,Math.abs(tangent[1])>.85?[1,0,0]:[0,1,0]);
      side=normal(side);prevSide=side;
      const up=cross(side,tangent);
      return Array.from({length:10},(_,j)=>{
        const n=vadd(vmul(side,Math.cos(j*tau/10)),vmul(up,Math.sin(j*tau/10)));
        return this.vertex(vadd(pt,vmul(n,r)),n,mat);
      });
    });
    for(let i=1;i<rings.length;i++)for(let j=0;j<10;j++){
      const k=(j+1)%10,a=rings[i-1],b=rings[i];this.indices.push(a[j],b[j],b[k],a[j],b[k],a[k]);
    }
  }
  feature(point,title,body){this.parts.push({point,title,body})}
}

function flange(m,x,y,z,r){
  m.drum(x,y,z,r,.10,metal.steel);
  m.drum(x,y+.05,z,r*.96,.035,metal.bright);
  for(let j=0;j<10;j++){
    const a=j*tau/10;
    m.drum(x+r*.84*Math.cos(a),y+.085,z+r*.84*Math.sin(a),Math.max(.023,r*.047),.045,metal.dark,6);
  }
}
function pressureVessel(m,x,z,y,r,h,mat,section=false){
  const start=section?1.63:0,end=section?tau-.14:tau;
  m.shell(x,z,[[.001,y],[r*.69,y+.06*h],[r*.94,y+.12*h],[r,y+.19*h],[r,y+.78*h],[r*.96,y+.85*h],[r*.77,y+.92*h],[r*.45,y+.98*h],[.001,y+h]],mat,start,end,40);
  for(const f of [.23,.7]){
    const yy=y+h*f;
    m.shell(x,z,[[r,yy-.025],[r+.024,yy-.025],[r+.024,yy+.025],[r,yy+.025]],metal.steel,start,end);
  }
}
function serviceCabinet(m,x,y,z,s=1){
  m.box(x,y+.31*s,z,.66*s,.62*s,.46*s,metal.ceramic);
  m.box(x,y+.31*s,z+.24*s,.58*s,.52*s,.025*s,metal.steel);
  for(let j=0;j<5;j++)m.box(x,y+(.19+j*.047)*s,z+.26*s,.41*s,.019*s,.018*s,metal.dark);
  m.box(x+.15*s,y+.51*s,z+.258*s,.10*s,.044*s,.02*s,metal.teal);
}
function deck(m,x,z,y,w,d){
  m.box(x,y,z,w,.13,d,metal.dark);
  m.box(x,y+.08,z,w-.07,.045,d-.07,metal.steel);
  for(const sx of [-1,1])for(const sz of [-1,1]){
    const px=x+sx*(w/2-.16),pz=z+sz*(d/2-.16);
    m.box(px,y-.22,pz,.16,.42,.18,metal.steel);
    m.box(px,y-.43,pz,.38,.07,.36,metal.dark);
  }
}
