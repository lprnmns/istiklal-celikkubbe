#!/usr/bin/env python3
"""Audit the authoritative KTR STEP asset for Phase 55 kinematics.

The audit is intentionally read-only. It imports ``work/ktr1.step`` through
FreeCAD when available, records the imported node labels, material hints,
bounding boxes, mesh statistics, and a conservative kinematic grouping
proposal. Exact mechanical pivots are not invented; when CAD hierarchy does
not expose them, the report marks the values as heuristic/manual-curation
candidates.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "work/ktr1.step"
REPORT_JSON = PROJECT_ROOT / "reports/phase55_asset_audit.json"
REPORT_MD = PROJECT_ROOT / "reports/phase55_asset_audit.md"


FREECAD_WORKER = r'''
from __future__ import annotations

import json
import math
from pathlib import Path

import FreeCAD
import Import

source = Path(__SOURCE__)
report_path = Path(__REPORT__)
tolerance = float(__TOLERANCE__)

if not source.exists():
    raise SystemExit(f"STEP source not found: {source}")

step_text = source.read_text(encoding="utf-8", errors="ignore")
doc = FreeCAD.newDocument("phase55_ktr_cad_audit")
Import.insert(str(source), doc.Name)
doc.recompute()

features = []
for obj in doc.Objects:
    if getattr(obj, "TypeId", "") != "Part::Feature":
        continue
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        continue
    bb = shape.BoundBox
    if max(bb.XLength, bb.YLength, bb.ZLength) <= 0:
        continue
    features.append(obj)

if not features:
    raise SystemExit("FreeCAD imported the STEP file but exposed no valid shape objects.")

global_min = [float("inf"), float("inf"), float("inf")]
global_max = [float("-inf"), float("-inf"), float("-inf")]
for obj in features:
    bb = obj.Shape.BoundBox
    global_min[0] = min(global_min[0], bb.XMin)
    global_min[1] = min(global_min[1], bb.YMin)
    global_min[2] = min(global_min[2], bb.ZMin)
    global_max[0] = max(global_max[0], bb.XMax)
    global_max[1] = max(global_max[1], bb.YMax)
    global_max[2] = max(global_max[2], bb.ZMax)

center = [(global_min[i] + global_max[i]) * 0.5 for i in range(3)]
extent = [global_max[i] - global_min[i] for i in range(3)]
max_extent = max(extent) or 1.0
scene_scale = 3.75 / max_extent

def transform_raw(x, y, z):
    return [
        (x - center[0]) * scene_scale,
        (z - global_min[2]) * scene_scale - 0.42,
        -(y - center[1]) * scene_scale,
    ]

def runtime_bbox(bb):
    points = [
        transform_raw(bb.XMin, bb.YMin, bb.ZMin),
        transform_raw(bb.XMin, bb.YMin, bb.ZMax),
        transform_raw(bb.XMin, bb.YMax, bb.ZMin),
        transform_raw(bb.XMin, bb.YMax, bb.ZMax),
        transform_raw(bb.XMax, bb.YMin, bb.ZMin),
        transform_raw(bb.XMax, bb.YMin, bb.ZMax),
        transform_raw(bb.XMax, bb.YMax, bb.ZMin),
        transform_raw(bb.XMax, bb.YMax, bb.ZMax),
    ]
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
    }

def color_tuple(value):
    try:
        if value is None:
            return None
        return [round(float(value[0]), 4), round(float(value[1]), 4), round(float(value[2]), 4)]
    except Exception:
        return None

def object_color(obj):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return None
    for attr in ("ShapeColor", "LineColor"):
        value = color_tuple(getattr(view, attr, None))
        if value:
            return {"source": attr, "rgb": value}
    diffuse = getattr(view, "DiffuseColor", None)
    if diffuse:
        try:
            first = diffuse[0]
            if len(first) >= 3:
                return {"source": "DiffuseColor[0]", "rgb": [round(float(first[0]), 4), round(float(first[1]), 4), round(float(first[2]), 4)]}
        except Exception:
            pass
    return None

def role_for(label, rb, cad_bb):
    low = (label or "").lower()
    size = [rb["max"][i] - rb["min"][i] for i in range(3)]
    c = [(rb["min"][i] + rb["max"][i]) * 0.5 for i in range(3)]
    frontish = c[2] < -0.18
    long_forward = size[2] > max(size[0], size[1]) * 1.55 and size[2] > 0.45
    low_part = c[1] < -0.08
    if "kamera" in low or "camera" in low:
        return "camera_group"
    if "namlu" in low or "launcher" in low or "barrel" in low or "bileşen13" in low or "bilesen13" in low or (frontish and long_forward):
        return "launcher_group"
    if "tabla" in low or "base" in low or "alt gövde" in low or "alt govde" in low or "leg" in low or "ayak" in low or low_part:
        return "static_root"
    if frontish and c[1] > 0.25:
        return "pitch_group"
    if "kapak" in low or "yan" in low or "gövde" in low or "govde" in low or "üst" in low or "ust" in low:
        return "yaw_group"
    return "yaw_group"

def visibility_for(obj):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return None
    try:
        return bool(getattr(view, "Visibility"))
    except Exception:
        return None

objects = []
group_map = {
    "static_root": [],
    "yaw_group": [],
    "pitch_group": [],
    "camera_group": [],
    "launcher_group": [],
    "decorative_static_covers": [],
}
triangle_total = 0
solid_total = 0
face_total = 0
color_values = []

for index, obj in enumerate(features):
    shape = obj.Shape
    bb = shape.BoundBox
    rb = runtime_bbox(bb)
    facets = []
    try:
        _points, facets = shape.tessellate(tolerance)
    except Exception:
        facets = []
    solids = list(getattr(shape, "Solids", []) or [])
    faces = list(getattr(shape, "Faces", []) or [])
    label = str(getattr(obj, "Label", getattr(obj, "Name", f"part_{index}")))
    role = role_for(label, rb, bb)
    node_name = label or str(getattr(obj, "Name", f"part_{index}"))
    color = object_color(obj)
    if color:
        color_values.append(color["rgb"])
    item = {
        "index": index,
        "name": str(getattr(obj, "Name", f"part_{index}")),
        "label": label,
        "type_id": str(getattr(obj, "TypeId", "")),
        "visibility": visibility_for(obj),
        "cad_bounding_box_mm": {
            "min": [bb.XMin, bb.YMin, bb.ZMin],
            "max": [bb.XMax, bb.YMax, bb.ZMax],
            "size": [bb.XLength, bb.YLength, bb.ZLength],
        },
        "runtime_bounding_box_m": rb,
        "solid_count": len(solids),
        "face_count": len(faces),
        "triangle_count_estimate": len(facets),
        "material_hint": color,
        "kinematic_group_candidate": role,
    }
    objects.append(item)
    group_map.setdefault(role, []).append(node_name)
    if role in {"camera_group", "launcher_group"}:
        group_map["pitch_group"].append(node_name)
    triangle_total += len(facets)
    solid_total += len(solids)
    face_total += len(faces)

def unique_colors(values):
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen

def center_of(labels):
    selected = [item for item in objects if item["label"] in labels]
    if not selected:
        return None
    mins = [min(item["runtime_bounding_box_m"]["min"][i] for item in selected) for i in range(3)]
    maxs = [max(item["runtime_bounding_box_m"]["max"][i] for item in selected) for i in range(3)]
    return [(mins[i] + maxs[i]) * 0.5 for i in range(3)]

static_center = center_of(group_map["static_root"]) or [0.0, -0.32, 0.0]
yaw_center = center_of(group_map["yaw_group"]) or [0.0, 0.28, 0.0]
pitch_center = center_of(group_map["pitch_group"]) or [0.0, 0.62, -0.45]
camera_center = center_of(group_map["camera_group"]) or [-0.32, 1.05, 0.08]
launcher_center = center_of(group_map["launcher_group"]) or [0.0, 0.78, -0.62]

payload = {
    "phase": 55,
    "source_step_path": str(source),
    "source_step_size_bytes": source.stat().st_size,
    "freecad_import_available": True,
    "freecad_document_object_count": len(doc.Objects),
    "shape_count": len(features),
    "solid_count": solid_total,
    "face_count": face_total,
    "mesh_count_estimate": len([item for item in objects if item["triangle_count_estimate"] > 0]),
    "triangle_count_estimate": triangle_total,
    "step_color_records": step_text.count("COLOUR_RGB"),
    "detected_colors": unique_colors(color_values),
    "material_color_access": "view_object_color_unavailable_or_partial" if not color_values else "object_view_colors_detected",
    "source_bounding_box_mm": {"min": global_min, "max": global_max, "size": extent},
    "runtime_scale": scene_scale,
    "runtime_bounding_box_m": runtime_bbox(type("BB", (), {
        "XMin": global_min[0], "YMin": global_min[1], "ZMin": global_min[2],
        "XMax": global_max[0], "YMax": global_max[1], "ZMax": global_max[2],
    })()),
    "objects": objects,
    "grouping_candidates": group_map,
    "pivot_anchor_candidates": {
        "yaw_pivot": {"position": [yaw_center[0], max(static_center[1] + 0.28, 0.0), yaw_center[2]], "method": "heuristic from yaw-group and static-root bounding boxes"},
        "pitch_pivot": {"position": pitch_center, "method": "heuristic center of front pitch/camera/launcher candidates"},
        "camera_origin": {"position": camera_center, "method": "camera label/bounding-box center or manual fallback"},
        "launcher_origin": {"position": launcher_center, "method": "launcher/long-forward part center or manual fallback"},
        "target_projection_anchor": {"position": [camera_center[0], camera_center[1], camera_center[2] + 1.0], "method": "camera origin forward projection in runtime +Z front"},
        "no_go_zone_anchor": {"position": [1.62, 0.18, 3.75], "method": "existing tactical scene visualization anchor in runtime +Z front"},
    },
    "front_launcher_camera_detail_detected": bool(group_map["launcher_group"] or group_map["camera_group"]),
    "step_import_preserves_hierarchy": False,
    "hierarchy_note": "Installed FreeCAD import exposes many Part::Feature objects with labels, but no validated revolute assembly hierarchy or joint metadata. Phase 55 creates explicit curated grouping metadata instead of claiming exact CAD kinematics.",
    "current_glb_flattening_risk": "Phase 54 GLB keeps per-object mesh/node names but does not encode yaw/pitch grouping or pivots.",
    "physical_command_enabled": False,
    "serial_tx_enabled": False,
    "no_physical_command_generated": True,
}

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"objects": len(objects), "triangles": triangle_total, "report": str(report_path)}, ensure_ascii=False))
'''


def iso_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def find_freecad() -> str | None:
    candidates = [
        shutil.which("freecadcmd"),
        shutil.which("FreeCADCmd"),
        shutil.which("freecad"),
        shutil.which("FreeCAD"),
        str(Path.home() / ".local/bin/freecad"),
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)


def inspect_glb_quick(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        return {"loads": False, "error": "not a GLB file"}
    json_len, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON":
        return {"loads": False, "error": "first GLB chunk is not JSON"}
    gltf = json.loads(data[20:20 + json_len].decode("utf-8"))
    accessors = gltf.get("accessors", [])
    triangles = 0
    for mesh in gltf.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            pos = primitive.get("attributes", {}).get("POSITION")
            if isinstance(pos, int) and pos < len(accessors):
                triangles += int(accessors[pos].get("count", 0)) // 3
    return {
        "loads": True,
        "node_count": len(gltf.get("nodes", [])),
        "mesh_count": len(gltf.get("meshes", [])),
        "material_count": len(gltf.get("materials", [])),
        "triangle_count": triangles,
    }


def inventory_files() -> list[dict[str, Any]]:
    roots = [PROJECT_ROOT / "work", PROJECT_ROOT / "frontend/public/assets/digital-twin", PROJECT_ROOT]
    skip_dirs = {".git", ".venv", "node_modules", "dist", "__pycache__", ".pytest_cache"}
    found: dict[Path, None] = {}
    for root in roots:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in skip_dirs]
            current = Path(current_root)
            if root == PROJECT_ROOT and current != PROJECT_ROOT:
                dirnames[:] = []
            for filename in filenames:
                path = current / filename
                if not path.is_file():
                    continue
                name = path.name.lower()
                if not any(keyword in name for keyword in ["ktr", "step", "stl", "glb", "operator", "twin", "cad"]):
                    continue
                if path.suffix.lower() not in {".step", ".stp", ".stl", ".str", ".glb", ".gltf", ".json"}:
                    continue
                found[path.resolve()] = None
    items: list[dict[str, Any]] = []
    for path in sorted(found):
        stat = path.stat()
        item: dict[str, Any] = {
            "path": rel(path),
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "modified_time": iso_time(stat.st_mtime),
        }
        if path.suffix.lower() == ".glb":
            try:
                item.update(inspect_glb_quick(path))
            except Exception as exc:  # pragma: no cover - diagnostics path
                item.update({"loads": False, "error": str(exc)})
        elif path.suffix.lower() in {".step", ".stp"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            item.update({
                "loads": "ISO-10303-21" in text[:2048],
                "step_color_records": text.count("COLOUR_RGB"),
                "advanced_face_count": text.count("ADVANCED_FACE"),
                "closed_shell_count": text.count("CLOSED_SHELL"),
                "manifold_solid_brep_count": text.count("MANIFOLD_SOLID_BREP"),
            })
        else:
            item["loads"] = True
        items.append(item)
    return items


def run_freecad_audit(source: Path, output_json: Path, tolerance: float) -> dict[str, Any]:
    freecad = find_freecad()
    if not freecad:
        payload = {
            "phase": 55,
            "source_step_path": rel(source),
            "freecad_import_available": False,
            "error": "FreeCAD executable not found; exact CAD audit could not run.",
            "asset_inventory": inventory_files(),
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        }
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return payload
    worker = FREECAD_WORKER
    replacements = {
        "__SOURCE__": repr(str(source.resolve())),
        "__REPORT__": repr(str(output_json.resolve())),
        "__TOLERANCE__": repr(str(tolerance)),
    }
    for key, value in replacements.items():
        worker = worker.replace(key, value)
    with tempfile.NamedTemporaryFile("w", suffix="_phase55_cad_audit.py", delete=False, encoding="utf-8") as handle:
        handle.write(worker)
        worker_path = Path(handle.name)
    try:
        result = subprocess.run([freecad, "--console", str(worker_path)], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False, timeout=600)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(f"Phase 55 FreeCAD audit failed: exit {result.returncode}")
    finally:
        worker_path.unlink(missing_ok=True)
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    payload["asset_inventory"] = inventory_files()
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def write_markdown(payload: dict[str, Any], output_md: Path) -> None:
    objects = payload.get("objects") if isinstance(payload.get("objects"), list) else []
    groups = payload.get("grouping_candidates") if isinstance(payload.get("grouping_candidates"), dict) else {}
    anchors = payload.get("pivot_anchor_candidates") if isinstance(payload.get("pivot_anchor_candidates"), dict) else {}
    inventory = payload.get("asset_inventory") if isinstance(payload.get("asset_inventory"), list) else []
    lines = [
        "# Phase 55 CAD / Asset Audit",
        "",
        f"- Source STEP: `{rel(Path(str(payload.get('source_step_path', DEFAULT_SOURCE)))) if payload.get('source_step_path') else rel(DEFAULT_SOURCE)}`",
        f"- FreeCAD import available: `{payload.get('freecad_import_available')}`",
        f"- Imported document objects: `{payload.get('freecad_document_object_count', 'n/a')}`",
        f"- Valid shape count: `{payload.get('shape_count', 'n/a')}`",
        f"- Solid count: `{payload.get('solid_count', 'n/a')}`",
        f"- Face count: `{payload.get('face_count', 'n/a')}`",
        f"- Estimated triangles: `{payload.get('triangle_count_estimate', 'n/a')}`",
        f"- STEP color records: `{payload.get('step_color_records', 'n/a')}`",
        f"- Front launcher/camera detail detected: `{payload.get('front_launcher_camera_detail_detected', False)}`",
        "",
        "## Hierarchy Finding",
        "",
        str(payload.get("hierarchy_note", "Exact assembly hierarchy was not available; grouping is heuristic/manual-curated.")),
        "",
        "## Kinematic Group Candidates",
        "",
    ]
    for group, labels in groups.items():
        sample = ", ".join(f"`{label}`" for label in list(labels)[:12])
        lines.append(f"- `{group}`: {len(labels)} nodes. {sample}")
    lines.extend(["", "## Pivot / Anchor Candidates", ""])
    for key, value in anchors.items():
        lines.append(f"- `{key}`: `{value.get('position')}` ({value.get('method')})")
    lines.extend([
        "",
        "## Part Samples",
        "",
        "| Label | Group | Runtime bbox min | Runtime bbox max | Triangles |",
        "| --- | --- | --- | --- | ---: |",
    ])
    for item in objects[:40]:
        bbox = item.get("runtime_bounding_box_m", {})
        lines.append(
            f"| `{item.get('label')}` | `{item.get('kinematic_group_candidate')}` | "
            f"`{bbox.get('min')}` | `{bbox.get('max')}` | {item.get('triangle_count_estimate', 0)} |"
        )
    lines.extend(["", "## Asset Inventory", ""])
    lines.extend(["| Path | Ext | Size | Loads | Mesh/triangles |", "| --- | --- | ---: | --- | --- |"])
    for item in inventory:
        geometry = []
        for key in ("node_count", "mesh_count", "triangle_count", "advanced_face_count"):
            if key in item:
                geometry.append(f"{key}={item[key]}")
        lines.append(f"| `{item.get('path')}` | `{item.get('extension')}` | {item.get('size_bytes')} | {item.get('loads')} | {'; '.join(geometry) or 'n/a'} |")
    lines.extend([
        "",
        "## Safety",
        "",
        "- This audit is read-only.",
        "- No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path was added.",
        "- `physical_command_enabled=false`.",
        "- `serial_tx_enabled=false`.",
        "- `no_physical_command_generated=true`.",
        "",
    ])
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--report-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    parser.add_argument("--tolerance", type=float, default=2.0)
    args = parser.parse_args()

    source = args.source.resolve()
    report_json = args.report_json.resolve()
    report_md = args.report_md.resolve()
    payload = run_freecad_audit(source, report_json, args.tolerance)
    write_markdown(payload, report_md)
    print(json.dumps({
        "source": rel(source),
        "report_json": rel(report_json),
        "report_md": rel(report_md),
        "shape_count": payload.get("shape_count"),
        "triangle_count_estimate": payload.get("triangle_count_estimate"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
