const keyLight=normal([-.49,.82,.69]);
const lightRight=normal(cross([0,1,0],keyLight));
const lightUp=cross(keyLight,lightRight);

/* Orthographic shadow map, in model coordinates. The same map serves every orbit angle. */
function deviceVisibility(vertices,indices){
  const n=256, depth=new Float32Array(n*n).fill(-Infinity);
  const points=vertices.map(p=>[(dot(p,lightRight)*.12+.5)*n,(dot(p,lightUp)*.12+.5)*n,dot(p,keyLight)]);
  for(let i=0;i<indices.length;i+=3){
    const a=points[indices[i]],b=points[indices[i+1]],c=points[indices[i+2]];
    rasterTriangle(a,b,c,n,n,(k,u,v,w)=>{
      const z=u*a[2]+v*b[2]+w*c[2];if(z>depth[k])depth[k]=z;
    });
  }
  return points.map(([x,y,z])=>{
    let visible=0;
    for(const dx of [-1,1])for(const dy of [-1,1]){
      const k=(Math.floor(y)+dy)*n+Math.floor(x)+dx;
      if(depth[k]===undefined||depth[k]<z+.095)visible++;
    }
    return .53+.47*visible/4;
  });
}

function rasterTriangle(a,b,c,width,height,pixel){
  const dx=b[0]-a[0],dy=b[1]-a[1],ex=c[0]-a[0],ey=c[1]-a[1],det=dx*ey-dy*ex;
  if(Math.abs(det)<.001)return;
  const x0=Math.max(0,Math.ceil(Math.min(a[0],b[0],c[0])-.5));
  const x1=Math.min(width-1,Math.floor(Math.max(a[0],b[0],c[0])-.5));
  const y0=Math.max(0,Math.ceil(Math.min(a[1],b[1],c[1])-.5));
  const y1=Math.min(height-1,Math.floor(Math.max(a[1],b[1],c[1])-.5));
  const dv=ey/det,dw=-dy/det;
  for(let y=y0;y<=y1;y++){
    const yy=y+.5-a[1],xx=x0+.5-a[0];
    let v=(xx*ey-yy*ex)/det,w=(yy*dx-xx*dy)/det;
    for(let x=x0;x<=x1;x++,v+=dv,w+=dw){
      const u=1-v-w;
      if(u>=-.00001&&v>=-.00001&&w>=-.00001)pixel(y*width+x,u,v,w);
    }
  }
}

