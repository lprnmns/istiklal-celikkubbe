#!/usr/bin/env python3
"""Convert the authoritative KTR STEP model into a browser-ready GLB.

The script intentionally fails instead of silently falling back to STL or a
procedural model. It uses FreeCAD headless when available and reconstructs
operator-readable materials when STEP presentation colors are not exposed by
the import API.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "work/ktr1.step"
DEFAULT_OUTPUT = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb"
DEFAULT_MANIFEST = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json"
PUBLIC_MANIFEST = PROJECT_ROOT / "frontend/public/assets/digital-twin/asset_manifest.json"


FREECAD_WORKER = r'''
from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

import FreeCAD
import Import

source = Path(__SOURCE__)
output = Path(__OUTPUT__)
manifest_path = Path(__MANIFEST__)
public_manifest_path = Path(__PUBLIC_MANIFEST__)
tolerance = float(__TOLERANCE__)

if not source.exists():
    raise SystemExit(f"STEP source not found: {source}")

step_text = source.read_text(encoding="utf-8", errors="ignore")
step_color_records = step_text.count("COLOUR_RGB")

doc = FreeCAD.newDocument("ktr_step_to_glb")
Import.insert(str(source), doc.Name)
doc.recompute()

objects = []
for obj in doc.Objects:
    if getattr(obj, "TypeId", "") != "Part::Feature":
        continue
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        continue
    bb = shape.BoundBox
    if max(bb.XLength, bb.YLength, bb.ZLength) <= 0:
        continue
    objects.append(obj)

if not objects:
    raise SystemExit("FreeCAD imported the STEP file but no Part::Feature solids were found.")

def object_global_placement(obj):
    if hasattr(obj, "getGlobalPlacement"):
        try:
            return obj.getGlobalPlacement()
        except Exception:
            pass
    return getattr(obj, "Placement", FreeCAD.Placement())

def globalize_point(obj, point):
    # STEP import may place important subassemblies under App::Part parents.
    # The raw Shape points are local for those children; FreeCAD GUI displays
    # them with getGlobalPlacement(). The browser GLB must use that same global
    # placement or weapon/camera parts appear detached from the main body.
    #
    # Exception: the imported `kamera v3` Shape already carries its own object
    # Placement in this FreeCAD build, but not the parent App::Part placement.
    # Applying full getGlobalPlacement() double-applies the object placement and
    # moves it above the model; applying no parent transform leaves it detached.
    # Therefore use parent-only placement: global * inverse(local placement).
    label = str(getattr(obj, "Label", "")).lower()
    if "kamera" in label or "camera" in label:
        try:
            parent_only = object_global_placement(obj).multiply(obj.Placement.inverse())
            return parent_only.multVec(point)
        except Exception:
            return point
    return object_global_placement(obj).multVec(point)

def bbox_corners(bb):
    return [
        FreeCAD.Vector(x, y, z)
        for x in (bb.XMin, bb.XMax)
        for y in (bb.YMin, bb.YMax)
        for z in (bb.ZMin, bb.ZMax)
    ]

global_min = [float("inf"), float("inf"), float("inf")]
global_max = [float("-inf"), float("-inf"), float("-inf")]
for obj in objects:
    for point in bbox_corners(obj.Shape.BoundBox):
        p = globalize_point(obj, point)
        global_min[0] = min(global_min[0], p.x)
        global_min[1] = min(global_min[1], p.y)
        global_min[2] = min(global_min[2], p.z)
        global_max[0] = max(global_max[0], p.x)
        global_max[1] = max(global_max[1], p.y)
        global_max[2] = max(global_max[2], p.z)

center = [(global_min[i] + global_max[i]) * 0.5 for i in range(3)]
extent = [global_max[i] - global_min[i] for i in range(3)]
max_extent = max(extent) or 1.0
scene_scale = 3.75 / max_extent

def transform_global(point):
    # FreeCAD STEP is converted into the cockpit scene coordinate system:
    # X stays lateral, STEP Z becomes scene up, STEP Y becomes forward depth.
    return (
        (point.x - center[0]) * scene_scale,
        (point.z - global_min[2]) * scene_scale - 0.42,
        -(point.y - center[1]) * scene_scale,
    )

def transform(obj, point):
    return transform_global(globalize_point(obj, point))

def transform_raw(x, y, z):
    class P:
        pass
    p = P()
    p.x = x
    p.y = y
    p.z = z
    return transform_global(p)

materials = [
    {"name": "freecad_body_warm_white", "pbrMetallicRoughness": {"baseColorFactor": [0.92, 0.94, 0.9, 1.0], "metallicFactor": 0.02, "roughnessFactor": 0.36}},
    {"name": "freecad_armor_vivid_red", "pbrMetallicRoughness": {"baseColorFactor": [0.78, 0.05, 0.045, 1.0], "metallicFactor": 0.08, "roughnessFactor": 0.34}},
    {"name": "launcher_visible_graphite", "pbrMetallicRoughness": {"baseColorFactor": [0.09, 0.095, 0.105, 1.0], "metallicFactor": 0.24, "roughnessFactor": 0.28}},
    {"name": "mechanical_bright_metal", "pbrMetallicRoughness": {"baseColorFactor": [0.68, 0.7, 0.72, 1.0], "metallicFactor": 0.42, "roughnessFactor": 0.22}},
    {"name": "sensor_camera_bright_cyan", "pbrMetallicRoughness": {"baseColorFactor": [0.02, 0.82, 0.98, 1.0], "metallicFactor": 0.08, "roughnessFactor": 0.24}},
    {"name": "base_visible_dark_gray", "pbrMetallicRoughness": {"baseColorFactor": [0.12, 0.13, 0.15, 1.0], "metallicFactor": 0.22, "roughnessFactor": 0.3}},
]

def material_index(label, bb):
    s = (label or "").lower()
    if "bileşen13" in s or "bilesen13" in s or "namlu" in s or "launcher" in s or "barrel" in s:
        return 2
    if "kamera" in s or "camera" in s:
        return 3
    if "rulman" in s or "dişli" in s or "disli" in s or "nema" in s or "axel" in s or "bearing" in s or "motor" in s:
        return 3
    if "tabla" in s or "alt gövde" in s or "alt govde" in s or "base" in s:
        return 5
    if bb.YLength > max(bb.XLength, bb.ZLength) * 2.0 and bb.YLength > 80:
        return 2
    if "sol" in s or "sağ" in s or "sag" in s or "kapak" in s or "yan gövde" in s or "yan govde" in s or "üst" in s or "ust" in s:
        return 1
    return 0

def face_normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)

buffer = bytearray()
buffer_views = []
accessors = []
meshes = []
nodes = []
triangle_count = 0
selected_labels = []
material_usage = set()

def align4():
    while len(buffer) % 4:
        buffer.append(0)

for obj in objects:
    points, facets = obj.Shape.tessellate(tolerance)
    if not facets:
        continue
    pos_values = []
    norm_values = []
    for tri in facets:
        verts = [transform(obj, points[int(index)]) for index in tri[:3]]
        normal = face_normal(verts[0], verts[1], verts[2])
        for vert in verts:
            pos_values.extend(vert)
            norm_values.extend(normal)
    if not pos_values:
        continue

    bb = obj.Shape.BoundBox
    mat_index = material_index(getattr(obj, "Label", ""), bb)
    material_usage.add(mat_index)
    selected_labels.append(getattr(obj, "Label", "part"))
    triangle_count += len(facets)

    align4()
    pos_offset = len(buffer)
    buffer.extend(struct.pack("<" + "f" * len(pos_values), *pos_values))
    pos_length = len(buffer) - pos_offset
    align4()
    norm_offset = len(buffer)
    buffer.extend(struct.pack("<" + "f" * len(norm_values), *norm_values))
    norm_length = len(buffer) - norm_offset

    position_accessor = len(accessors)
    buffer_views.append({"buffer": 0, "byteOffset": pos_offset, "byteLength": pos_length, "target": 34962})
    vertex_count = len(pos_values) // 3
    accessors.append({
        "bufferView": len(buffer_views) - 1,
        "componentType": 5126,
        "count": vertex_count,
        "type": "VEC3",
        "min": [min(pos_values[i::3]) for i in range(3)],
        "max": [max(pos_values[i::3]) for i in range(3)],
    })
    normal_accessor = len(accessors)
    buffer_views.append({"buffer": 0, "byteOffset": norm_offset, "byteLength": norm_length, "target": 34962})
    accessors.append({
        "bufferView": len(buffer_views) - 1,
        "componentType": 5126,
        "count": vertex_count,
        "type": "VEC3",
    })

    mesh_index = len(meshes)
    meshes.append({
        "name": getattr(obj, "Label", "step_part"),
        "primitives": [{
            "attributes": {"POSITION": position_accessor, "NORMAL": normal_accessor},
            "material": mat_index,
            "mode": 4,
        }],
    })
    nodes.append({"name": getattr(obj, "Label", "step_part"), "mesh": mesh_index})

if not meshes:
    raise SystemExit("STEP tessellation produced no GLB meshes.")

glb_min = [float("inf"), float("inf"), float("inf")]
glb_max = [float("-inf"), float("-inf"), float("-inf")]
for accessor in accessors:
    if accessor.get("type") != "VEC3" or "min" not in accessor:
        continue
    for i in range(3):
        glb_min[i] = min(glb_min[i], accessor["min"][i])
        glb_max[i] = max(glb_max[i], accessor["max"][i])

def find_label_anchor(*keywords):
    best = None
    for obj in objects:
        label = getattr(obj, "Label", "").lower()
        if not all(keyword in label for keyword in keywords):
            continue
        bb = obj.Shape.BoundBox
        corners = bbox_corners(bb)
        global_corners = [globalize_point(obj, point) for point in corners]
        raw = (
            (min(point.x for point in global_corners) + max(point.x for point in global_corners)) * 0.5,
            (min(point.y for point in global_corners) + max(point.y for point in global_corners)) * 0.5,
            (min(point.z for point in global_corners) + max(point.z for point in global_corners)) * 0.5,
        )
        best = transform_raw(*raw)
        break
    return best

camera_anchor = find_label_anchor("kamera") or (-0.32, 1.05, 0.08)
launcher_anchor = find_label_anchor("bileşen13") or find_label_anchor("bilesen13") or (0.0, 0.78, -0.62)
base_anchor = (0.0, -0.42, 0.0)
target_projection_anchor = (camera_anchor[0], camera_anchor[1], camera_anchor[2] + 1.0)

gltf = {
    "asset": {"version": "2.0", "generator": "ISTIKLAL Phase 50 FreeCAD STEP converter"},
    "scene": 0,
    "scenes": [{"nodes": list(range(len(nodes)))}],
    "nodes": nodes,
    "meshes": meshes,
    "materials": materials,
    "buffers": [{"byteLength": len(buffer)}],
    "bufferViews": buffer_views,
    "accessors": accessors,
}

json_blob = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
while len(json_blob) % 4:
    json_blob += b" "
while len(buffer) % 4:
    buffer.append(0)

glb = bytearray()
total_length = 12 + 8 + len(json_blob) + 8 + len(buffer)
glb.extend(struct.pack("<III", 0x46546C67, 2, total_length))
glb.extend(struct.pack("<I4s", len(json_blob), b"JSON"))
glb.extend(json_blob)
glb.extend(struct.pack("<I4s", len(buffer), b"BIN\0"))
glb.extend(buffer)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(glb)

source_bytes = source.read_bytes()
manifest = {
    "selected_asset_type": "REAL_STEP_GLB",
    "selected_asset_path": "/assets/digital-twin/ktr1_freecad_fidelity.glb",
    "preferred_browser_asset": "/assets/digital-twin/ktr1_freecad_fidelity.glb",
    "source_asset": "work/ktr1.step",
    "source_asset_absolute": str(source),
    "output_asset": "/assets/digital-twin/ktr1_freecad_fidelity.glb",
    "output_asset_absolute": str(output),
    "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "conversion_method": "freecad_headless_step_tessellation_to_glb_global_placement_freecad_reference_material_reconstruction",
    "color_extraction_method": "STEP COLOUR_RGB records detected; FreeCAD headless did not expose per-object presentation colors, so vivid FreeCAD-reference materials were reconstructed from labels and geometry roles.",
    "conversion_status": "converted_colored_step_to_freecad_fidelity_glb",
    "material_preserved": False,
    "materials_reconstructed": True,
    "material_preservation_status": "reconstructed",
    "material_reconstruction_reason": "FreeCAD headless STEP import exposed geometry and part labels but did not expose per-face STEP presentation colors through ViewObject.DiffuseColor. STEP COLOUR_RGB presentation records were detected and the browser asset uses a FreeCAD-reference palette by part names and geometry roles.",
    "step_color_records": step_color_records,
    "freecad_reference_generated": True,
    "freecad_visual_match_estimate": "major silhouette and red/white/dark/metal/cyan material classes are represented; exact face-level STEP colors were not available through the installed FreeCAD headless API.",
    "color_count": len(material_usage),
    "material_count": len(material_usage),
    "part_count": len(objects),
    "mesh_count": len(meshes),
    "triangle_count": triangle_count,
    "triangle_count_before": triangle_count,
    "triangle_count_after": triangle_count,
    "bounding_box": {"min": glb_min, "max": glb_max},
    "scale": scene_scale,
    "rotation": {"x": 0, "y": 0, "z": 0},
    "position": {"x": 0, "y": 0, "z": 0},
    "camera_anchor": {"x": camera_anchor[0], "y": camera_anchor[1], "z": camera_anchor[2], "source": "estimated_from_kamera_part_or_manual_anchor"},
    "launcher_anchor": {"x": launcher_anchor[0], "y": launcher_anchor[1], "z": launcher_anchor[2], "source": "estimated_from_launcher_like_part_or_manual_anchor"},
    "base_anchor": {"x": base_anchor[0], "y": base_anchor[1], "z": base_anchor[2], "source": "normalized_step_bounds_floor"},
    "target_projection_anchor": {"x": target_projection_anchor[0], "y": target_projection_anchor[1], "z": target_projection_anchor[2], "source": "camera_anchor_forward_projection"},
    "asset_transform": {
        "scale": {"x": 1, "y": 1, "z": 1},
        "rotation_deg": {"x": 0, "y": 0, "z": 0},
        "position": {"x": 0, "y": 0, "z": 0},
        "camera_mount_anchor": {"x": camera_anchor[0], "y": camera_anchor[1], "z": camera_anchor[2], "source": "estimated_from_kamera_part_or_manual_anchor"},
        "launcher_axis_anchor": {"x": launcher_anchor[0], "y": launcher_anchor[1], "z": launcher_anchor[2], "source": "estimated_from_launcher_like_part_or_manual_anchor"},
        "base_anchor": {"x": base_anchor[0], "y": base_anchor[1], "z": base_anchor[2], "source": "normalized_step_bounds_floor"},
        "target_projection_anchor": {"x": target_projection_anchor[0], "y": target_projection_anchor[1], "z": target_projection_anchor[2], "source": "camera_anchor_forward_projection"},
    },
    "scale_units": "normalized_scene_units_from_step",
    "coordinate_notes": "Source STEP is imported with FreeCAD; each Part::Feature point is first transformed by getGlobalPlacement() to match FreeCAD GUI assembly placement. Scene X is STEP X, scene Y is STEP Z, scene Z is negative STEP Y. Runtime front is +Z. Anchors are estimated visualization references only.",
    "camera_mount_reference_available": True,
    "launcher_axis_reference_available": True,
    "fallback_used": False,
    "fallback_reason": None,
    "source_stl_path": None,
    "source_cad_path": "work/ktr1.step",
    "dominant_colors": [
        "warm white/light gray",
        "vivid red/dark red",
        "visible graphite",
        "bright metallic gray",
        "cyan sensor",
        "dark gray base"
    ],
    "warnings": [
        "per-face STEP color attachment unavailable in installed headless FreeCAD API",
        "materials reconstructed to match FreeCAD visual reference categories",
        "App::Part child global placements are applied before GLB export"
    ],
    "derived_web_asset_size_bytes": output.stat().st_size,
    "glb_size_bytes": output.stat().st_size,
    "sample_part_labels": selected_labels[:40],
    "no_physical_command_generated": True,
    "physical_command_enabled": False,
    "serial_tx_enabled": False,
}
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
public_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "output": str(output),
    "manifest": str(manifest_path),
    "part_count": len(objects),
    "mesh_count": len(meshes),
    "triangle_count": triangle_count,
    "color_count": len(material_usage),
    "material_preserved": False,
    "materials_reconstructed": True,
}, ensure_ascii=False))
'''


def find_freecad() -> str | None:
    candidates = [
        shutil.which("freecadcmd"),
        shutil.which("FreeCADCmd"),
        shutil.which("freecad"),
        shutil.which("FreeCAD"),
        str(Path.home() / ".local/bin/freecad"),
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)


def run_conversion(source: Path, output: Path, manifest: Path, tolerance: float) -> None:
    freecad = find_freecad()
    if not freecad:
        raise SystemExit("FreeCAD executable not found; cannot convert colored STEP without silently falling back.")
    worker = FREECAD_WORKER
    replacements = {
        "__SOURCE__": repr(str(source)),
        "__OUTPUT__": repr(str(output)),
        "__MANIFEST__": repr(str(manifest)),
        "__PUBLIC_MANIFEST__": repr(str(PUBLIC_MANIFEST)),
        "__TOLERANCE__": repr(str(tolerance)),
    }
    for key, value in replacements.items():
        worker = worker.replace(key, value)
    with tempfile.NamedTemporaryFile("w", suffix="_ktr_step_worker.py", delete=False, encoding="utf-8") as handle:
        handle.write(worker)
        worker_path = Path(handle.name)
    try:
        command = [freecad, "--console", str(worker_path)]
        result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False, timeout=600)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(f"STEP conversion failed with {freecad}: exit {result.returncode}")
        print(result.stdout.strip())
    finally:
        worker_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--tolerance", type=float, default=4.5)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    manifest = args.manifest.resolve()
    if source.suffix.lower() not in {".step", ".stp"}:
        raise SystemExit(f"Authoritative source must be STEP/STP, got: {source}")
    run_conversion(source, output, manifest, args.tolerance)


if __name__ == "__main__":
    main()
