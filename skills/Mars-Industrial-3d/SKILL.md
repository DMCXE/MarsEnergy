---
name: industrial-3d-asset-prompt
description: >-
  Generate cohesive, engineering-grade 3D model and studio render prompts (both
  master specifications for 3D modeling agents/Blender/artists and standalone
  prompts for Flux/Midjourney/Rodin/Tripo). Use when designing consistent
  industrial hard-surface 3D assets, technical cutaways, modular hardware kits,
  locked-camera A/B comparisons, or architectural/process dioramas for decks,
  proposals, web showcases, or STEM education.
---

# Industrial 3D Asset Prompt Engineering

This skill distills a proven industrial-design prompt system for generating cohesive sets of hard-surface 3D models (`.glb`) and transparent studio renders (RGBA `.png`) that stay visually unified across dark-mode keynotes, white-paper documents, and interactive web showcases.

## When to Use This Skill
- You need to write a **Master Spec Prompt** for a 3D modeling agent, Blender automation script, or human 3D artist to produce a multi-asset library.
- You need **Standalone Image/3D Prompts** for generative tools (Flux, Midjourney, Nano Banana, Tripo, Meshy, Rodin) that must look like they belong to the exact same product family.
- You need to enforce **consistent style, color semantics, camera angle, cutaway logic, and domain guardrails** across iterative batches of assets.

## Core Standards at a Glance

### 1. Universal Visual Style (通用风格)
- **Aesthetic anchor**: Precision Industrial Hard-Surface & Technical Cutaway (inspired by aerospace engineering manuals and Braun/Dieter Rams hardware clarity).
- **Must include**: Clean geometric chamfers, structural ribs/flanges, realistic wall thickness on sectioned shells, tidy orthogonal cable/pipe routing, color-coded bands, and solid chamfered plinths or lab baseplates.
- **Strictly forbid**:
  - Cheap cyberpunk neon glow or oversaturated sci-fi clichés.
  - Childish/cartoon proportions or glossy toy-like plastic.
  - **Any baked text, gibberish labels, numbers, watermarks, or floating HUDs** (all labels and screen readouts are overlaid later as clean vectors in PPT/web; screens must stay clean blank dark OLED glass).

### 2. Five Reusable Design Archetypes (设计原型)
Pick the archetype(s) that match the user's asset list (full specs in [camera_lighting_and_cutaway.md](./references/camera_lighting_and_cutaway.md)):
1. **Physical Cutaway Architecture**: Preserve exterior structural ribs/rings for silhouette recognition; physically slice open `110°–135°` on the camera-facing side to reveal double-wall thickness and proportional internal bays (e.g., exact `3:7` volume split mapping real numerical ratios).
2. **Locked-Camera A/B Comparison Pair**: Lock identical camera, horizon, and bounding framing across two states (full power vs. dimmed, normal vs. fault, Option A vs. Option B) so slides or UI toggles switch seamlessly without spatial drift.
3. **Desktop Hardware & Modular Interface Kit**: Matte dark-grey chamfered lab baseplate, physical toggle switches, blank dark OLED meter screens, tidy cables, and optional exploded/hot-swap hover (`~15 mm` lift) exposing standardized gold pogo-pins and asymmetric alignment keys.
4. **Geological / Process Cross-Section Diorama**: Standardized round or chamfered square terrain/process plinth sliced open `110°` on the front to show clear subsurface strata and unbroken vertical/horizontal equipment flows.
5. **Minimalist Isomorphic Scale Diorama**: Zero clutter (no random trees or realistic pedestrians); clean geometric architectural blocks connected by slim color-coded utility trenches and 3-tier lighting states (bright vital / soft dimmed / dark shed).

### 3. Universal Color & Material Guide (颜色指南)
Keep **75%–85%** of every model in restrained neutral industrial finishes, reserving **15%–25%** for semantic accent coding (max 3 semantic accents per asset). Full hex codes and light/dark background tuning live in [color_and_material_guide.md](./references/color_and_material_guide.md):
- **Neutral Base (75%–85%)**:
  - Main enamel shells: Warm Off-White `#D3CFBC` / `#E1E0CC` (never sterile pure `#FFFFFF`).
  - Structural metal / rails / manifolds: Brushed Titanium / Aluminum `#ADB7B8` / `#93A2A3`.
  - Baseplates / heatsinks / frames: Matte Anodized Dark Grey `#353F45` / `#2B353B`.
