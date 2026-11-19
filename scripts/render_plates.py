"""Render high-resolution 3D studio plates from the MarsEnergy engine via headless Chromium."""
import argparse
import base64
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JS_FILES = (
    "state.js",
    "render/viewport.js",
    "render/mesh.js",
    "render/raster.js",
    "models/freighter.js",
    "models/terminal.js",
    "scenes/device.js",
    "scenes/terrain.js",
    "scenes/cargo.js",
)

PLATES = [
    ("01_mars_utopia_globe", {"scene": "cargo", "cargoMode": "mars", "site": "utopia", "yaw": -0.68, "pitch": -0.22, "dist": 9.6}),
    ("02_utopia_base_oblique", {"scene": "terrain", "site": "utopia", "phase": "p1", "build": "early", "activeUnits": 5, "subsurfaceOn": True, "terrainMode": "oblique", "yaw": -0.36, "pitch": -0.78, "dist": 12.6}),
    ("03_utopia_base_4units", {"scene": "terrain", "site": "utopia", "phase": "p1", "build": "early", "activeUnits": 4, "shed": True, "b2Mode": "save", "subsurfaceOn": True, "terrainMode": "detail", "terrainFocus": "E", "yaw": -2.25, "pitch": -0.64, "dist": 3.6}),
    ("04_gale_bradbury", {"scene": "terrain", "site": "gale", "phase": "p1", "build": "early", "activeUnits": 5, "subsurfaceOn": True, "terrainMode": "oblique", "yaw": -0.24, "pitch": -0.82, "dist": 12.8}),
    ("05_b2_greenhouse", {"scene": "terrain", "site": "utopia", "phase": "p1", "build": "early", "terrainMode": "detail", "terrainFocus": "B2", "subsurfaceOn": True, "yaw": -0.58, "pitch": -0.50, "dist": 3.2}),
    ("06_p1_vertical", {"scene": "device", "phase": "p1", "soilCutaway": True, "umbrellaMode": False, "dustTau": 0.6, "deviceLabels": True, "yaw": -2.55, "pitch": -0.32, "dist": 8.6}),
    ("07_p1_umbrella_dust", {"scene": "device", "phase": "p1", "soilCutaway": True, "umbrellaMode": True, "dustTau": 5.2, "deviceLabels": True, "yaw": -2.45, "pitch": -0.36, "dist": 8.6}),
    ("08_p2_brayton", {"scene": "device", "phase": "p2", "soilCutaway": True, "deviceLabels": True, "yaw": -2.35, "pitch": -0.35, "dist": 9.8}),
    ("09_dfr_station", {"scene": "device", "phase": "dfr", "soilCutaway": True, "drainDrill": "drained", "leadDrainDone": True, "deviceLabels": True, "yaw": -2.42, "pitch": -0.34, "dist": 9.8}),
    ("10_fusion_station", {"scene": "device", "phase": "fusion", "soilCutaway": True, "tritiumIgnited": True, "deviceLabels": True, "yaw": -2.45, "pitch": -0.36, "dist": 9.8}),
    ("11_zone_d_tower", {"scene": "terrain", "site": "utopia", "phase": "p1", "terrainMode": "detail", "terrainFocus": "D", "subsurfaceOn": True, "yaw": -0.45, "pitch": -0.50, "dist": 3.5}),
    ("12_starship_cutaway", {"scene": "cargo", "cargoMode": "vehicle", "phase": "p1", "direction": "in", "yaw": -0.36, "pitch": -0.16, "dist": 9.4}),
    ("13_hohmann_transfer", {"scene": "cargo", "cargoMode": "helio", "site": "utopia", "phase": "p1", "direction": "in", "progress": 0.44, "yaw": -0.25, "pitch": -0.68, "dist": 9.8}),
]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def js_json(value):
    # Escape '<' so data cannot close the enclosing script element.
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")


def image_call(loader, key, path):
    raw = path.read_bytes()
    if not raw.startswith(b"\xff\xd8") or not raw.endswith(b"\xff\xd9"):
        raise ValueError(f"Expected a JPEG: {path}")
    uri = "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")
    return f"{loader}({js_json(key)},{js_json(uri)});"


