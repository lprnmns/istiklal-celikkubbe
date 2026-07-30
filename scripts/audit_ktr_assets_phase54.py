#!/usr/bin/env python3
"""Inventory KTR CAD/mesh assets for Phase 54 fidelity comparison."""

from __future__ import annotations

import json
import os
import struct
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = PROJECT_ROOT / "reports/142_phase54_asset_inventory.md"
REPORT_JSON = PROJECT_ROOT / "reports/phase54_asset_inventory_contract.json"


def iso_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def candidate_paths() -> list[Path]:
    roots = [
        PROJECT_ROOT / "work",
        PROJECT_ROOT / "frontend/public/assets/digital-twin",
        PROJECT_ROOT,
    ]
    keywords = ("ktr", "KTR", "operator", "twin", "cad", "step", "stl", "glb", "str")
    skip_dirs = {".git", ".venv", "node_modules", "dist", "__pycache__", ".pytest_cache"}
    paths: dict[Path, None] = {}
    for root in roots:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in skip_dirs]
            current = Path(current_root)
            if root == PROJECT_ROOT and current != PROJECT_ROOT:
                # The project root pass is only for top-level assets such as
                # ktr1.step/ktr1.stl. Subtrees are handled by explicit roots.
                dirnames[:] = []
            for filename in filenames:
                path = current / filename
                if not path.is_file():
                    continue
                name = path.name
                if any(keyword in name for keyword in keywords):
                    suffix = path.suffix.lower()
                    if suffix in {".step", ".stp", ".stl", ".str", ".glb", ".gltf", ".json"}:
                        paths[path.resolve()] = None
    return sorted(paths)


def inspect_step(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "loads": text.startswith("ISO-10303-21") or "ISO-10303-21" in text[:1024],
        "step_color_records": text.count("COLOUR_RGB"),
        "advanced_face_count": text.count("ADVANCED_FACE"),
        "closed_shell_count": text.count("CLOSED_SHELL"),
        "manifold_solid_brep_count": text.count("MANIFOLD_SOLID_BREP"),
        "material_color_available": text.count("COLOUR_RGB") > 0,
        "weapon_front_keywords": sum(text.upper().count(word) for word in ["NAMLU", "BARREL", "LAUNCHER", "BILE"]),
    }


def inspect_binary_stl(data: bytes) -> dict[str, object] | None:
    if len(data) < 84:
        return None
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + triangle_count * 50
    if expected != len(data):
        return None
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    for offset in range(84, len(data), 50):
        for vertex in range(3):
            base = offset + 12 + vertex * 12
            x, y, z = struct.unpack_from("<fff", data, base)
            for index, value in enumerate((x, y, z)):
                mins[index] = min(mins[index], value)
                maxs[index] = max(maxs[index], value)
    return {
        "loads": True,
        "stl_format": "binary",
        "triangle_count": triangle_count,
        "bounding_box": {"min": mins, "max": maxs},
        "material_color_available": False,
        "weapon_front_keywords": 0,
    }


def inspect_ascii_stl(path: Path) -> dict[str, object]:
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    triangle_count = 0
    vertex_count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("facet normal"):
                triangle_count += 1
            if not stripped.startswith("vertex "):
                continue
            parts = stripped.split()
            if len(parts) < 4:
                continue
            values = [float(parts[1]), float(parts[2]), float(parts[3])]
            vertex_count += 1
            for index, value in enumerate(values):
                mins[index] = min(mins[index], value)
                maxs[index] = max(maxs[index], value)
    return {
        "loads": vertex_count > 0,
        "stl_format": "ascii",
        "triangle_count": triangle_count or vertex_count // 3,
        "vertex_count": vertex_count,
        "bounding_box": {"min": mins, "max": maxs},
        "material_color_available": False,
        "weapon_front_keywords": 0,
    }


