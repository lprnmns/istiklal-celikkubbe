#!/usr/bin/env python3
"""Check Phase 56 runtime GLB node coverage against kinematic groups.

This is a read-only asset inspection script. It does not add hardware command
paths, serial TX, Pico commands, or physical motion.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_kinematic_world_phase55.glb"
KINEMATICS_PATH = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_kinematics.json"
OUT_JSON = PROJECT_ROOT / "reports/phase56_runtime_node_group_coverage.json"
OUT_MD = PROJECT_ROOT / "reports/phase56_runtime_node_group_coverage.md"


def read_glb_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    magic, _version, _length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise SystemExit(f"Not a GLB file: {path}")
    offset = 12
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            return json.loads(chunk.decode("utf-8"))
    raise SystemExit(f"GLB JSON chunk not found: {path}")


def main() -> None:
    glb = read_glb_json(GLB_PATH)
    kinematics = json.loads(KINEMATICS_PATH.read_text(encoding="utf-8"))
    node_names = [str(node.get("name", "")) for node in glb.get("nodes", []) if node.get("name")]
    group_by_node: dict[str, str] = {}
    duplicate_assignments: dict[str, list[str]] = {}
    priority = ["camera_group", "launcher_group", "pitch_group", "static_root", "decorative_static_covers", "yaw_group"]
    groups = kinematics.get("groups", {})
    for group_name in priority + [name for name in groups if name not in priority]:
        labels = groups.get(group_name, [])
        for label in labels:
            previous = group_by_node.get(label)
            if previous:
                duplicate_assignments.setdefault(label, [previous]).append(group_name)
                continue
            group_by_node[label] = group_name

    missing = [name for name in node_names if name not in group_by_node]
    extra = sorted(label for label in group_by_node if label not in set(node_names))
    counts: dict[str, int] = {}
    for name in node_names:
        group = group_by_node.get(name, "unassigned")
        counts[group] = counts.get(group, 0) + 1

    payload = {
        "schema": "phase56_runtime_node_group_coverage",
        "glbPath": "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "kinematicsPath": "/assets/digital-twin/ktr1_kinematics.json",
        "nodeCount": len(node_names),
        "coveredNodeCount": len(node_names) - len(missing),
        "coverageRatio": round((len(node_names) - len(missing)) / max(1, len(node_names)), 4),
        "groupCountsFromGlbNodes": counts,
        "missingNodes": missing,
        "extraKinematicLabels": extra,
        "duplicateAssignments": duplicate_assignments,
        "keyNodeCoverage": {
            "kamera v3": group_by_node.get("kamera v3"),
            "Bileşen13": group_by_node.get("Bileşen13"),
            "Axel": group_by_node.get("Axel"),
            "alt gövde": group_by_node.get("alt gövde"),
            "tabla": group_by_node.get("tabla"),
        },
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "\n".join([
            "# Phase 56 Runtime Node Group Coverage",
            "",
            f"- GLB nodes: `{payload['nodeCount']}`",
            f"- Covered nodes: `{payload['coveredNodeCount']}`",
            f"- Coverage ratio: `{payload['coverageRatio']}`",
            f"- Missing nodes: `{len(missing)}`",
            f"- Duplicate assignments: `{len(duplicate_assignments)}`",
            "",
            "## Group Counts From GLB Nodes",
            "",
            *[f"- `{key}`: {value}" for key, value in sorted(counts.items())],
            "",
            "## Key Node Coverage",
            "",
            *[f"- `{key}`: `{value}`" for key, value in payload["keyNodeCoverage"].items()],
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
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