def build_capture_html():
    src, data, assets = ROOT / "src", ROOT / "data", ROOT / "assets"
    sites = read_json(data / "sites.json")
    grids = {site: read_json(data / "elevation" / (site + ".json")) for site in sites}

    script = ["'use strict';"]
    for name, value in (
        ("PHASES", read_json(data / "phases.json")),
        ("SITES", sites),
        ("zones", read_json(data / "zones.json")),
        ("cargoLoads", read_json(data / "cargo.json")),
        ("DEM", grids),
    ):
        script.append(f"const {name} = {js_json(value)};")
    for filename in JS_FILES:
        script.append((src / filename).read_text(encoding="utf-8").rstrip())
    for planet in ("earth", "mars"):
        script.append(image_call("loadPlanet", planet, assets / "planets" / (planet + ".jpg")))
    for site in sites:
        script.append(image_call("decodeSurfaceTexture", site, assets / "terrain" / (site + ".jpg")))

    plates_map = js_json({k: v for k, v in PLATES})
    runner = f"""
const PLATES = {plates_map};
function syncFlight() {{}}
const canvas = document.getElementById('cap');
const vp = new Viewport3D(canvas, {{ yaw: -0.5, pitch: -0.5, dist: 10, autoRotate: 0 }});
const views = {{ device: vp, terrain: vp, cargo: vp, continuum: vp }};

function renderPlateNow() {{
  const key = (location.hash || '').replace('#', '') || '01_mars_utopia_globe';
  const cfg = PLATES[key] || PLATES['01_mars_utopia_globe'];
  Object.assign(state, cfg);
  vp.yaw = vp.targetYaw = cfg.yaw ?? -0.5;
  vp.pitch = vp.targetPitch = cfg.pitch ?? -0.5;
  vp.dist = vp.targetDist = cfg.dist ?? 10;
  syncCargo();
  vp.beginFrame('#081018');
  if (cfg.scene === 'device') drawDeviceScene(vp);
  else if (cfg.scene === 'terrain') drawTerrainBaseScene(vp);
  else drawCargoMacroScene(vp, cfg.cargoMode || 'mars');
  vp.endFrame();
  window.__plateReady = true;
}}

function waitAndDraw() {{
  if (Object.keys(planetMaps).length === 2 && Object.keys(surfaceTextures).length === Object.keys(SITES).length) {{
    renderPlateNow();
  }} else {{
    setTimeout(waitAndDraw, 40);
  }}
}}
waitAndDraw();
"""
    script.append(runner)
    js_body = "\n\n".join(script)

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;width:100%;height:100%;background:#081018;overflow:hidden}}
canvas{{width:100vw;height:100vh;display:block}}
</style></head>
<body>
<canvas id="cap"></canvas>
<div hidden>
  <span id="inspectorTitle"></span><span id="inspectorBody"></span><span id="inspectSite"></span>
  <select id="terrainSelect"><option value="ref">ref</option></select>
  <div id="terrainDetail"></div><div id="terrainMeasure"></div>
  <span id="cargoTitle"></span><span id="cargoPadLink"></span><span id="cargoLoadTitle"></span>
  <ul id="manifest"></ul><select id="cargoWindow"><option value="0">0</option></select>
  <span id="departPort"></span><span id="arrivalPort"></span><span id="departDate"></span><span id="arrivalDate"></span>
  <span id="windowNote"></span><span id="cargoCaption"></span>
  <input id="flightProgress" type="range" value="0"><span id="flightDay"></span><span id="flightStatus"></span><button id="play"></button>
</div>
<script>
{js_body}
</script>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", metavar="EXECUTABLE", help="path to Chrome, Chromium or chrome-headless-shell")
    parser.add_argument("--out", type=Path, default=ROOT / "assets" / "renders")
    args = parser.parse_args()
    browser = args.chrome or os.environ.get("CHROME_BIN")
    if browser:
        browser = shutil.which(os.path.expanduser(browser))
    else:
        browser = next((path for name in ("chromium", "google-chrome", "chrome-headless-shell")
                        if (path := shutil.which(name))), None)
    if not browser:
        parser.error("Chrome or Chromium executable not found. Set --chrome or CHROME_BIN.")

    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".capture-", dir=out_dir) as tmp:
        scratch = Path(tmp)
        cap_html = scratch / "capture.html"
        cap_html.write_text(build_capture_html(), encoding="utf-8")
        for name, _ in PLATES:
            out_png = scratch / f"{name}.png"
            cmd = [
                browser,
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--user-data-dir={scratch / 'profile'}",
                "--window-size=1400,880",
                "--virtual-time-budget=2200",
                f"--screenshot={out_png}",
                f"{cap_html.as_uri()}#{name}",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode or not out_png.is_file() or out_png.stat().st_size < 10000:
                raise RuntimeError(f"Failed rendering {name}: {res.stderr}")
            size = out_png.stat().st_size
            out_png.replace(out_dir / out_png.name)
            print(f"Rendered {out_png.name} ({size:,} bytes)", flush=True)


if __name__ == "__main__":
    main()
