class Viewport3D {
    constructor(canvas, opts = {}) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.yaw = opts.yaw ?? -0.68;
      this.pitch = opts.pitch ?? 0.48;
      this.dist = opts.dist ?? 14;
      this.targetYaw = this.yaw;
      this.targetPitch = this.pitch;
      this.targetDist = this.dist;
      this.panX = 0;
      this.panY = 0;
      this.fov = opts.fov ?? 520;
      this.autoRotate = opts.autoRotate ?? 0.002;
      this.dragging = false;
      this.lastX = 0;
      this.lastY = 0;
      this.dragDist = 0;
      this.prims = [];
      this.labels = [];
      this.hitTargets = [];
      this.hoveredId = null;
      this.onSelect = opts.onSelect || null;
      this._bindEvents();
    }

    _bindEvents() {
      const c = this.canvas;
      c.addEventListener('pointerdown', (e) => {
        this.dragging = true;
        this.lastX = e.clientX;
        this.lastY = e.clientY;
        this.dragDist = 0;
        c.setPointerCapture(e.pointerId);
      });
      c.addEventListener('pointermove', (e) => {
        const rect = c.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        if (this.dragging) {
          const dx = e.clientX - this.lastX;
          const dy = e.clientY - this.lastY;
          this.dragDist += Math.hypot(dx, dy);
          if(this.canvas.id==='canvasTerrain'&&state.terrainMode==='plan'){
            if(this.dragDist<4)return;
            state.terrainMode='oblique';refreshTerrainReadout();
          }
          this.targetYaw -= dx * 0.0085;
          this.targetPitch = Math.max(-1.35, Math.min(1.42, this.targetPitch + dy * 0.0075));
          this.lastX = e.clientX;
          this.lastY = e.clientY;
        } else {
          this.hoveredId = this._hitTest(mx, my);
          c.style.cursor = this.hoveredId ? 'pointer' : 'grab';
        }
      });
      c.addEventListener('pointerup', (e) => {
        if (this.dragging && this.dragDist < 6) {
          const rect = c.getBoundingClientRect();
          const hit = this._hitTest(e.clientX - rect.left, e.clientY - rect.top);
          if (hit && this.onSelect) this.onSelect(hit);
        }
        this.dragging = false;
      });
      c.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (this.canvas.id === 'canvasContinuum' && e.shiftKey) {
          // Shift+wheel controls continuum scale
          state.continuumScale = Math.max(0, Math.min(100, state.continuumScale + e.deltaY * 0.04));
          document.getElementById('continuumSlider').value = state.continuumScale;
          return;
        }
        this.targetDist = Math.max(this.canvas.id==='canvasTerrain'?2.4:4.5, Math.min(36, this.targetDist * (1 + e.deltaY * 0.0011)));
      }, { passive: false });
    }

    _hitTest(mx, my) {
      // In a dense site map a marker's touch area can extend under another label.
      // Match the visible label before considering the projected anchor.
      const label=this.hitTargets.find(h=>h.isLabel && mx>=h.x && mx<=h.x+h.w && my>=h.y && my<=h.y+h.h);
      if(label)return label.data;
      for (let i = this.hitTargets.length - 1; i >= 0; i--) {
        const h = this.hitTargets[i];
        if (mx >= h.x && mx <= h.x + h.w && my >= h.y && my <= h.y + h.h) return h.data;
      }
      return null;
    }

    resize() {
      const parent = this.canvas.parentElement;
      if (!parent) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = parent.clientWidth || 400;
      const h = parent.clientHeight || 380;
      if (this.canvas.width !== Math.floor(w * dpr) || this.canvas.height !== Math.floor(h * dpr)) {
        this.canvas.width = Math.floor(w * dpr);
        this.canvas.height = Math.floor(h * dpr);
      }
      this.w = w;
      this.h = h;
      this.dpr = dpr;
    }

    beginFrame(bgStyle) {
      this.resize();
      if (!this.dragging) this.targetYaw += this.autoRotate;
      this.yaw += (this.targetYaw - this.yaw) * 0.14;
      this.pitch += (this.targetPitch - this.pitch) * 0.14;
      this.dist += (this.targetDist - this.dist) * 0.14;

      this.cy = Math.cos(this.yaw);
      this.sy = Math.sin(this.yaw);
      this.cp = Math.cos(this.pitch);
      this.sp = Math.sin(this.pitch);

      const ctx = this.ctx;
      ctx.save();
      ctx.scale(this.dpr, this.dpr);
      ctx.clearRect(0, 0, this.w, this.h);
      if (bgStyle) {
        ctx.fillStyle = bgStyle;
        ctx.fillRect(0, 0, this.w, this.h);
      }
      this.prims = [];
      this.labels = [];
      this.hitTargets = [];
    }

    // Transform world (x, y up, z) to camera space
    toCam(x, y, z) {
      const x1 = x * this.cy - z * this.sy;
      const z1 = x * this.sy + z * this.cy;
      const y2 = y * this.cp - z1 * this.sp;
      const z2 = y * this.sp + z1 * this.cp + this.dist;
      return { x: x1, y: y2, z: z2 };
    }

    project(x, y, z) {
      const c = this.toCam(x, y, z);
      if (c.z <= 0.35) return null;
      const depth = this.canvas.id==='canvasTerrain' && state.terrainMode==='plan' ? this.dist : c.z;
      const scale = (this.fov * Math.min(this.w, this.h) / 460) / depth;
      return {
        sx: this.w * 0.5 + this.panX + c.x * scale,
        sy: this.h * 0.52 + this.panY - c.y * scale,
        z: c.z,
        scale,
        cam: c
      };
    }

    // Directional shade helper from world normal (nx, ny, nz)
    shade(nx, ny, nz, baseRGB, ambient = 0.36) {
      // Sun vector in world space
      const lx = 0.56, ly = 0.74, lz = 0.38;
      const len = Math.hypot(nx, ny, nz) || 1;
      const dot = Math.max(0, (nx * lx + ny * ly + nz * lz) / len);
      const k = Math.min(1.22, ambient + dot * 0.74);
      const r = Math.min(255, Math.round(baseRGB[0] * k));
      const g = Math.min(255, Math.round(baseRGB[1] * k));
      const b = Math.min(255, Math.round(baseRGB[2] * k));
      return `rgb(${r},${g},${b})`;
    }

    addPoly(pts3, fill, stroke = null, lineWidth = 0.8, alpha = 1, depthBias = 0, shadeRGB = null, ambient = 0.36) {
      const proj = [];
      let zSum = 0;
      for (let i = 0; i < pts3.length; i++) {
        const p = this.project(pts3[i][0], pts3[i][1], pts3[i][2]);
        if (!p) return;
        proj.push(p);
        zSum += p.z;
      }
      let finalFill = fill;
      if (shadeRGB && pts3.length >= 3) {
        const ax = pts3[1][0] - pts3[0][0], ay = pts3[1][1] - pts3[0][1], az = pts3[1][2] - pts3[0][2];
        const bx = pts3[2][0] - pts3[0][0], by = pts3[2][1] - pts3[0][1], bz = pts3[2][2] - pts3[0][2];
        let nx = ay * bz - az * by;
        let ny = az * bx - ax * bz;
        let nz = ax * by - ay * bx;
        // Orient normal upward for terrain/horizontal surfaces and toward camera/sun for double-sided vertical fins
        if (ny < 0) {
          nx = -nx;
          ny = -ny;
          nz = -nz;
        }
        finalFill = this.shade(nx, ny, nz, shadeRGB, ambient);
      }
      this.prims.push({
        type: 'poly',
        z: zSum / pts3.length + depthBias,
        proj,
        fill: finalFill,
        stroke,
        lineWidth,
        alpha
      });
    }

    addLine(p1, p2, color, width = 1.5, dash = null, alpha = 1, depthBias = 0) {
      const a = this.project(p1[0], p1[1], p1[2]);
      const b = this.project(p2[0], p2[1], p2[2]);
      if (!a || !b) return;
      this.prims.push({
        type: 'line',
        z: (a.z + b.z) * 0.5 + depthBias,
        a, b, color, width, dash, alpha
      });
    }

    addTube(points, widthPx, color, dash = null, alpha = 1, glow = false, depthBias = 0) {
      const proj = [];
      let zSum = 0;
      for (let i = 0; i < points.length; i++) {
        const p = this.project(points[i][0], points[i][1], points[i][2]);
        if (!p) continue;
        proj.push(p);
        zSum += p.z;
      }
      if (proj.length < 2) return;
      this.prims.push({
        type: 'tube',
        z: zSum / proj.length + depthBias,
        proj, widthPx, color, dash, alpha, glow
      });
    }

    addSphere(x, y, z, r, fill, glowColor = null, alpha = 1, depthBias = 0) {
      const p = this.project(x, y, z);
      if (!p) return;
      this.prims.push({
        type: 'sphere',
        z: p.z + depthBias,
        sx: p.sx, sy: p.sy, sr: Math.max(1.5, r * p.scale),
        fill, glowColor, alpha
      });
    }

    addBox(cx, cy, cz, sx, sy, sz, rotY, rgb, stroke = 'rgba(255,255,255,0.12)', alpha = 1, depthBias = 0) {
      const hx = sx * 0.5, hy = sy * 0.5, hz = sz * 0.5;
      const c = Math.cos(rotY), s = Math.sin(rotY);
      const v = (lx, ly, lz) => [
        cx + lx * c - lz * s,
        cy + ly,
        cz + lx * s + lz * c
      ];
      const p000 = v(-hx, -hy, -hz), p100 = v(hx, -hy, -hz), p110 = v(hx, hy, -hz), p010 = v(-hx, hy, -hz);
      const p001 = v(-hx, -hy, hz),  p101 = v(hx, -hy, hz),  p111 = v(hx, hy, hz),  p011 = v(-hx, hy, hz);
      const faces = [
        { pts: [p010, p110, p111, p011], n: [0, 1, 0] },  // top
        { pts: [p000, p001, p101, p100], n: [0, -1, 0] }, // bottom
        { pts: [p001, p011, p111, p101], n: [s, 0, c] },  // +z
        { pts: [p000, p100, p110, p010], n: [-s, 0, -c] },// -z
        { pts: [p100, p101, p111, p110], n: [c, 0, -s] }, // +x
        { pts: [p000, p010, p011, p001], n: [-c, 0, s] }  // -x
      ];
      for (const f of faces) {
        const fill = this.shade(f.n[0], f.n[1], f.n[2], rgb, 0.34);
        this.addPoly(f.pts, fill, stroke, 0.7, alpha, depthBias);
      }
    }

    addCylinder(cx, cy, cz, rTop, rBot, h, segs, rgb, stroke = 'rgba(255,255,255,0.1)', alpha = 1, depthBias = 0) {
      const y0 = cy - h * 0.5, y1 = cy + h * 0.5;
      const topPts = [], botPts = [];
      for (let i = 0; i < segs; i++) {
        const a = (i / segs) * Math.PI * 2;
        const ca = Math.cos(a), sa = Math.sin(a);
        const a2 = ((i + 1) / segs) * Math.PI * 2;
        const ca2 = Math.cos(a2), sa2 = Math.sin(a2);
        const b0 = [cx + ca * rBot, y0, cz + sa * rBot];
        const b1 = [cx + ca2 * rBot, y0, cz + sa2 * rBot];
        const t1 = [cx + ca2 * rTop, y1, cz + sa2 * rTop];
        const t0 = [cx + ca * rTop, y1, cz + sa * rTop];
        topPts.push(t0);
        botPts.push(b0);
        const midA = (a + a2) * 0.5;
        const fill = this.shade(Math.cos(midA), 0.12, Math.sin(midA), rgb, 0.35);
        this.addPoly([b0, b1, t1, t0], fill, stroke, 0.5, alpha, depthBias);
      }
      this.addPoly(topPts, this.shade(0, 1, 0, rgb, 0.42), stroke, 0.6, alpha, depthBias);
    }

    addDome(cx, cy, cz, rx, ry, rz, segU, segV, rgb, stroke = 'rgba(255,255,255,0.14)', alpha = 0.92, depthBias = 0) {
      for (let v = 0; v < segV; v++) {
        const phi0 = (v / segV) * (Math.PI * 0.5);
        const phi1 = ((v + 1) / segV) * (Math.PI * 0.5);
        for (let u = 0; u < segU; u++) {
          const th0 = (u / segU) * Math.PI * 2;
          const th1 = ((u + 1) / segU) * Math.PI * 2;
          const pt = (phi, th) => [
            cx + Math.cos(phi) * Math.cos(th) * rx,
            cy + Math.sin(phi) * ry,
            cz + Math.cos(phi) * Math.sin(th) * rz
          ];
          const p00 = pt(phi0, th0), p10 = pt(phi0, th1), p11 = pt(phi1, th1), p01 = pt(phi1, th0);
          const mp = (phi0 + phi1) * 0.5, mt = (th0 + th1) * 0.5;
          const fill = this.shade(Math.cos(mp) * Math.cos(mt), Math.sin(mp), Math.cos(mp) * Math.sin(mt), rgb, 0.35);
          this.addPoly([p00, p10, p11, p01], fill, stroke, 0.5, alpha, depthBias);
        }
      }
    }

    addTorus(cx, cy, cz, R, r, segU, segV, rgb, stroke = null, alpha = 1, tiltX = 0) {
      const ct = Math.cos(tiltX), st = Math.sin(tiltX);
      const pt = (u, v) => {
        const cu = Math.cos(u), su = Math.sin(u), cv = Math.cos(v), sv = Math.sin(v);
        const lx = (R + r * cv) * cu;
        const ly = r * sv;
        const lz = (R + r * cv) * su;
        return [cx + lx, cy + ly * ct - lz * st, cz + ly * st + lz * ct];
      };
      for (let i = 0; i < segU; i++) {
        const u0 = (i / segU) * Math.PI * 2, u1 = ((i + 1) / segU) * Math.PI * 2;
        for (let j = 0; j < segV; j++) {
          const v0 = (j / segV) * Math.PI * 2, v1 = ((j + 1) / segV) * Math.PI * 2;
          const p00 = pt(u0, v0), p10 = pt(u1, v0), p11 = pt(u1, v1), p01 = pt(u0, v1);
          const mu = (u0 + u1) * 0.5, mv = (v0 + v1) * 0.5;
          const fill = this.shade(Math.cos(mv) * Math.cos(mu), Math.sin(mv), Math.cos(mv) * Math.sin(mu), rgb, 0.36);
          this.addPoly([p00, p10, p11, p01], fill, stroke, 0.45, alpha);
        }
      }
    }

    addPin(x, y, z, title, color, data) {
      const p = this.project(x, y, z);
      if (!p) return;
      this.labels.push({ sx: p.sx, sy: p.sy, z: p.z, title, color, data });
    }

    endFrame() {
      const ctx = this.ctx;
      // Sort back-to-front (largest z first)
      this.prims.sort((a, b) => b.z - a.z);

      for (let i = 0; i < this.prims.length; i++) {
        const pr = this.prims[i];
        ctx.save();
        ctx.globalAlpha = pr.alpha ?? 1;
        if (pr.type === 'poly') {
          ctx.beginPath();
          ctx.moveTo(pr.proj[0].sx, pr.proj[0].sy);
          for (let j = 1; j < pr.proj.length; j++) ctx.lineTo(pr.proj[j].sx, pr.proj[j].sy);
          ctx.closePath();
          if (pr.fill) {
            ctx.fillStyle = pr.fill;
            ctx.fill();
          }
          if (pr.stroke) {
            ctx.strokeStyle = pr.stroke;
            ctx.lineWidth = pr.lineWidth;
            ctx.stroke();
          }
        } else if (pr.type === 'line') {
          ctx.beginPath();
          if (pr.dash) ctx.setLineDash(pr.dash);
          ctx.moveTo(pr.a.sx, pr.a.sy);
          ctx.lineTo(pr.b.sx, pr.b.sy);
          ctx.strokeStyle = pr.color;
          ctx.lineWidth = pr.width;
          ctx.stroke();
        } else if (pr.type === 'tube') {
          ctx.beginPath();
          if (pr.dash) {
            ctx.setLineDash(pr.dash);
            ctx.lineDashOffset = -(state.time * 24);
          }
          ctx.moveTo(pr.proj[0].sx, pr.proj[0].sy);
          for (let j = 1; j < pr.proj.length; j++) ctx.lineTo(pr.proj[j].sx, pr.proj[j].sy);
          ctx.strokeStyle = pr.color;
          ctx.lineWidth = pr.widthPx;
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';
          if (pr.glow) {
            ctx.shadowColor = pr.color;
            ctx.shadowBlur = 10;
          }
          ctx.stroke();
        } else if (pr.type === 'sun') {
          const r=pr.r;ctx.translate(pr.sx,pr.sy);
          const halo=ctx.createRadialGradient(0,0,r*.7,0,0,r*3);
          halo.addColorStop(0,'#e48e38');halo.addColorStop(.42,'#e888292e');halo.addColorStop(1,'#e8882900');
          ctx.fillStyle=halo;ctx.fillRect(-r*3,-r*3,6*r,6*r);
          const disc=ctx.createRadialGradient(0,0,.1*r,0,0,r);
          disc.addColorStop(0,'#ffefba');disc.addColorStop(.84,'#ffd17a');disc.addColorStop(1,'#ffb459');
          ctx.fillStyle=disc;ctx.beginPath();ctx.arc(0,0,r,0,tau);ctx.fill();
        } else if (pr.type === 'image') {
          ctx.translate(pr.sx,pr.sy);ctx.rotate(pr.angle||0);ctx.drawImage(pr.img,-pr.w/2,-pr.h/2,pr.w,pr.h);
        } else if (pr.type === 'sphere') {
          if (pr.glowColor) {
            const g = ctx.createRadialGradient(pr.sx, pr.sy, pr.sr * 0.1, pr.sx, pr.sy, pr.sr * 2.2);
            g.addColorStop(0, pr.glowColor);
            g.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(pr.sx, pr.sy, pr.sr * 2.2, 0, Math.PI * 2);
            ctx.fill();
          }
          const sg = ctx.createRadialGradient(
            pr.sx - pr.sr * 0.32, pr.sy - pr.sr * 0.32, pr.sr * 0.12,
            pr.sx, pr.sy, pr.sr
          );
          sg.addColorStop(0, '#ffffff');
          sg.addColorStop(0.28, pr.fill);
          sg.addColorStop(1, 'rgba(10,12,22,0.92)');
          ctx.fillStyle = sg;
          ctx.beginPath();
          ctx.arc(pr.sx, pr.sy, pr.sr, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      // Draw crisp projected 3D callout labels front-to-back with simple anti-overlap
      this.labels.sort((a, b) => a.z - b.z);
      const placed = [];
      ctx.font = '600 10.5px ui-monospace, SFMono-Regular, Menlo, monospace';
      for (const lb of this.labels) {
        const tw = ctx.measureText(lb.title).width + 16;
        const th = 19;
        // Try locations around the anchor, keeping each label inside the canvas.
        const boundX = x => Math.max(5, Math.min(this.w - tw - 5, x));
        const boundY = y => Math.max(5, Math.min(this.h - th - 5, y));
        let bx = boundX(lb.sx + 10), by = boundY(lb.sy - 22);
        let bestScore = Infinity;
        for (const row of [0, -1, 1, -2, 2, -3, 3, -4, 4]) {
          for (const side of [1, -1]) {
            const x = boundX(side > 0 ? lb.sx + 10 : lb.sx - tw - 10);
            const y = boundY(lb.sy - 22 + row * (th + 4));
            const overlap = placed.some(p => x < p.x + p.w + 3 && x + tw + 3 > p.x && y < p.y + p.h + 3 && y + th + 3 > p.y);
            const coversSite = (lb.data?.terrainKey || this.canvas.id==='canvasCargo') && this.labels.some(p=>p!==lb && p.sx>x-3 && p.sx<x+tw+3 && p.sy>y-3 && p.sy<y+th+3);
            const score = (overlap ? 1000 : 0) + (coversSite ? 85 : 0) + Math.abs(row) * 22 + (side < 0 ? 3 : 0);
            if (score < bestScore) { bestScore = score; bx = x; by = y; }
          }
        }
        placed.push({ x: bx, y: by, w: tw, h: th });

        const isSel = state.selectedHotspot && lb.data && state.selectedHotspot.id === lb.data.id;
        const isHov = this.hoveredId && lb.data && this.hoveredId.id === lb.data.id;

        ctx.save();
        // Anchor dot & leader line
        ctx.beginPath();
        ctx.arc(lb.sx, lb.sy, isSel || isHov ? 4.2 : 3, 0, Math.PI * 2);
        ctx.fillStyle = lb.color;
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(lb.sx, lb.sy);
        ctx.lineTo(bx + 4, by + th * 0.5);
        ctx.strokeStyle = lb.color;
        ctx.lineWidth = isSel || isHov ? 1.6 : 1;
        ctx.globalAlpha = 0.85;
        ctx.stroke();

        // Pill box
        ctx.globalAlpha = 1;
        ctx.fillStyle = state.isLightTheme ? 'rgba(255,255,255,0.92)' : 'rgba(9,14,26,0.88)';
        ctx.strokeStyle = isSel || isHov ? '#ffffff' : lb.color;
        ctx.lineWidth = isSel || isHov ? 1.6 : 1;
        ctx.beginPath();
        if (typeof ctx.roundRect === 'function') {
          ctx.roundRect(bx, by, tw, th, 5);
        } else {
          ctx.rect(bx, by, tw, th);
        }
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = state.isLightTheme ? '#0f172a' : '#f1f5f9';
        ctx.fillText(lb.title, bx + 8, by + 13);
        ctx.restore();

        if (lb.data) {
          this.hitTargets.push({ x: bx, y: by, w: tw, h: th, isLabel:true, data: lb.data });
          this.hitTargets.push({ x: lb.sx - 8, y: lb.sy - 8, w: 16, h: 16, data: lb.data });
        }
      }

      ctx.restore();
    }
  }
