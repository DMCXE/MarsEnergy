"""Export the device scene presets as grouped GLBs and studio PNGs."""
import argparse
from functools import partial
import json
from math import atan2, cos, sin
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

from build import DEFAULT_DIR, bake
from geometry import MATERIALS, Model

sys.path.append(str(Path(__file__).resolve().parents[1]))
from render_plates import PLATES


SCENE_GROUPS = (
    (
        ("06_p1_vertical", "P1 heat-pipe plant, vertical radiators"),
        ("07_p1_umbrella_dust", "P1 heat-pipe plant, dusty umbrella radiators"),
    ),
    (("08_p2_brayton", "P2 Brayton-cycle plant"),),
    (("09_dfr_station", "DFR power station, drained state"),),
    (("10_fusion_station", "Fusion power station cutaway"),),
)

STUDIO_MATERIALS = {
    "titanium": "titanium",
    "steel": "steel",
    "bright": "steel",
    "dark": "graphite",
    "graphite": "anodized",
    "ceramic": "enamel",
    "brass": "amber",
    "copper": "copper",
    "teal": "teal",
    "red": "red",
    "rock": "soil",
    "strata": "ochre",
    "ground": "soil",
    "concrete": "stone",
    "glass": "lcfs",
}


def load_scene_meshes(node, presets):
    result = subprocess.run(
        [node, str(Path(__file__).with_name("device_mesh.cjs"))],
        input=json.dumps(presets), capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def add_section(model, part, positions, normals, local_palette, triangles, materials):
    triangle_colors = local_palette[triangles]
    if not np.all(triangle_colors == triangle_colors[:, :1]):
        raise ValueError(f"Expected a single material per triangle in {part}")
    a, b, c = positions[triangles].transpose(1, 0, 2)
    face_normals = np.cross(b - a, c - a)
    has_area = np.linalg.norm(face_normals, axis=1) > 1e-10
    triangles = triangles[has_area].copy()
    # Keep the browser shading normals while making the GLB winding agree with them.
    reversed_faces = np.einsum("ij,ij->i", face_normals[has_area], normals[triangles].sum(axis=1)) < 0
    triangles[reversed_faces] = triangles[reversed_faces, ::-1]
    labels = triangle_colors[has_area, 0]
    for label in np.unique(labels):
        faces = triangles[labels == label]
        used, indices = np.unique(faces, return_inverse=True)
        model.parts[part][materials[label]].append((positions[used], normals[used], indices.reshape(faces.shape)))


def make_model(name, scene, preset, mesh, palette, yaw):
    vertices = np.asarray(mesh["vertices"])
    indices = np.asarray(mesh["indices"], dtype=np.intp).reshape(-1, 3)
    colors, labels = np.unique(vertices[:, 6:], axis=0, return_inverse=True)
    materials = [palette[tuple(color)] for color in colors]

    # Map the browser's +Y-up geometry into the +Z-up authoring frame, then align
    # the exposed section with the standard studio camera and its light rig.
    axes = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    rotation = np.array([[cos(yaw), -sin(yaw), 0], [sin(yaw), cos(yaw), 0], [0, 0, 1]])
    transform = rotation @ axes
    positions = vertices[:, :3] @ transform.T
    normals = vertices[:, 3:6] @ transform.T

    model = Model(name)
    groups = mesh["groups"]
    end_offsets = [group["offset"] for group in groups[1:]] + [len(mesh["indices"])]
    for group, end in zip(groups, end_offsets):
        section = indices[group["offset"] // 3:end // 3]
        if len(section):
            add_section(model, group["name"], positions, normals, labels.reshape(-1), section, materials)

    display_state = {key: value for key, value in preset.items() if key not in {"scene", "yaw", "pitch", "dist", "deviceLabels"}}
    model.state = {
        "sourceScene": scene,
        "sceneState": display_state,
        "sourceScale": "Illustrative display units",
        "displayRotationZRadians": yaw,
    }
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--width", type=int, default=2400)
    parser.add_argument("--samples", type=int, default=12)
    args = parser.parse_args()
    if args.width < 3 or args.samples < 1:
        parser.error("--width must be at least 3 and --samples must be positive")
    node = shutil.which("node")
    if not node:
        parser.error("Node.js is required to read the JavaScript scene meshes")

    presets = dict(PLATES)
    scene_keys = [scene for group in SCENE_GROUPS for scene, _ in group]
    data = load_scene_meshes(node, [presets[scene] for scene in scene_keys])
    palette = {tuple(value): STUDIO_MATERIALS[key] for key, value in data["palette"].items()}
    for index, rgb in enumerate(((66, 76, 80), (59, 69, 74), (73, 81, 83)), 1):
        material = f"radiator_panel_{index}"
        MATERIALS[material] = ("".join(f"{channel:02x}" for channel in rgb), .43, .55, 1, 0)
        palette[(*rgb, .43)] = material

    # The original close-up views have similar azimuths. Use the same front
    # direction for all assets and a shared fit for the P1 comparison pair.
    reference_yaw = presets["07_p1_umbrella_dust"]["yaw"]
    yaw = atan2(-1, -.43) - atan2(cos(reference_yaw), -sin(reference_yaw))
    meshes = dict(zip(scene_keys, data["meshes"]))
    groups = [
        [(scene.split("_", 1)[1], partial(make_model, name, scene, presets[scene], meshes[scene], palette, yaw))
         for scene, name in group]
        for group in SCENE_GROUPS
    ]
    bake(groups, args.out, args.width, args.samples, floor_origin=True)


if __name__ == "__main__":
    main()