def inspect_stl(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    binary = inspect_binary_stl(data)
    if binary is not None:
        return binary
    return inspect_ascii_stl(path)


def inspect_glb(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        return {"loads": False, "error": "not a binary glTF file"}
    json_len, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON":
        return {"loads": False, "error": "first GLB chunk is not JSON"}
    gltf = json.loads(data[20:20 + json_len].decode("utf-8"))
    meshes = gltf.get("meshes", [])
    materials = gltf.get("materials", [])
    accessors = gltf.get("accessors", [])
    triangle_count = 0
    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            position = primitive.get("attributes", {}).get("POSITION")
            if isinstance(position, int) and position < len(accessors):
                triangle_count += int(accessors[position].get("count", 0)) // 3
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    for accessor in accessors:
        if accessor.get("type") == "VEC3" and "min" in accessor and "max" in accessor:
            for index in range(3):
                mins[index] = min(mins[index], float(accessor["min"][index]))
                maxs[index] = max(maxs[index], float(accessor["max"][index]))
    return {
        "loads": True,
        "mesh_count": len(meshes),
        "material_count": len(materials),
        "triangle_count": triangle_count,
        "bounding_box": {"min": mins, "max": maxs},
        "material_color_available": bool(materials),
        "weapon_front_keywords": sum(str(mesh.get("name", "")).lower().count(word) for mesh in meshes for word in ["namlu", "barrel", "launcher", "bile"]),
    }


def inspect(path: Path) -> dict[str, object]:
    stat = path.stat()
    item: dict[str, object] = {
        "path": rel(path),
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_time": iso_time(stat.st_mtime),
    }
    try:
        suffix = path.suffix.lower()
        if suffix in {".step", ".stp"}:
            item.update(inspect_step(path))
        elif suffix in {".stl", ".str"}:
            item.update(inspect_stl(path))
        elif suffix == ".glb":
            item.update(inspect_glb(path))
        elif suffix == ".json":
            item.update({"loads": True, "json_keys": list(json.loads(path.read_text(encoding="utf-8")).keys())[:12]})
        else:
            item.update({"loads": False, "error": "unsupported extension"})
    except Exception as exc:  # pragma: no cover - diagnostics script
        item.update({"loads": False, "error": str(exc)})
    item["weapon_front_assembly_appears_present"] = bool(int(item.get("weapon_front_keywords", 0) or 0) > 0 or int(item.get("triangle_count", 0) or 0) > 100_000)
    return item


def write_markdown(items: list[dict[str, object]]) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 54 Asset Inventory",
        "",
        "Scope: KTR STEP/STL/GLB assets discovered in `work/`, project root, and `frontend/public/assets/digital-twin/`.",
        "",
        "| Path | Ext | Size | Loads | Geometry | Materials | Weapon/front evidence |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for item in items:
        geometry = []
        for key in ("part_count", "mesh_count", "triangle_count", "advanced_face_count", "closed_shell_count"):
            if key in item:
                geometry.append(f"{key}={item[key]}")
        lines.append(
            f"| `{item['path']}` | `{item['extension']}` | {item['size_bytes']} | {item.get('loads')} | "
            f"{'<br>'.join(geometry) or 'n/a'} | {item.get('material_color_available', 'n/a')} | "
            f"{item.get('weapon_front_assembly_appears_present')} |"
        )
    lines.extend([
        "",
        "Notes:",
        "- STEP color availability is inferred from `COLOUR_RGB` records; installed headless FreeCAD still may not expose face colors directly.",
        "- STL/STR files do not carry material data, but high triangle count can preserve weapon geometry for geometry-only fallback.",
        "- No physical command, serial TX, motor, fire, servo, GPIO, PWM, STEP/DIR, or hardware-enable path is created by this audit.",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    items = [inspect(path) for path in candidate_paths()]
    write_markdown(items)
    REPORT_JSON.write_text(json.dumps({
        "phase": 54,
        "asset_inventory_count": len(items),
        "items": items,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
        "no_physical_command_generated": True,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "report": rel(REPORT_MD), "contract": rel(REPORT_JSON)}))


if __name__ == "__main__":
    main()
