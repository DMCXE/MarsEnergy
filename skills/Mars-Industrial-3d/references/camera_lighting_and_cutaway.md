# Camera, Lighting, Cutaway & Detailing Guide (机位、布光与通用细节规范)

Visual consistency across a multi-asset library comes from **locking geometry and photography rules before describing any subject**.

---

## 1. Camera Geometry (统一相机参数)

| Parameter | Standard Value | Why It Matters |
| :--- | :--- | :--- |
| **Viewpoint** | 3/4 isometric elevated view (3/4 等轴微俯视) | Shows top layout, front elevation, and side depth simultaneously without hiding interior bays. |
| **Elevation / Pitch** | `25°–30°` (recommended batch lock: **`27°`**) | Low enough to read vertical doors/racks/pins, high enough to read floor busbars and ground piping. |
| **Focal Length** | `55–65 mm` equivalent (or pseudo-orthographic) | Suppresses wide-angle distortion so parallel edges stay crisp and side-by-side pairs look architecturally aligned. |
| **Framing & Margin** | Subject centered; **`≥ 5%` clean transparent margin** on all 4 sides | Prevents clipped antennas/pipes and enables automated lossless bounding-box cropping later. |
| **Coordinate System (`.glb`)** | Right-handed `+Y` up, centered at origin `(0, 0, 0)`, bottom resting cleanly on `Y = 0` | Ensures instant drag-and-drop import into Blender, Three.js, Spline, or custom renderers. |

---

## 2. Studio Lighting Rig (统一三点工业布光)

1. **Key Light (主光)**: Warm-white studio softbox from **front-top-left** (reference directional vector `[-0.49, 0.82, 0.69]`), creating soft sculptural gradients across curved shells and crisp bevel highlights.
2. **Rim Light (轮廓边缘光)**: Crisp **cool cyan (`#48CAE4`)** (or cool neutral white for pure light-mode projects) from **back-right**, outlining dark anodized baseplates, heatsinks, and cylindrical hulls so they pop cleanly off dark canvases (`#060E1A`).
3. **Fill Light (补光)**: Low-intensity neutral soft fill so sectioned interior racks remain fully legible with zero crushed black voids.
4. **No Fake Glows or Lens Flares**: Avoid bloom haze, volumetric fog, fire/exhaust plumes, or heavy cast floor shadows that bleed to image edges.

---

## 3. Structural Cutaway & Archetype Detailing Rules (五大原型细节法则)

### A. Physical Cutaways (物理剖切架构)
- **Preserve the silhouette**: Keep outer structural ribs, frames, or steel reinforcement rings intact across the roof and ends so viewers still recognize the outer building/module instantly.
- **Slice angle**: Physically section open **`110°–135°`** on the camera-facing front side (never rely solely on blurry semi-transparent X-ray shells, which look messy and fail in opaque CPU/real-time renderers).
- **Show wall thickness**: Exposed cut edges MUST display **double-wall insulated shell thickness** and clean metallic trim caps—never paper-thin zero-thickness polygons.
- **Proportional internal mapping**: When internal bays represent quantitative ratios (e.g., `30%` battery rack vs. `70%` fuel cell + tanks), state the exact spatial ratio (`3:7`) explicitly in the prompt.

### B. Locked-Camera A/B State Pairs (锁机位双态对照)
- Whenever comparing two operating states or two engineering options (e.g., full-power `12h` vs. dimmed `8h`, vertical fins vs. horizontal umbrella, Site A vs. Site B):
  - Lock **100% identical camera coordinates, focal length, plinth footprint, and horizon line**.
  - Change ONLY the targeted variables (lighting intensity / active LED bars / geological strata / process equipment).
  - For image generators (Flux/Midjourney), generate State A first, then use **image-to-image / edit lock** for State B so slide-to-slide overlay alignment stays pixel-accurate.

### C. Modular Interfaces & Exploded Hot-Swap Details (模块化与防呆细节)
- **Exploded hover pose**: Lift one replaceable module **`~15 mm`** vertically above its socket to reveal underside connectors without detaching it so far that the mechanical relationship is lost.
- **Standardized connector micro-details**:
  - Uniform array of **gold pogo-pins / contact pads** (e.g., 8-pin grid).
  - **Two asymmetric alignment/keying pins** (防呆定位销) visually proving foolproof polarity.
  - Shared mechanical geometry across related assets (e.g., plug-in cube bottom matches bus board socket AND satellite payload frame).
- **Tidy routing**: Orthogonal bent cables/pipes with color-coded bands; zero tangled spaghetti wires.

### D. Geological / Process Cross-Section Plinths (地质与工艺横断面)
- Use a uniform cylindrical or chamfered-square terrain block sliced open **`110°`** at the front.
- Enforce **clean, distinct horizontal strata** matching real domain science (e.g., dry terracotta overburden cleanly above pale icy-blue ice stratum vs. layered dark-brown hydrated clay with zero blue ice).
- Trace the complete physical loop without broken pipes (e.g., intake/borehole → conversion drum/skid → condenser/manifold → storage tank → outlet/tailings).

### E. Minimalist Scale Dioramas (极简同构沙盘)
- Use **clean geometric architectural massing** on a chamfered matte plinth.
- Strip decorative noise: **zero random trees, zero realistic human figures, zero road clutter**.
- Communicate system priority solely through **surface utility line color** + **3-tier window/fixture lighting** (bright vital / dimmed throttled / dark switched-off).

---

## 4. Universal Micro-Details & Anti-Hallucination Rules (通用微细节与防穿帮红线)

### Always Include These Subtle Quality Signals
- Crisp **chamfered edges (倒角)** on baseplates, housings, and racks.
- Subtle **fasteners, panel seams, ventilation louvers, flanges, and pipe elbows**.
- **Blank dark-glass OLED displays** on meters/receivers (`blank dark OLED glass, no gibberish text`).
- Realistic **physical switches, handles, spring feet, or protective guard rails**.

### Universal Negative Constraints (Always Append)
- **Zero Text Policy**: `no text, no letters, no numbers, no gibberish labels, no logos, no watermarks, no floating HUD callouts`.
- **Zero Aesthetic Drift**: `no cartoon proportions, no cheap neon cyberpunk glow, no messy clutter, no background frame or vignette`.
- **Domain Safety Guardrails** *(customize per domain)*:
  - Educational lab kits → `safe low-voltage DC benchtop hardware, no open flame, no alcohol burners, no 220V/110V AC wall plugs`.
  - Educational rockets / launch hardware → `clean educational model/sounding rocket aesthetic, no fire, no exhaust smoke`.
  - Scientific integrity → explicitly forbid common AI hallucinations (e.g., `no open blue surface lake`, `no Earth open-air plastic farm tunnel`).

---

## 5. Post-Delivery Verification Checklist (交付验收核验)
After assets are generated, verify:
1. **Transparency & Margins**: True RGBA PNG with clean alpha edges (zero halo fringe on `#060E1A` AND `#FFFFFF`), resolution `≥ 2400 × 1600 px`, `≥ 5%` clear margin on all 4 sides.
2. **Text Audit**: Inspect every OLED screen, badge, and housing surface at 100% zoom — zero AI-hallucinated pseudo-characters.
3. **Locked-Pair Alignment**: Overlay A/B pairs at 50% opacity — silhouettes and plinth corners must align cleanly.
4. **Layered `.glb` Check**: Open/parse `.glb` to verify node hierarchy separates outer shells, internal assemblies, light groups, and connectors cleanly.
