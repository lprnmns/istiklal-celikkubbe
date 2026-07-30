#!/usr/bin/env python3
"""Export the Phase 55 kinematic KTR GLB and kinematics metadata.

Blender authoring is used only when available. In this environment the reliable
path is FreeCAD STEP tessellation with stable per-part node names, followed by
explicit kinematic metadata in ``ktr1_kinematics.json``. This script does not
create or enable any hardware command path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from audit_ktr_cad_phase55 import REPORT_JSON as AUDIT_JSON
from convert_ktr_step_to_glb import PROJECT_ROOT, run_conversion


DEFAULT_SOURCE = PROJECT_ROOT / "work/ktr1.step"
ASSET_DIR = PROJECT_ROOT / "frontend/public/assets/digital-twin"
DEFAULT_OUTPUT = ASSET_DIR / "ktr1_kinematic_world_phase55.glb"
DEFAULT_MANIFEST = ASSET_DIR / "ktr1_kinematic_world_phase55_manifest.json"
DEFAULT_KINEMATICS = ASSET_DIR / "ktr1_kinematics.json"
PUBLIC_MANIFEST = ASSET_DIR / "asset_manifest.json"
BLENDER_REPORT = PROJECT_ROOT / "reports/phase55_blender_authoring.md"
GROUPING_REPORT = PROJECT_ROOT / "reports/phase55_kinematic_grouping.md"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def public_asset_path(path: Path) -> str:
    return "/" + str(path.resolve().relative_to(PROJECT_ROOT / "frontend/public"))


def run_audit_if_needed(source: Path) -> dict[str, Any]:
    if not AUDIT_JSON.exists():
        subprocess.run(["python3", "scripts/audit_ktr_cad_phase55.py", "--source", str(source)], cwd=PROJECT_ROOT, check=True)
    payload = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    if str(payload.get("source_step_path", "")).endswith(str(source.name)):
        return payload
    subprocess.run(["python3", "scripts/audit_ktr_cad_phase55.py", "--source", str(source)], cwd=PROJECT_ROOT, check=True)
    return json.loads(AUDIT_JSON.read_text(encoding="utf-8"))


def first_anchor(payload: dict[str, Any], key: str, fallback: list[float]) -> list[float]:
    candidates = payload.get("pivot_anchor_candidates")
    if not isinstance(candidates, dict):
        return fallback
    item = candidates.get(key)
    if not isinstance(item, dict):
        return fallback
    position = item.get("position")
    if not isinstance(position, list) or len(position) < 3:
        return fallback
    return [round(float(position[0]), 5), round(float(position[1]), 5), round(float(position[2]), 5)]


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def groups_from_audit(payload: dict[str, Any]) -> dict[str, list[str]]:
    raw = payload.get("grouping_candidates")
    groups: dict[str, list[str]] = {
        "static_root": [],
        "yaw_group": [],
        "pitch_group": [],
        "camera_group": [],
        "launcher_group": [],
        "decorative_static_covers": [],
    }
    if isinstance(raw, dict):
        for key in groups:
            value = raw.get(key, [])
            if isinstance(value, list):
                groups[key] = unique([str(item) for item in value])
    objects = payload.get("objects")
    if isinstance(objects, list):
        labels = [str(item.get("label")) for item in objects if item.get("label")]
        if not groups["yaw_group"]:
            groups["yaw_group"] = labels
        for item in objects:
            label = str(item.get("label", ""))
            role = str(item.get("kinematic_group_candidate", ""))
            if role in groups and label not in groups[role]:
                groups[role].append(label)
    for group in ("camera_group", "launcher_group"):
        for label in groups[group]:
            if label not in groups["pitch_group"]:
                groups["pitch_group"].append(label)
    pitch_set = set(groups["pitch_group"])
    static_set = set(groups["static_root"])
    groups["yaw_group"] = unique([label for label in groups["yaw_group"] if label not in static_set and label not in pitch_set])
    return {key: unique(value) for key, value in groups.items()}


def write_blender_report() -> bool:
    blender = shutil.which("blender")
    BLENDER_REPORT.parent.mkdir(parents=True, exist_ok=True)
    if not blender:
        BLENDER_REPORT.write_text(
            "\n".join([
                "# Phase 55 Blender Authoring",
                "",
                "Result: Blender is not installed in this environment, so Phase 55 did not create Blender-authored empties inside the GLB.",
                "",
                "Fallback authoring path:",
                "- FreeCAD imports `work/ktr1.step` and exports a high-fidelity GLB with stable per-part node names.",
                "- `frontend/public/assets/digital-twin/ktr1_kinematics.json` declares visualization-only groups, pivots and anchors.",
                "- The Three.js runtime creates `static_root`, `yaw_pivot`, `yaw_group`, `pitch_pivot`, `pitch_group`, `camera_group`, and `launcher_group` at load time.",
                "",
                "Manual Blender pass TODO:",
                "- Install Blender with CAD import support.",
                "- Import the Phase 55 GLB or original STEP-derived mesh.",
                "- Add empties named `yaw_pivot`, `pitch_pivot`, `camera_origin`, `camera_axis`, `launcher_origin`, `launcher_axis`, `target_projection_anchor`, and `no_go_zone_anchor`.",
                "- Parent meshes into static/yaw/pitch/camera/launcher groups and re-export GLB.",
                "",
                "Safety: this is visualization-only authoring. No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path, serial TX, or Pico command sender is added.",
                "",
            ]),
            encoding="utf-8",
        )
        return False
    BLENDER_REPORT.write_text(
        "\n".join([
            "# Phase 55 Blender Authoring",
            "",
            f"Blender executable detected at `{blender}`.",
            "",
            "This automated pass still uses FreeCAD for STEP tessellation because the installed Blender CAD importer availability is not guaranteed. The generated GLB keeps stable part node names, and `ktr1_kinematics.json` supplies runtime pivots and grouping.",
            "",
            "Safety: visualization-only; no physical command path added.",
            "",
        ]),
        encoding="utf-8",
    )
    return True


def write_kinematics(payload: dict[str, Any], output: Path, glb: Path) -> dict[str, Any]:
    groups = groups_from_audit(payload)
    yaw_pivot = first_anchor(payload, "yaw_pivot", [0.0, 0.35, 0.0])
    pitch_pivot = first_anchor(payload, "pitch_pivot", [0.0, 0.72, -0.52])
    camera_origin = first_anchor(payload, "camera_origin", [-0.32, 1.05, 0.08])
    launcher_origin = first_anchor(payload, "launcher_origin", [0.0, 0.78, -0.62])
    target_anchor = first_anchor(payload, "target_projection_anchor", [camera_origin[0], camera_origin[1], camera_origin[2] + 1.0])
    no_go_anchor = first_anchor(payload, "no_go_zone_anchor", [1.62, 0.18, 3.75])
    source_size = DEFAULT_SOURCE.resolve().stat().st_size if DEFAULT_SOURCE.exists() else None
    kinematics: dict[str, Any] = {
        "assetVersion": "phase55",
        "visualizationOnly": True,
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
        "source": {
            "cadPath": "work/ktr1.step",
            "cadSizeBytes": source_size,
            "glbPath": public_asset_path(glb),
            "kinematicsPath": "/assets/digital-twin/ktr1_kinematics.json",
            "unitsSource": "mm",
            "unitsRuntime": "m",
        },
        "coordinateSystems": {
            "sourceCad": {"up": "+Z", "front": "-Y", "right": "+X"},
            "runtimeWorld": {"up": "+Y", "front": "+Z", "right": "+X"},
            "rootCorrectionEulerDeg": [-90, 0, 0],
            "conversionNote": "The GLB positions are already converted as X=CAD X, Y=CAD Z, Z=-CAD Y; runtime front is +Z and root correction is documented but not reapplied at runtime.",
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
        "groups": groups,
        "manualOverrideMap": {
            "notes": "Exact STEP revolute assembly hierarchy is not exposed by the installed FreeCAD import. These aliases are heuristically curated from labels and bounding boxes and must be revised after mechanical validation.",
            "cameraKeywords": ["kamera", "camera"],
            "launcherKeywords": ["namlu", "launcher", "barrel", "bileşen13", "bilesen13"],
            "staticKeywords": ["tabla", "base", "alt gövde", "alt govde", "leg", "ayak"],
        },
        "pivots": {
            "yaw_pivot": {"position": yaw_pivot, "axis": [0, 1, 0], "source": "phase55_audit_bbox_heuristic"},
            "pitch_pivot": {"position": pitch_pivot, "axis": [1, 0, 0], "source": "phase55_audit_front_group_bbox_heuristic"},
        },
        "anchors": {
            "camera_origin": {"position": camera_origin, "direction": [0, 0, 1], "source": "camera label or manual fallback"},
            "camera_axis": {"originNode": "camera_origin", "direction": [0, 0, 1]},
            "launcher_origin": {"position": launcher_origin, "direction": [0, 0, 1], "source": "launcher label/long-forward geometry or manual fallback"},
            "launcher_axis": {"originNode": "launcher_origin", "direction": [0, 0, 1]},
            "target_projection_anchor": {"position": target_anchor, "source": "camera origin forward projection"},
            "no_go_zone_anchor": {"position": no_go_anchor, "source": "existing visualization no-go volume anchor"},
        },
        "joints": {
            "yaw_joint": {
                "type": "revolute",
                "pivotNode": "yaw_pivot",
                "axis": [0, 1, 0],
                "limitsDeg": [-180, 180],
                "defaultDeg": 0,
                "previewRangeDeg": [-45, 45],
                "visualizationOnly": True,
            },
            "pitch_joint": {
                "type": "revolute",
                "pivotNode": "pitch_pivot",
                "axis": [1, 0, 0],
                "limitsDeg": [-10, 75],
                "defaultDeg": 0,
                "previewRangeDeg": [-10, 45],
                "visualizationOnly": True,
            },
        },
        "offsets": {
            "camera_to_launcher_mm": [30, 0, 0],
            "source": "Phase 35-55 cockpit projection contract; visualization-only annotation",
        },
        "viewPresets": {
            "freecadMatch": {"view": "freecad", "description": "Orthographic CAD-like full silhouette"},
            "operator": {"view": "operator", "description": "3/4 operator view"},
            "frontWeaponCloseup": {"view": "weaponCloseup", "description": "Front launcher/camera closeup"},
            "side": {"view": "side"},
            "topDown": {"view": "top"},
            "cameraPOV": {"view": "camera"},
            "launcherAxisPOV": {"view": "chase"},
            "targetPOV": {"view": "target"},
            "reset": {"view": "freecad"},
        },
        "validation": {
            "exact_step_hierarchy_preserved": False,
            "hierarchy_preservation_note": "FreeCAD provided stable Part::Feature labels but no validated joint hierarchy.",
            "yaw_preview_available": True,
            "pitch_preview_available": True,
            "front_weapon_inspection_presets": ["weapon", "weaponCloseup"],
            "visualization_only_preview_controls": True,
        },
    }
    output.write_text(json.dumps(kinematics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return kinematics


def patch_manifest(manifest_path: Path, glb_path: Path, kinematics_path: Path, audit_payload: dict[str, Any], blender_used: bool) -> dict[str, Any]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    glb_asset = public_asset_path(glb_path)
    data.update({
        "phase": 55,
        "selected_asset_type": "REAL_STEP_KINEMATIC_GLB",
        "selected_asset_path": glb_asset,
        "preferred_browser_asset": glb_asset,
        "output_asset": glb_asset,
        "output_asset_absolute": str(glb_path),
        "kinematics_path": "/assets/digital-twin/ktr1_kinematics.json",
        "kinematic_metadata": "/assets/digital-twin/ktr1_kinematics.json",
        "conversion_method": "freecad_headless_step_tessellation_plus_phase55_kinematic_metadata",
        "conversion_status": "phase55_kinematic_step_glb_with_runtime_pivots",
        "blender_used": blender_used,
        "exact_step_hierarchy_preserved": False,
        "step_hierarchy_note": "Stable part names preserved; mechanical joint hierarchy inferred and curated in kinematics JSON.",
        "kinematic_grouping_report": "reports/phase55_kinematic_grouping.md",
        "asset_audit_report": "reports/phase55_asset_audit.md",
        "yaw_preview_available": True,
        "pitch_preview_available": True,
        "visualizationOnly": True,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
        "no_physical_command_generated": True,
    })
    if DEFAULT_SOURCE.exists():
        data["source_cad_sha256"] = hashlib.sha256(DEFAULT_SOURCE.read_bytes()).hexdigest()
    for key in ("shape_count", "solid_count", "face_count", "front_launcher_camera_detail_detected"):
        if key in audit_payload:
            data[key] = audit_payload[key]
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PUBLIC_MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def write_grouping_report(kinematics: dict[str, Any], manifest: dict[str, Any]) -> None:
    groups = kinematics["groups"]
    anchors = kinematics["anchors"]
    pivots = kinematics["pivots"]
    lines = [
        "# Phase 55 Kinematic Grouping",
        "",
        "This report defines the visualization-only kinematic digital twin grouping for `work/ktr1.step`.",
        "",
        "Important honesty note: the installed FreeCAD import preserved many named parts but did not expose a validated mechanical joint hierarchy. The groups below are derived from labels, bounding boxes and geometry roles, then used only for browser preview. They are not hardware commands.",
        "",
        f"- Generated GLB: `{manifest.get('selected_asset_path')}`",
        f"- Kinematics JSON: `{kinematics['source']['kinematicsPath']}`",
        f"- Exact STEP hierarchy preserved: `{manifest.get('exact_step_hierarchy_preserved')}`",
        "",
        "## Groups",
        "",
    ]
    for group, labels in groups.items():
        sample = ", ".join(f"`{label}`" for label in labels[:18])
        lines.append(f"- `{group}`: {len(labels)} nodes. {sample}")
    lines.extend(["", "## Pivots", ""])
    for key, value in pivots.items():
        lines.append(f"- `{key}`: position `{value['position']}`, axis `{value['axis']}`, source `{value['source']}`")
    lines.extend(["", "## Anchors", ""])
    for key, value in anchors.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Runtime Behavior",
        "",
        "- Three.js loads the flat GLB node list, reparents nodes into runtime `static_root`, `yaw_pivot`, `yaw_group`, `pitch_pivot`, and `pitch_group` containers, then applies visualization-only preview rotations.",
        "- Camera and launcher anchors remain in the pitch group, so the 30 mm offset, FOV, and target projection move rigidly during preview.",
        "- Yaw/pitch sliders do not call backend APIs and do not send Pico, motor, fire, servo, GPIO, PWM, STEP/DIR, serial TX, or hardware-enable commands.",
        "",
        "## Safety",
        "",
        "- `physical_command_enabled=false`",
        "- `serial_tx_enabled=false`",
        "- `no_physical_command_generated=true`",
        "",
    ])
    GROUPING_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--kinematics", type=Path, default=DEFAULT_KINEMATICS)
    parser.add_argument("--tolerance", type=float, default=1.2)
    parser.add_argument("--skip-conversion", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    manifest = args.manifest.resolve()
    kinematics_path = args.kinematics.resolve()
    audit_payload = run_audit_if_needed(source)
    blender_used = write_blender_report()
    if not args.skip_conversion or not output.exists():
        run_conversion(source, output, manifest, args.tolerance)
    kinematics = write_kinematics(audit_payload, kinematics_path, output)
    manifest_data = patch_manifest(manifest, output, kinematics_path, audit_payload, blender_used)
    write_grouping_report(kinematics, manifest_data)
    print(json.dumps({
        "output": rel(output),
        "manifest": rel(manifest),
        "kinematics": rel(kinematics_path),
        "blender_used": blender_used,
        "triangles": manifest_data.get("triangle_count"),
        "selected_asset_type": manifest_data.get("selected_asset_type"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
