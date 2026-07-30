#!/usr/bin/env python3
"""Inspect Phase 55 KTR GLB node hierarchy and mesh statistics."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLB = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_kinematic_world_phase55.glb"
FALLBACK_GLB = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_step_hifi_phase54.glb"
REPORT_JSON = PROJECT_ROOT / "reports/phase55_glb_node_hierarchy.json"
REPORT_MD = PROJECT_ROOT / "reports/phase55_glb_node_hierarchy.md"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def read_glb(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"not a binary glTF file: {path}")
    json_len, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON":
        raise ValueError("first GLB chunk is not JSON")
    return json.loads(data[20:20 + json_len].decode("utf-8"))


def material_hex(material: dict[str, Any]) -> str | None:
    color = material.get("pbrMetallicRoughness", {}).get("baseColorFactor")
    if not isinstance(color, list) or len(color) < 3:
        return None
    values = [max(0, min(255, int(round(float(channel) * 255)))) for channel in color[:3]]
    return "#" + "".join(f"{value:02x}" for value in values)


def inspect(path: Path) -> dict[str, Any]:
    gltf = read_glb(path)
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    accessors = gltf.get("accessors", [])
    materials = gltf.get("materials", [])

    mesh_triangles: dict[int, int] = {}
    mesh_materials: dict[int, list[int]] = {}
    for mesh_index, mesh in enumerate(meshes):
        tris = 0
        mat_ids: list[int] = []
        for primitive in mesh.get("primitives", []):
            pos = primitive.get("attributes", {}).get("POSITION")
            if isinstance(pos, int) and pos < len(accessors):
                tris += int(accessors[pos].get("count", 0)) // 3
            mat = primitive.get("material")
            if isinstance(mat, int) and mat not in mat_ids:
                mat_ids.append(mat)
        mesh_triangles[mesh_index] = tris
        mesh_materials[mesh_index] = mat_ids

    inspected_nodes = []
    total_triangles = 0
    root_children = set()
    for scene in gltf.get("scenes", []):
        for node_index in scene.get("nodes", []):
            if isinstance(node_index, int):
                root_children.add(node_index)
    for index, node in enumerate(nodes):
        mesh_index = node.get("mesh")
        triangles = mesh_triangles.get(mesh_index, 0) if isinstance(mesh_index, int) else 0
        total_triangles += triangles
        material_ids = mesh_materials.get(mesh_index, []) if isinstance(mesh_index, int) else []
        inspected_nodes.append({
            "index": index,
            "name": node.get("name", f"node_{index}"),
            "mesh": mesh_index,
            "children": node.get("children", []),
            "root_scene_child": index in root_children,
            "triangle_count": triangles,
            "material_ids": material_ids,
            "material_names": [materials[item].get("name", f"material_{item}") for item in material_ids if item < len(materials)],
        })

    return {
        "phase": 55,
        "glb_path": rel(path),
        "glb_size_bytes": path.stat().st_size,
        "node_count": len(nodes),
        "mesh_count": len(meshes),
        "material_count": len(materials),
        "triangle_count": total_triangles,
        "root_scene_node_count": len(root_children),
        "hierarchy_status": "flat_or_shallow" if len(root_children) > max(1, len(nodes) // 2) else "nested",
        "materials": [
            {
                "index": index,
                "name": material.get("name", f"material_{index}"),
                "color": material_hex(material),
                "roughness": material.get("pbrMetallicRoughness", {}).get("roughnessFactor"),
                "metalness": material.get("pbrMetallicRoughness", {}).get("metallicFactor"),
            }
            for index, material in enumerate(materials)
        ],
        "nodes": inspected_nodes,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
        "no_physical_command_generated": True,
    }


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    lines = [
        "# Phase 55 GLB Node Hierarchy Inspection",
        "",
        f"- GLB: `{payload['glb_path']}`",
        f"- Nodes: `{payload['node_count']}`",
        f"- Meshes: `{payload['mesh_count']}`",
        f"- Materials: `{payload['material_count']}`",
        f"- Triangles: `{payload['triangle_count']}`",
        f"- Hierarchy status: `{payload['hierarchy_status']}`",
        "",
        "The Phase 55 runtime creates visualization-only yaw/pitch groups from this named mesh list using `ktr1_kinematics.json`; it does not treat this flat node list as validated mechanical joint metadata.",
        "",
        "## Materials",
        "",
        "| Name | Color | Roughness | Metalness |",
        "| --- | --- | ---: | ---: |",
    ]
    for material in payload["materials"]:
        lines.append(f"| `{material['name']}` | `{material['color']}` | {material['roughness']} | {material['metalness']} |")
    lines.extend(["", "## Node Samples", "", "| Index | Name | Root | Triangles | Materials |", "| ---: | --- | --- | ---: | --- |"])
    for node in payload["nodes"][:80]:
        mats = ", ".join(f"`{name}`" for name in node["material_names"])
        lines.append(f"| {node['index']} | `{node['name']}` | {node['root_scene_child']} | {node['triangle_count']} | {mats} |")
    lines.extend([
        "",
        "Safety: inspection is read-only; no physical command, serial TX, Pico command, motor, fire, servo, GPIO, PWM, STEP/DIR, or hardware-enable path is created.",
        "",
    ])
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, default=DEFAULT_GLB if DEFAULT_GLB.exists() else FALLBACK_GLB)
    parser.add_argument("--report-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    args = parser.parse_args()

    path = args.glb.resolve()
    payload = inspect(path)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(payload, args.report_md)
    print(json.dumps({
        "glb": rel(path),
        "nodes": payload["node_count"],
        "meshes": payload["mesh_count"],
        "triangles": payload["triangle_count"],
        "report": rel(args.report_json),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