- **Semantic Accents (15%–25%)**:
  - Vital / Primary Bus / Active Healthy / Bio: Emerald / Mint `#34D399`.
  - Data / Water / Telemetry / Cold Side / Rim Light: Industrial Cyan / Teal `#48CAE4` / `#509A95`.
  - Thermal / Dispatchable Load / Caution / Accent: Warm Amber Orange `#FF8F45` / `#DF9B47`.

### 4. Universal Detailing, Camera & Delivery Specs (通用细节与交付)
- **Camera**: 3/4 isometric elevated view (`25°–30°` pitch, default lock `27°`; `55–65 mm` equivalent focal length to minimize distortion).
- **Lighting**: Warm-white studio key light from front-top-left + crisp cool cyan (`#48CAE4`) or clean neutral rim light from back-right so dark metals separate cleanly from dark slide canvases while warm enamel stays crisp on white paper.
- **File Outputs**:
  - **Render**: Transparent RGBA `.png`, `≥ 2400 × 1600 px`, `≥ 5%` clean transparent margin on all four edges, no rectangular drop-shadow clipping. (If a generator cannot output alpha, specify `isolated on solid uniform dark navy background #060E1A` for clean post-extraction.)
  - **3D Source** (when using 3D agents/Blender): Layered `.glb` with named independent groups (outer shell, internal modules, light strips, shared connectors), right-handed `+Y` up, centered at origin.
- **Cross-Asset Shared Geometry**: When multiple assets connect conceptually (e.g., a bus board and a plug-in payload module), explicitly instruct that their mechanical connectors share identical geometry and pin layout.

## Workflow: Writing a New Asset Prompt Pack

1. **Audit Scope & Target Pipeline**:
   - Clarify whether the user will feed prompts to a **3D Agent / Blender / Artist** (produce a Master Control Prompt with `.glb` + `.png` specs) or **Single-Image / 3D Generators** like Flux / Midjourney / Tripo (produce self-contained English single-asset prompt cards), or **both**.
2. **Map Each Asset to an Archetype & Priority**:
   - Assign `P0 / P1 / P2` tiers, exact filenames (`snake_case`), any locked-camera A/B pairs, and any cross-asset shared connectors.
3. **Define 1–2 Domain Guardrails per Asset**:
   - Every asset MUST specify what **not** to hallucinate physically or scientifically (e.g., "enclosed low-voltage DC lab kit — no open flames or 220V wall plugs", "subsurface ice strictly under regolith overburden — no open blue lakes", "no exhaust flames on educational rocket").
4. **Assemble Prompts from Templates**:
   - Read [prompt_templates.md](./references/prompt_templates.md) for the exact Chinese Master Control Prompt skeleton and English single-asset prompt formula.
   - Reference [mars_energy_showcase.md](./examples/mars_energy_showcase.md) if you want to inspect proven phrasing that yielded consistent 11-asset batches.
5. **Run the Delivery QA Checklist**:
   Before returning prompts to the user, verify every single prompt includes:
   - [ ] Locked camera angle (`25°–30°`, `55–65 mm`) and studio lighting (warm-white key + rim light).
   - [ ] Explicit neutral + semantic hex palette (<= 3 accent colors per piece).
   - [ ] Concrete geometric details (chamfers, wall thickness, cables/pipes, blank dark screens).
   - [ ] Strict anti-clutter & no-text constraint (`no text, no labels, no HUD, no watermark`).
   - [ ] Transparent RGBA PNG (`≥ 2400×1600`, `≥ 5%` margin) and layered `.glb` naming (if applicable).
   - [ ] Asset-specific domain/safety guardrails and locked-camera pairing notes (if applicable).

## Reference Files
- [Color & Material Guide](./references/color_and_material_guide.md) — Neutral/semantic hex system, surface finishes, and dark vs. light canvas adaptation.
- [Camera, Lighting & Cutaway Guide](./references/camera_lighting_and_cutaway.md) — Isometric framing, three-point rim lighting, `110°–135°` cutaway geometry, exploded hot-swap poses, and locked A/B comparisons.
- [Prompt Templates](./references/prompt_templates.md) — Copy-ready Chinese Master Prompt & English single-asset prompt templates with domain swap slots.
- [MarsEnergy 11-Asset Showcase](./examples/mars_energy_showcase.md) — Proven reference examples across all five design archetypes.