// Keep a depth-tested, shaded turntable image until the camera or assembly changes.
// This also keeps the offline renderer usable without a WebGL driver.
function renderMeshPlate(vp,model,scale,frameKey='deviceFrame',origin=[0,0,0]){
  const signature=[model.key,vp.yaw.toFixed(4),vp.pitch.toFixed(4),vp.dist.toFixed(3),vp.w,vp.h,vp.dpr,scale,...origin].join('/');
  if(vp[frameKey]?.signature===signature)return vp[frameKey].canvas;
  const resolution=Math.min(Math.max(1.5,vp.dpr),2,1180/Math.min(vp.w,vp.h));
  // The subject occupies the central square. Wide panels keep their original perspective.
  const canvas=vp[frameKey]?.canvas||document.createElement('canvas');
  const cw=frameKey==='baseFrame'?vp.w:Math.min(vp.w,Math.ceil(vp.h*1.95));
  const width=Math.round(cw*resolution),height=Math.round(vp.h*resolution);
  if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height}
  const ctx=canvas.getContext('2d'), bitmap=ctx.createImageData(width,height);
  const pixels=bitmap.data,depth=new Float32Array(width*height);
  const eye=[-vp.dist*vp.cp*vp.sy/scale,-vp.dist*vp.sp/scale,-vp.dist*vp.cp*vp.cy/scale];
  const focal=vp.fov*Math.min(vp.w,vp.h)/460*resolution;
  const tex=model.texture,plan=vp.canvas.id==='canvasTerrain'&&state.terrainMode==='plan';
  const projected=model.vertices.map((p,i)=>{
    const x=p[0]-origin[0],y=p[1]-origin[1],z=p[2]-origin[2],cam=vp.toCam(x*scale,y*scale,z*scale);
    const inv=1/Math.max(.001,cam.z),view=normal([eye[0]-x,eye[1]-y,eye[2]-z]);
    let nx=p[3],ny=p[4],nz=p[5];
    if(nx*view[0]+ny*view[1]+nz*view[2]<0){nx=-nx;ny=-ny;nz=-nz}
    const facing=Math.max(0,nx*view[0]+ny*view[1]+nz*view[2]);
    const direct=Math.max(0,nx*keyLight[0]+ny*keyLight[1]+nz*keyLight[2]);
    const visibility=model.visibility[i],metallic=p[9];
    const diffuse=.50+.12*ny+.50*direct*visibility;
    const rx=2*facing*nx-view[0],ry=2*facing*ny-view[1],rz=2*facing*nz-view[2];
    // Reflections from two broad studio lights give curved metal a readable highlight.
    const warm=Math.pow(Math.max(0,-.64*rx+.64*ry+.42*rz),11);
    const cool=Math.pow(Math.max(0,.28*rx+.78*ry-.56*rz),6);
    const edge=Math.pow(1-facing,3)*metallic*17;
    const gloss=Math.max(0,metallic)*visibility;
    // A bright horizon and two dark reflection bands pick out the curved stainless hull.
    const satin=metallic>1?65*Math.exp(-((rx+.48)**2)/.082)+31*Math.exp(-((rx-.60)**2)/.045)-19*Math.exp(-((ry-.21)**2)/.026):0;
    const projectInv=plan?1/vp.dist:inv;
    return [width/2+cam.x*focal*projectInv, height*.52-cam.y*focal*projectInv,inv,
      p[6]*diffuse+gloss*(warm*110+cool*46)+edge+satin,
      p[7]*diffuse+gloss*(warm*95+cool*57)+edge+satin,
      p[8]*diffuse+gloss*(warm*77+cool*76)+edge+satin,cam.z,metallic,(p[0]+4.6)*(plan?1:inv)/9.2,(4.6-p[2])*(plan?1:inv)/9.2];
  });
  for(let i=0;i<model.indices.length;i+=3){
    const a=projected[model.indices[i]],b=projected[model.indices[i+1]],c=projected[model.indices[i+2]];
    if(Math.min(a[6],b[6],c[6])<.22)continue;
    const grain=a[7]<.1?8:1.3;
    rasterTriangle(a,b,c,width,height,(k,u,v,w)=>{
      const z=a[2]*u+b[2]*v+c[2]*w;
      if(z<=depth[k])return;
      depth[k]=z;
      const noise=(((Math.imul(k,1597334677)>>>17)&255)/255-.5)*grain;
      let albedo=1;
      if(a[7]===-1 && tex){
        const divisor=plan?1:z;
        const tx=Math.max(0,Math.min(tex.width-1,Math.floor((u*a[8]+v*b[8]+w*c[8])*tex.width/divisor)));
        const ty=Math.max(0,Math.min(tex.height-1,Math.floor((u*a[9]+v*b[9]+w*c[9])*tex.height/divisor)));
        albedo=tex.lut[tex.samples[ty*tex.width+tx]];
      }
      const j=k*4;
      pixels[j]=(u*a[3]+v*b[3]+w*c[3])*albedo+noise;
      pixels[j+1]=(u*a[4]+v*b[4]+w*c[4])*albedo+noise;
      pixels[j+2]=(u*a[5]+v*b[5]+w*c[5])*albedo+noise;
      pixels[j+3]=255;
    });
  }
  ctx.putImageData(bitmap,0,0);
  vp[frameKey]={signature,canvas,width:cw};
  return canvas;
}
