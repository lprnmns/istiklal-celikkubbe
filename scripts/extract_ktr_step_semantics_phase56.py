#!/usr/bin/env python3
"""Extract Phase 56 CAD semantics contracts for the KTR digital twin.

This script is read-only with respect to hardware. It does not create any
motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable, serial TX, or Pico command
path. The output JSON files are digital-twin authoring contracts that must be
validated against FreeCAD and the physical mechanism before they are treated as
mechanically authoritative.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "work/ktr1.step"
REPORT_DIR = PROJECT_ROOT / "reports"
ASSET_DIR = PROJECT_ROOT / "frontend/public/assets/digital-twin"

SEMANTIC_AUDIT_JSON = REPORT_DIR / "phase56_step_semantic_audit.json"
SEMANTIC_AUDIT_MD = REPORT_DIR / "phase56_step_semantic_audit.md"
ASSEMBLY_TREE_JSON = REPORT_DIR / "phase56_step_assembly_tree.json"
PART_TABLE_MD = REPORT_DIR / "phase56_part_table.md"
DEVICE_FRAME_JSON = ASSET_DIR / "ktr1_device_frame.json"
MECHANICAL_GROUPS_JSON = ASSET_DIR / "ktr1_mechanical_groups.json"
JOINT_CALIBRATION_JSON = ASSET_DIR / "ktr1_joint_calibration.json"
KINEMATICS_JSON = ASSET_DIR / "ktr1_kinematics.json"
PHASE56_RUNTIME_KINEMATICS_JSON = ASSET_DIR / "ktr1_kinematics_phase56_runtime.json"


FREECAD_WORKER = r'''
from __future__ import annotations

import json
from pathlib import Path

import FreeCAD
import Import

source = Path(__SOURCE__)
out = Path(__OUTPUT__)
tolerance = float(__TOLERANCE__)

doc = FreeCAD.newDocument("phase56_ktr_semantics")
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

def runtime_point(x, y, z):
    # Phase 56 canonical runtime frame:
    # CAD X -> runtime X, CAD Z -> runtime Y, CAD -Y -> runtime Z.
    return [
        (x - center[0]) * scene_scale,
        (z - global_min[2]) * scene_scale - 0.42,
        -(y - center[1]) * scene_scale,
    ]

def runtime_bbox(bb):
    points = [
        runtime_point(bb.XMin, bb.YMin, bb.ZMin),
        runtime_point(bb.XMin, bb.YMin, bb.ZMax),
        runtime_point(bb.XMin, bb.YMax, bb.ZMin),
        runtime_point(bb.XMin, bb.YMax, bb.ZMax),
        runtime_point(bb.XMax, bb.YMin, bb.ZMin),
        runtime_point(bb.XMax, bb.YMin, bb.ZMax),
        runtime_point(bb.XMax, bb.YMax, bb.ZMin),
        runtime_point(bb.XMax, bb.YMax, bb.ZMax),
    ]
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
        "center": [(min(point[i] for point in points) + max(point[i] for point in points)) * 0.5 for i in range(3)],
        "size": [max(point[i] for point in points) - min(point[i] for point in points) for i in range(3)],
    }

def object_color(obj):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return None
    for attr in ("ShapeColor", "LineColor"):
        value = getattr(view, attr, None)
        try:
            if value is not None and len(value) >= 3:
                return {"source": attr, "rgb": [round(float(value[0]), 4), round(float(value[1]), 4), round(float(value[2]), 4)]}
        except Exception:
            pass
    diffuse = getattr(view, "DiffuseColor", None)
    try:
        if diffuse and diffuse[0] and len(diffuse[0]) >= 3:
            return {"source": "DiffuseColor[0]", "rgb": [round(float(diffuse[0][0]), 4), round(float(diffuse[0][1]), 4), round(float(diffuse[0][2]), 4)]}
    except Exception:
        pass
    return None

def classify(label, rb):
    low = label.lower()
    center = rb["center"]
    size = rb["size"]
    front = center[2] > 0.10
    lower = center[1] < -0.06
    central_x = abs(center[0]) < 0.22
    bearing_like = "608zz" in low or "rulman" in low
    if "kamera" in low or "camera" in low:
        return "camera_assembly", "label contains camera/kamera"
    if "bileşen13" in low or "bilesen13" in low or "namlu" in low or "launcher" in low or "barrel" in low:
        return "launcher_assembly", "label identifies launcher/barrel candidate"
    if any(token in low for token in ("üst dişli", "ust disli", "sonsuz", "nema17", "grand fulffy", "axel", "ayna", "wire")):
        return "pitch_cradle", "pitch/elevation drive or cradle label"
    if any(token in low for token in ("bileşen18", "bilesen18", "bileşen19", "bilesen19", "bileşen20", "bilesen20")):
        return "yaw_rotor", "large central/side carrier body candidate"
    if low.startswith("compound") and (size[0] > 0.70 or size[1] > 0.90):
        return "yaw_rotor", "large compound cover/body candidate"
    if "tabla" in low or "base" in low or "alt gövde" in low or "alt govde" in low or "ayak" in low or lower:
        return "static_base", "base/static label or low runtime center"
    if any(token in low for token in ("üst sol", "ust sol", "sağ üst", "sag ust", "kapak", "yan gövde", "yan govde", "gövde", "govde")):
        return "yaw_rotor", "upper/side body candidate"
    if bearing_like:
        if central_x and center[1] > 0.45:
            return "yaw_rotor", "central bearing candidate near yaw ring"
        return "candidate_review_required", "bearing/fastener requires manual role validation"
    if front and center[1] > 0.15 and central_x:
        return "pitch_cradle", "front central upper part candidate"
    if front and center[1] > 0.15:
        return "yaw_rotor", "front side/cover part; rotates with yaw unless manually moved to pitch"
    return "yaw_rotor", "default moving upper assembly candidate"

parts = []
for index, obj in enumerate(features):
    shape = obj.Shape
    bb = shape.BoundBox
    rb = runtime_bbox(bb)
    facets = []
    try:
        _points, facets = shape.tessellate(tolerance)
    except Exception:
        facets = []
    label = str(getattr(obj, "Label", getattr(obj, "Name", f"part_{index}")))
    role, reason = classify(label, rb)
    parts.append({
        "index": index,
        "name": str(getattr(obj, "Name", f"part_{index}")),
        "label": label,
        "type_id": str(getattr(obj, "TypeId", "")),
        "visibility": None,
        "cad_bbox_mm": {
            "min": [bb.XMin, bb.YMin, bb.ZMin],
            "max": [bb.XMax, bb.YMax, bb.ZMax],
            "center": [(bb.XMin + bb.XMax) * 0.5, (bb.YMin + bb.YMax) * 0.5, (bb.ZMin + bb.ZMax) * 0.5],
            "size": [bb.XLength, bb.YLength, bb.ZLength],
        },
        "runtime_bbox_m": rb,
        "solid_count": len(list(getattr(shape, "Solids", []) or [])),
        "face_count": len(list(getattr(shape, "Faces", []) or [])),
        "triangle_count_estimate": len(facets),
        "freecad_view_color": object_color(obj),
        "phase56_group_candidate": role,
        "group_reason": reason,
    })

payload = {
    "source": str(source),
    "document_object_count": len(doc.Objects),
    "part_feature_count": len(features),
    "source_bbox_mm": {"min": global_min, "max": global_max, "center": center, "size": extent},
    "runtime_scale": scene_scale,
    "parts": parts,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"parts": len(parts), "output": str(out)}, ensure_ascii=False))
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


def run_freecad_extract(source: Path, output: Path, tolerance: float) -> dict[str, Any]:
    freecad = find_freecad()
    if not freecad:
        raise SystemExit("FreeCAD executable not found; cannot perform Phase 56 CAD semantic extraction.")
    worker = FREECAD_WORKER
    replacements = {
        "__SOURCE__": repr(str(source)),
        "__OUTPUT__": repr(str(output)),
        "__TOLERANCE__": repr(str(tolerance)),
    }
    for key, value in replacements.items():
        worker = worker.replace(key, value)
    with tempfile.NamedTemporaryFile("w", suffix="_phase56_freecad_worker.py", delete=False, encoding="utf-8") as handle:
        handle.write(worker)
        worker_path = Path(handle.name)
    try:
        result = subprocess.run([freecad, "--console", str(worker_path)], cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=600)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(f"FreeCAD semantic extraction failed: exit {result.returncode}")
    finally:
        worker_path.unlink(missing_ok=True)
    return json.loads(output.read_text(encoding="utf-8"))


def parse_step_records(source: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8", errors="ignore")
    product_names = sorted(set(re.findall(r"PRODUCT\s*\(\s*'([^']*)'", text)))
    color_records = re.findall(r"COLOUR_RGB\s*\(\s*'([^']*)'\s*,\s*([0-9.Ee+-]+)\s*,\s*([0-9.Ee+-]+)\s*,\s*([0-9.Ee+-]+)", text)
    return {
        "record_counts": {
            "COLOUR_RGB": text.count("COLOUR_RGB"),
            "PRESENTATION_STYLE_ASSIGNMENT": text.count("PRESENTATION_STYLE_ASSIGNMENT"),
            "MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION": text.count("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION"),
            "NEXT_ASSEMBLY_USAGE_OCCURRENCE": text.count("NEXT_ASSEMBLY_USAGE_OCCURRENCE"),
            "PRODUCT": text.count("PRODUCT"),
            "AXIS2_PLACEMENT_3D": text.count("AXIS2_PLACEMENT_3D"),
            "DIRECTION": text.count("DIRECTION"),
        },
        "product_name_count": len(product_names),
        "sample_product_names": product_names[:80],
        "color_records": [
            {"name": name, "rgb": [float(r), float(g), float(b)]}
            for name, r, g, b in color_records[:40]
        ],
    }


def group_parts(parts: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups = {
        "static_base": [],
        "yaw_rotor": [],
        "pitch_cradle": [],
        "pitch_drive": [],
        "launcher_assembly": [],
        "camera_assembly": [],
        "candidate_review_required": [],
        "decorative_covers": [],
        "unclassified": [],
    }
    for part in parts:
        label = str(part["label"])
        group = str(part.get("phase56_group_candidate", "unclassified"))
        if group not in groups:
            group = "unclassified"
        groups[group].append(label)
    for part in groups["launcher_assembly"] + groups["camera_assembly"]:
        if part not in groups["pitch_cradle"]:
            groups["pitch_cradle"].append(part)
    for part in list(groups["pitch_cradle"]):
        low = part.lower()
        if any(token in low for token in ("üst dişli", "ust disli", "sonsuz", "nema17")) and part not in groups["pitch_drive"]:
            groups["pitch_drive"].append(part)
    return groups


def center_for_labels(parts: list[dict[str, Any]], labels: list[str]) -> list[float] | None:
    selected = [part for part in parts if part["label"] in labels]
    if not selected:
        return None
    mins = [min(part["runtime_bbox_m"]["min"][i] for part in selected) for i in range(3)]
    maxs = [max(part["runtime_bbox_m"]["max"][i] for part in selected) for i in range(3)]
    return [round((mins[i] + maxs[i]) * 0.5, 5) for i in range(3)]


def center_for_first_existing(parts: list[dict[str, Any]], labels: list[str]) -> tuple[list[float] | None, str | None]:
    by_label = {str(part["label"]): part for part in parts}
    for label in labels:
        part = by_label.get(label)
        if part:
            return [round(float(value), 5) for value in part["runtime_bbox_m"]["center"]], label
    return None, None


def unique_labels(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for label in labels:
        if label in seen:
            continue
        seen.add(label)
        unique.append(label)
    return unique


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_outputs(source: Path, freecad_payload: dict[str, Any], step_payload: dict[str, Any]) -> None:
    parts = freecad_payload["parts"]
    groups = group_parts(parts)
    now = datetime.now(timezone.utc).isoformat()
    source_bbox = freecad_payload["source_bbox_mm"]
    device_frame = {
        "schema": "phase56_device_frame",
        "sourceCadPath": "work/ktr1.step",
        "createdAt": now,
        "status": "draft_requires_freecad_and_physical_validation",
        "visualizationOnly": True,
        "sourceCad": {
            "units": "mm",
            "up": "+Z",
            "front": "-Y",
            "right": "+X",
            "frontDecision": "Camera/launcher candidates are at negative CAD Y; user FreeCAD screenshots show weapon/front in that direction.",
        },
        "runtimeWorld": {
            "units": "m_normalized",
            "up": "+Y",
            "front": "+Z",
            "right": "+X",
            "transform": "runtimeX=CAD X, runtimeY=CAD Z, runtimeZ=-CAD Y",
        },
        "canonicalViews": {
            "frontWeapon": {"lookDirectionRuntime": [0, 0, -1], "description": "Camera looking toward the device from runtime +Z/front side."},
            "rear": {"lookDirectionRuntime": [0, 0, 1]},
            "left": {"lookDirectionRuntime": [1, 0, 0]},
            "right": {"lookDirectionRuntime": [-1, 0, 0]},
            "top": {"lookDirectionRuntime": [0, -1, 0]},
            "operator": {"lookDirectionRuntime": [-0.25, -0.35, -1]},
        },
        "sourceBoundingBoxMm": source_bbox,
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }

    yaw_axis_center, yaw_axis_source = center_for_first_existing(parts, ["tabla", "alt gövde", "alt govde"])
    if yaw_axis_center:
        # The yaw axis is vertical in runtime (+Y). The Y coordinate is arbitrary
        # along that axis, so use the base/table X/Z center and normalize Y to 0
        # for stable visualization.
        yaw_axis_center[1] = 0.0
    yaw_center = yaw_axis_center or center_for_labels(parts, groups["yaw_rotor"]) or [0, 0.8, 0]
    pitch_axis_center, pitch_axis_source = center_for_first_existing(parts, ["Axel", "Bileşen5(Ayna)", "Bilesen5(Ayna)"])
    if pitch_axis_center:
        # The pitch axis is parallel to runtime X. The X coordinate is arbitrary
        # along that axis, so normalize it to the device centerline for clearer
        # visualization and reporting while preserving the measured Y/Z axis line.
        pitch_axis_center[0] = 0.0
    pitch_center = pitch_axis_center or center_for_labels(parts, groups["pitch_cradle"]) or [0, 0.7, 0.9]
    camera_center = center_for_labels(parts, groups["camera_assembly"]) or [0.5, 0.73, 1.03]
    launcher_center = center_for_labels(parts, groups["launcher_assembly"]) or [-0.3, 0.68, 1.26]
    mechanical_groups = {
        "schema": "phase56_mechanical_groups",
        "sourceCadPath": "work/ktr1.step",
        "status": "draft_manual_validation_required",
        "groupingMethod": "FreeCAD labels + bbox/front-axis heuristics; not accepted as final mechanical truth until validated",
        "groups": groups,
        "counts": {key: len(value) for key, value in groups.items()},
        "validationRequired": [
            "Confirm static_base parts do not rotate with yaw.",
            "Confirm yaw_rotor contains every part moved by X/azimuth step motor.",
            "Confirm pitch_cradle contains every part moved by Y/elevation step motor.",
            "Confirm launcher_assembly and camera_assembly are physically attached to pitch_cradle.",
        ],
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }
    joint_calibration = {
        "schema": "phase56_joint_calibration",
        "sourceCadPath": "work/ktr1.step",
        "status": "draft_requires_manual_pick_or_physical_measurement",
        "visualizationOnly": True,
        "joints": {
            "yaw": {
                "physicalMotor": "X/azimuth step motor",
                "pivot": yaw_center,
                "axisRuntime": [0, 1, 0],
                "limitsDeg": [-180, 180],
                "stepToDegree": None,
                "source": (
                    f"base/table part `{yaw_axis_source}` X/Z center with Y normalized to yaw axis"
                    if yaw_axis_source
                    else "bbox center draft; replace with bearing/shaft centerline"
                ),
            },
            "pitch": {
                "physicalMotor": "Y/elevation step motor",
                "pivot": pitch_center,
                "axisRuntime": [1, 0, 0],
                "limitsDeg": [-10, 75],
                "stepToDegree": None,
                "source": (
                    f"candidate shaft/axis part `{pitch_axis_source}` bbox Y/Z with X normalized to centerline"
                    if pitch_axis_source
                    else "pitch_cradle bbox center draft; replace with elevation shaft centerline"
                ),
            },
        },
        "anchors": {
            "camera_origin": {"position": camera_center, "axisRuntime": [0, 0, 1], "source": "camera part bbox center draft"},
            "launcher_origin": {"position": launcher_center, "axisRuntime": [0, 0, 1], "source": "launcher part bbox center draft"},
            "target_projection_anchor": {"position": [camera_center[0], camera_center[1], round(camera_center[2] + 1.0, 5)], "source": "front-axis camera ray draft"},
            "no_go_zone_anchor": {"position": [0, 0, 0], "source": "not calibrated"},
        },
        "offsets": {
            "camera_to_launcher_mm": [30, 0, 0],
            "status": "contract value; must be verified against CAD/physical measurement",
        },
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }
    runtime_kinematics = {
        "assetVersion": "phase55",
        "phase56Refinement": {
            "enabled": True,
            "sourceContracts": [
                "/assets/digital-twin/ktr1_device_frame.json",
                "/assets/digital-twin/ktr1_mechanical_groups.json",
                "/assets/digital-twin/ktr1_joint_calibration.json",
            ],
            "status": "draft_manual_validation_required",
        },
        "visualizationOnly": True,
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
        "source": {
            "cadPath": "work/ktr1.step",
            "cadSizeBytes": source.stat().st_size,
            "glbPath": "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
            "kinematicsPath": "/assets/digital-twin/ktr1_kinematics.json",
            "unitsSource": "mm",
            "unitsRuntime": "m",
        },
        "coordinateSystems": {
            "sourceCad": {"up": "+Z", "front": "-Y", "right": "+X"},
            "runtimeWorld": {"up": "+Y", "front": "+Z", "right": "+X"},
            "rootCorrectionEulerDeg": [-90, 0, 0],
            "conversionNote": "Runtime GLB coordinates use X=CAD X, Y=CAD Z, Z=-CAD Y; this contract makes front +Z explicit.",
        },
        "nodes": {
            "root": "ktr1_root",
            "staticRoot": "static_root",
            "yawPivot": "yaw_pivot",
            "yawGroup": "yaw_group",
            "pitchPivot": "pitch_pivot",
            "pitchGroup": "pitch_group",
            "cameraOrigin": "camera_origin",
            "cameraAxis": "camera_axis",
            "launcherOrigin": "launcher_origin",
            "launcherAxis": "launcher_axis",
            "targetProjectionAnchor": "target_projection_anchor",
            "noGoZoneAnchor": "no_go_zone_anchor",
        },
        "groups": {
            "static_root": unique_labels(groups["static_base"]),
            "yaw_group": unique_labels(groups["yaw_rotor"] + groups["candidate_review_required"]),
            "pitch_group": unique_labels(groups["pitch_cradle"] + groups["pitch_drive"]),
            "camera_group": unique_labels(groups["camera_assembly"]),
            "launcher_group": unique_labels(groups["launcher_assembly"]),
            "decorative_static_covers": unique_labels(groups["decorative_covers"]),
        },
        "manualOverrideMap": {
            "notes": "Phase 56 refined from FreeCAD labels and bbox diagnostics. Candidate bearings/fasteners default to yaw_group for preview but remain manually reviewable in ktr1_mechanical_groups.json.",
            "cameraKeywords": ["kamera", "camera"],
            "launcherKeywords": ["namlu", "launcher", "barrel", "bileşen13", "bilesen13"],
            "staticKeywords": ["tabla", "base", "alt gövde", "alt govde", "leg", "ayak"],
            "pitchKeywords": ["üst dişli", "ust disli", "sonsuz", "nema17", "grand fulffy", "axel", "ayna", "wire"],
        },
        "pivots": {
            "yaw_pivot": {
                "position": joint_calibration["joints"]["yaw"]["pivot"],
                "axis": joint_calibration["joints"]["yaw"]["axisRuntime"],
                "source": joint_calibration["joints"]["yaw"]["source"],
            },
            "pitch_pivot": {
                "position": joint_calibration["joints"]["pitch"]["pivot"],
                "axis": joint_calibration["joints"]["pitch"]["axisRuntime"],
                "source": joint_calibration["joints"]["pitch"]["source"],
            },
        },
        "anchors": {
            "camera_origin": {
                "position": joint_calibration["anchors"]["camera_origin"]["position"],
                "direction": joint_calibration["anchors"]["camera_origin"]["axisRuntime"],
                "source": joint_calibration["anchors"]["camera_origin"]["source"],
            },
            "camera_axis": {"originNode": "camera_origin", "direction": joint_calibration["anchors"]["camera_origin"]["axisRuntime"]},
            "launcher_origin": {
                "position": joint_calibration["anchors"]["launcher_origin"]["position"],
                "direction": joint_calibration["anchors"]["launcher_origin"]["axisRuntime"],
                "source": joint_calibration["anchors"]["launcher_origin"]["source"],
            },
            "launcher_axis": {"originNode": "launcher_origin", "direction": joint_calibration["anchors"]["launcher_origin"]["axisRuntime"]},
            "target_projection_anchor": joint_calibration["anchors"]["target_projection_anchor"],
            "no_go_zone_anchor": joint_calibration["anchors"]["no_go_zone_anchor"],
        },
        "joints": {
            "yaw_joint": {
                "type": "revolute",
                "pivotNode": "yaw_pivot",
                "axis": joint_calibration["joints"]["yaw"]["axisRuntime"],
                "limitsDeg": joint_calibration["joints"]["yaw"]["limitsDeg"],
                "defaultDeg": 0,
                "previewRangeDeg": [-45, 45],
                "visualizationOnly": True,
            },
            "pitch_joint": {
                "type": "revolute",
                "pivotNode": "pitch_pivot",
                "axis": joint_calibration["joints"]["pitch"]["axisRuntime"],
                "limitsDeg": joint_calibration["joints"]["pitch"]["limitsDeg"],
                "defaultDeg": 0,
                "previewRangeDeg": [-10, 45],
                "visualizationOnly": True,
            },
        },
        "offsets": {
            "camera_to_launcher_mm": joint_calibration["offsets"]["camera_to_launcher_mm"],
            "source": "Phase 56 projection contract; visualization-only annotation",
        },
        "viewPresets": {
            "freecadMatch": {"view": "freecad"},
            "operator": {"view": "operator"},
            "frontWeaponCloseup": {"view": "weaponCloseup"},
            "side": {"view": "side"},
            "topDown": {"view": "top"},
            "cameraPOV": {"view": "camera"},
            "launcherAxisPOV": {"view": "chase"},
            "targetPOV": {"view": "target"},
            "reset": {"view": "freecad"},
        },
        "validation": {
            "exact_step_hierarchy_preserved": False,
            "hierarchy_preservation_note": "FreeCAD provided stable Part::Feature labels but no validated revolute assembly hierarchy.",
            "yaw_preview_available": True,
            "pitch_preview_available": True,
            "front_weapon_inspection_presets": ["weapon", "weaponCloseup"],
            "visualization_only_preview_controls": True,
            "phase56_candidate_review_required_count": len(groups["candidate_review_required"]),
        },
    }
    assembly_tree = {
        "schema": "phase56_step_assembly_tree",
        "sourceCadPath": "work/ktr1.step",
        "status": "partial",
        "reason": "FreeCAD import exposed flat Part::Feature objects; STEP text contains assembly records but this script has not resolved full XDE product occurrence transforms.",
        "stepRecordSummary": step_payload,
        "flatFreecadParts": [
            {
                "label": part["label"],
                "name": part["name"],
                "groupCandidate": part["phase56_group_candidate"],
                "cadBBoxMm": part["cad_bbox_mm"],
                "runtimeBBoxM": part["runtime_bbox_m"],
                "triangleCountEstimate": part["triangle_count_estimate"],
                "freecadViewColor": part["freecad_view_color"],
            }
            for part in parts
        ],
        "nextRequiredExtraction": "Use OCCT XDE STEPCAFControl_Reader or a FreeCAD macro that resolves product occurrence tree and colors.",
    }
    semantic_audit = {
        "schema": "phase56_step_semantic_audit",
        "sourceCadPath": "work/ktr1.step",
        "sourceAbsolutePath": str(source),
        "createdAt": now,
        "freecad": {
            "documentObjectCount": freecad_payload["document_object_count"],
            "partFeatureCount": freecad_payload["part_feature_count"],
            "runtimeScale": freecad_payload["runtime_scale"],
        },
        "step": step_payload,
        "diagnosis": {
            "sourceGeometryPresent": True,
            "browserMismatchPrimaryCause": "CAD assembly/material/joint semantics are not preserved into the GLB/runtime contracts.",
            "webRendererCapacityIsPrimaryCause": False,
            "exactAssemblyTreeAvailable": False,
            "materialsPreserved": False,
            "kinematicTruthStatus": "draft_not_mechanically_validated",
        },
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }

    write_json(DEVICE_FRAME_JSON, device_frame)
    write_json(MECHANICAL_GROUPS_JSON, mechanical_groups)
    write_json(JOINT_CALIBRATION_JSON, joint_calibration)
    write_json(KINEMATICS_JSON, runtime_kinematics)
    write_json(PHASE56_RUNTIME_KINEMATICS_JSON, runtime_kinematics)
    write_json(ASSEMBLY_TREE_JSON, assembly_tree)
    write_json(SEMANTIC_AUDIT_JSON, semantic_audit)
    write_markdown_reports(semantic_audit, assembly_tree, mechanical_groups, joint_calibration)


def write_markdown_reports(
    semantic_audit: dict[str, Any],
    assembly_tree: dict[str, Any],
    mechanical_groups: dict[str, Any],
    joint_calibration: dict[str, Any],
) -> None:
    SEMANTIC_AUDIT_MD.write_text(
        "\n".join([
            "# Phase 56 STEP Semantic Audit",
            "",
            f"- Source: `{semantic_audit['sourceCadPath']}`",
            f"- FreeCAD part features: `{semantic_audit['freecad']['partFeatureCount']}`",
            f"- STEP assembly records: `{semantic_audit['step']['record_counts']['NEXT_ASSEMBLY_USAGE_OCCURRENCE']}`",
            f"- STEP color records: `{semantic_audit['step']['record_counts']['COLOUR_RGB']}`",
            f"- Exact assembly tree available: `{semantic_audit['diagnosis']['exactAssemblyTreeAvailable']}`",
            f"- Materials preserved: `{semantic_audit['diagnosis']['materialsPreserved']}`",
            "",
            "## Diagnosis",
            "",
            semantic_audit["diagnosis"]["browserMismatchPrimaryCause"],
            "",
            "The source geometry is present. The current blocker is CAD semantic extraction: hierarchy, colors, validated joints, pivots and canonical device frame.",
            "",
            "## Safety",
            "",
            "- `physical_command_enabled=false`",
            "- `serial_tx_enabled=false`",
            "- `no_physical_command_generated=true`",
            "",
        ]),
        encoding="utf-8",
    )
    lines = [
        "# Phase 56 Part Table",
        "",
        "| # | Label | Group candidate | Tris | Runtime center | Runtime size | Color |",
        "|---:|---|---|---:|---|---|---|",
    ]
    for index, part in enumerate(assembly_tree["flatFreecadParts"]):
        bbox = part["runtimeBBoxM"]
        color = part["freecadViewColor"]
        color_text = "n/a" if not color else f"{color.get('source')} {color.get('rgb')}"
        lines.append(
            f"| {index} | `{part['label']}` | `{part['groupCandidate']}` | {part['triangleCountEstimate']} | "
            f"`{[round(v, 4) for v in bbox['center']]}` | `{[round(v, 4) for v in bbox['size']]}` | `{color_text}` |"
        )
    PART_TABLE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    REPORT_DIR.joinpath("phase56_mechanical_grouping.md").write_text(
        "\n".join([
            "# Phase 56 Mechanical Grouping Draft",
            "",
            "This is a draft grouping contract. It is not final mechanical truth until checked against the physical X/Y step motor mechanism and FreeCAD part selection.",
            "",
            *[f"- `{key}`: {len(value)} parts" for key, value in mechanical_groups["groups"].items()],
            "",
            "## Required Manual Validation",
            "",
            *[f"- {item}" for item in mechanical_groups["validationRequired"]],
            "",
            "## Safety",
            "",
            "- Visualization-only.",
            "- No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path.",
            "- No serial TX.",
            "- No Pico command sending.",
            "",
        ]),
        encoding="utf-8",
    )
    REPORT_DIR.joinpath("phase56_joint_anchor_calibration.md").write_text(
        "\n".join([
            "# Phase 56 Joint and Anchor Calibration Draft",
            "",
            "The values below are draft runtime coordinates. They must be replaced or confirmed by CAD shaft/axis picking and physical measurement.",
            "",
            f"- Yaw pivot: `{joint_calibration['joints']['yaw']['pivot']}` source `{joint_calibration['joints']['yaw']['source']}`",
            f"- Pitch pivot: `{joint_calibration['joints']['pitch']['pivot']}` source `{joint_calibration['joints']['pitch']['source']}`",
            f"- Camera origin: `{joint_calibration['anchors']['camera_origin']['position']}` axis `{joint_calibration['anchors']['camera_origin']['axisRuntime']}`",
            f"- Launcher origin: `{joint_calibration['anchors']['launcher_origin']['position']}` axis `{joint_calibration['anchors']['launcher_origin']['axisRuntime']}`",
            "",
            "## Safety",
            "",
            "- Preview/calibration only.",
            "- No physical commands are generated.",
            "",
        ]),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--tolerance", type=float, default=1.2)
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"STEP source not found: {source}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    temp_json = REPORT_DIR / "_phase56_freecad_parts_tmp.json"
    freecad_payload = run_freecad_extract(source, temp_json, args.tolerance)
    temp_json.unlink(missing_ok=True)
    step_payload = parse_step_records(source)
    write_outputs(source, freecad_payload, step_payload)
    print(json.dumps({
        "semantic_audit": str(SEMANTIC_AUDIT_JSON.relative_to(PROJECT_ROOT)),
        "assembly_tree": str(ASSEMBLY_TREE_JSON.relative_to(PROJECT_ROOT)),
        "device_frame": str(DEVICE_FRAME_JSON.relative_to(PROJECT_ROOT)),
        "mechanical_groups": str(MECHANICAL_GROUPS_JSON.relative_to(PROJECT_ROOT)),
        "joint_calibration": str(JOINT_CALIBRATION_JSON.relative_to(PROJECT_ROOT)),
        "runtime_kinematics": str(KINEMATICS_JSON.relative_to(PROJECT_ROOT)),
        "phase56_runtime_kinematics": str(PHASE56_RUNTIME_KINEMATICS_JSON.relative_to(PROJECT_ROOT)),
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
