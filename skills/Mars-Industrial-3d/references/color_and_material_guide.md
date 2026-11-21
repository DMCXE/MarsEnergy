# Color & Material Guide (通用颜色与材质指南)

This palette follows the **80/20 Industrial Discipline**: 75%–85% restrained neutral materials give every model timeless hardware credibility, while 15%–25% semantic accents communicate system architecture in under 2 seconds.

---

## 1. Core Neutral Palette (75%–85% Surface Area)

| Material Role | Hex Codes | Surface & PBR Cues | Typical Usage |
| :--- | :--- | :--- | :--- |
| **Warm Enamel Shell** (外壳米白搪瓷) | `#D3CFBC` / `#E1E0CC` | Satin matte painted enamel (`roughness ~0.40–0.55`), soft specular roll-off; avoid sterile `#FFFFFF` which clips highlights on white documents. | Pressurized modules, outer structural ribs, instrument housings, rocket fairings, architectural walls. |
| **Aerospace Titanium / Brushed Aluminum** (钛合金/拉丝铝) | `#ADB7B8` / `#93A2A3` | Subtle brushed satin metallic (`metallic ~0.75–0.85, roughness ~0.30–0.40`). | Structural rails (e.g., CubeSat frame), reinforcement rings, manifolds, antennas, pipe flanges, display plinth accents. |
| **Anodized Dark Grey** (阳极氧化深灰) | `#353F45` / `#2B353B` | Matte bead-blasted anodized aluminum or anti-static polymer (`roughness ~0.55–0.65`). | Lab baseplates, multi-fin heatsinks, equipment racks, internal bulkheads, cable trays, darkened shed buildings. |
| **Chamfered Light Plinth** (切角浅灰底座) | `#C7CBD1` / `#D6D9DD` | Matte concrete/composite slab with crisp 45° chamfered corners. | Architectural aprons, diorama bases, standalone module display plinths. |
| **Gold Contact / Brass Accent** (镀金触点/黄铜热端) | `#D9A74A` / `#C99238` | High-sheen metallic (`metallic ~0.90, roughness ~0.22`). | Standardized pogo-pins, PC/104 pin headers, precision valve fittings, thermal couplings. |

---

## 2. Semantic Functional Accents (15%–25% Surface Area)

Rule of thumb: **Use at most 3 semantic accents on any single asset.** Always keep the color-to-meaning mapping consistent across an entire project batch.

| Semantic Meaning | Primary Hex | Secondary Hex | Typical Applications |
| :--- | :--- | :--- | :--- |
| **Vital / Life-Support / Primary Bus / Active Healthy / Bio** | `#34D399` (Emerald / Mint) | `#10B981` | Vital power bus rail, active hospital/habitat windows, hydroponic seedlings, hydrogen tank band, green status LEDs. |
| **Telemetry / Data / Water / Cold Side / Rim Highlight** | `#48CAE4` (Industrial Cyan) | `#509A95` (Teal) | Data bus, coolant/water piping, OLED bezel accents, battery charge indicator bars, oxygen tank band, back-right rim light. |
| **Thermal / Dispatchable Load / Caution / High-Temp** | `#FF8F45` (Warm Amber) | `#DF9B47` (Copper-Orange) | Dispatchable bus rail, heater safety guard rim, rotary kiln drum, waste-heat inlet pipe, rocket nosecone band, parachute pack. |
| **Secondary Subsystem Differentiator** *(optional)* | `#A78BFA` / `#818CF8` (Muted Purple/Indigo) | — | Only when >3 distinct zones/modules must sit side-by-side (e.g., greenhouse module cap band, science lab card). |

---

## 3. Natural & Environmental Accents (For Dioramas & Cross-Sections)

| Element | Hex Codes | Visual Rule |
| :--- | :--- | :--- |
| **Dry Regolith / Terracotta Soil** | `#9E6C4F` / `#865842` | Matte granular earth (`roughness ~0.85–0.95`), subtle horizontal micro-layering. |
| **Sedimentary Rock / Hydrated Clay** | `#6B584B` / `#7C736C` | Layered dark-brown and slate-grey bands; never confuse with blue ice. |
| **Subsurface Water Ice** | `#A8D5E5` / `#7BB8CC` | Pale icy-blue semi-matte crystalline stratum strictly buried beneath dry overburden unless domain dictates otherwise. |
| **Photovoltaic / Optical Glass** | `#1B365D` (Deep PV Blue) / `#5C8F91` (Tinted Glass) | Clean dark-blue grid cells with crisp silver busbars; clean tinted glass edges with subtle bevel reflections. |

---

## 4. Dual-Canvas Adaptation (Dark Decks + White Documents)

Assets built with this system must look equally crisp on **dark keynote decks (`#060E1A`)** and **white Word/PDF pages (`#FFFFFF` / `#F8FAFC`)**:
1. **Why Warm Off-White (`#D3CFBC`) beats Pure White (`#FFFFFF`)**: Pure white disappears on white paper; warm enamel holds a clean, readable silhouette on white pages while glowing gracefully under warm key lighting on dark slides.
2. **Why Rim Lighting (`#48CAE4` or crisp cool-white) is mandatory**: Matte dark-grey baseplates (`#2B353B`) melt into `#060E1A` navy slides unless a crisp back-right rim highlight traces the chamfered perimeter.
3. **Never bake background glow or heavy black floor shadows into the alpha channel**: Keep floor shadows subtle and tightly grounded (or omit soft wide floor haze) so the PNG floats effortlessly on both dark glass cards and white editorial pages.

---

## 5. Adapting the Palette to Other Domains

When adapting this skill outside aerospace/energy, **keep the 3 neutral bases verbatim** and reassign the 3 semantic accents to match the new domain:
- **Medical / Biotech Hardware**: Enamel + Titanium + Dark Grey; Accents = Sterile Teal (`#48CAE4`) for fluidics, Emerald (`#34D399`) for active diagnostics, Amber (`#FF8F45`) for bio-safety interlocks.
- **Robotics / Industrial Automation**: Enamel + Titanium + Dark Grey; Accents = Amber (`#FF8F45`) for actuated joints/safety guards, Cyan (`#48CAE4`) for LiDAR/sensors, Emerald (`#34D399`) for power bus.
- **Smart City / Clean Grid**: Enamel + Concrete Plinth + Dark Grey; Accents = Emerald (`#34D399`) for critical infrastructure, Soft Blue (`#60A5FA`) for throttled tier, Dark Grey (`#353F45`) for shed loads.
