#!/usr/bin/env python3
"""Convert KTR STL/STR geometry to GLB for Phase 54 fidelity fallback."""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "ktr1.stl"
DEFAULT_OUTPUT = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54.glb"
DEFAULT_MANIFEST = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54_manifest.json"


def normal_from_triangle(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> tuple[float, float, float]:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def read_binary_stl(path: Path) -> tuple[list[float], list[float], str] | None:
    data = path.read_bytes()
    if len(data) < 84:
        return None
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    if 84 + triangle_count * 50 != len(data):
        return None
    positions: list[float] = []
    normals: list[float] = []
    for offset in range(84, len(data), 50):
        normal = struct.unpack_from("<fff", data, offset)
        for index in range(3):
            vertex = struct.unpack_from("<fff", data, offset + 12 + index * 12)
            positions.extend(vertex)
            normals.extend(normal)
    return positions, normals, "binary"


def read_ascii_stl(path: Path) -> tuple[list[float], list[float], str]:
    positions: list[float] = []
    normals: list[float] = []
    tri: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped.startswith("vertex "):
                continue
            parts = stripped.split()
            if len(parts) < 4:
                continue
            tri.append((float(parts[1]), float(parts[2]), float(parts[3])))
            if len(tri) == 3:
                normal = normal_from_triangle(tri[0], tri[1], tri[2])
                for vertex in tri:
                    positions.extend(vertex)
                    normals.extend(normal)
                tri = []
    return positions, normals, "ascii"


def read_stl(path: Path) -> tuple[list[float], list[float], str]:
    binary = read_binary_stl(path)
    if binary is not None:
        return binary
    return read_ascii_stl(path)


def transformed_positions(raw: list[float]) -> tuple[list[float], dict[str, list[float]], float]:
    xs = raw[0::3]
    ys = raw[1::3]
    zs = raw[2::3]
    mins = [min(xs), min(ys), min(zs)]
    maxs = [max(xs), max(ys), max(zs)]
    center = [(mins[index] + maxs[index]) * 0.5 for index in range(3)]
    extent = [maxs[index] - mins[index] for index in range(3)]
    scale = 3.75 / (max(extent) or 1.0)
    out: list[float] = []
    for x, y, z in zip(xs, ys, zs):
        out.extend([
            (x - center[0]) * scale,
            (z - mins[2]) * scale - 0.42,
            -(y - center[1]) * scale,
        ])
    tx = out[0::3]
    ty = out[1::3]
    tz = out[2::3]
    return out, {"min": [min(tx), min(ty), min(tz)], "max": [max(tx), max(ty), max(tz)]}, scale


def transform_normals(raw: list[float]) -> list[float]:
    out: list[float] = []
    for x, y, z in zip(raw[0::3], raw[1::3], raw[2::3]):
        out.extend([x, z, -y])
    return out


def pack_accessor(buffer: bytearray, values: list[float], accessors: list[dict[str, object]], buffer_views: list[dict[str, object]], include_minmax: bool) -> int:
    while len(buffer) % 4:
        buffer.append(0)
    offset = len(buffer)
    buffer.extend(struct.pack("<" + "f" * len(values), *values))
    length = len(buffer) - offset
    buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": length, "target": 34962})
    accessor: dict[str, object] = {
        "bufferView": len(buffer_views) - 1,
        "componentType": 5126,
        "count": len(values) // 3,
        "type": "VEC3",
    }
    if include_minmax:
        accessor["min"] = [min(values[i::3]) for i in range(3)]
        accessor["max"] = [max(values[i::3]) for i in range(3)]
    accessors.append(accessor)
    return len(accessors) - 1


def write_glb(path: Path, positions: list[float], normals: list[float]) -> None:
    buffer = bytearray()
    buffer_views: list[dict[str, object]] = []
    accessors: list[dict[str, object]] = []
    pos_accessor = pack_accessor(buffer, positions, accessors, buffer_views, True)
    norm_accessor = pack_accessor(buffer, normals, accessors, buffer_views, False)
    material = {
        "name": "phase54_stl_geometry_neutral_cad_gray",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.72, 0.75, 0.78, 1.0],
            "metallicFactor": 0.08,
            "roughnessFactor": 0.48,
        },
    }
    gltf = {
        "asset": {"version": "2.0", "generator": "ISTIKLAL Phase 54 STL geometry converter"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "ktr1_stl_geometry_phase54", "mesh": 0}],
        "meshes": [{
            "name": "ktr1_stl_geometry_phase54",
            "primitives": [{"attributes": {"POSITION": pos_accessor, "NORMAL": norm_accessor}, "material": 0, "mode": 4}],
        }],
        "materials": [material],
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
    total = 12 + 8 + len(json_blob) + 8 + len(buffer)
    glb.extend(struct.pack("<III", 0x46546C67, 2, total))
    glb.extend(struct.pack("<I4s", len(json_blob), b"JSON"))
    glb.extend(json_blob)
    glb.extend(struct.pack("<I4s", len(buffer), b"BIN\0"))
    glb.extend(buffer)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(glb)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    source = args.source.resolve()
    if source.suffix.lower() not in {".stl", ".str"}:
        raise SystemExit(f"Expected STL/STR source, got {source}")
    raw_positions, raw_normals, stl_format = read_stl(source)
    if not raw_positions:
        raise SystemExit(f"No STL triangles found in {source}")
    positions, bbox, scale = transformed_positions(raw_positions)
    normals = transform_normals(raw_normals)
    write_glb(args.output.resolve(), positions, normals)
    triangle_count = len(positions) // 9
    output_asset = f"/{args.output.resolve().relative_to(PROJECT_ROOT / 'frontend/public')}"
    manifest = {
        "phase": 54,
        "selected_asset_type": "REAL_STL_GEOMETRY_GLB",
        "selected_asset_path": output_asset,
        "preferred_browser_asset": output_asset,
        "source_asset": str(source.relative_to(PROJECT_ROOT)) if source.is_relative_to(PROJECT_ROOT) else str(source),
        "output_asset": output_asset,
        "conversion_method": "ascii_or_binary_stl_to_glb_geometry_only_phase54",
        "stl_format": stl_format,
        "material_preserved": False,
        "materials_reconstructed": False,
        "material_preservation_status": "geometry_only",
        "color_count": 1,
        "material_count": 1,
        "part_count": 1,
        "mesh_count": 1,
        "triangle_count": triangle_count,
        "triangle_count_before": triangle_count,
        "triangle_count_after": triangle_count,
        "bounding_box": bbox,
        "scale": scale,
        "camera_anchor": {"x": 0.5, "y": 0.72, "z": 1.03, "source": "estimated_phase54_stl_geometry"},
        "launcher_anchor": {"x": -0.3, "y": 0.68, "z": 1.26, "source": "estimated_phase54_stl_geometry"},
        "base_anchor": {"x": 0, "y": -0.42, "z": 0, "source": "normalized_stl_floor"},
        "target_projection_anchor": {"x": 0.5, "y": 0.72, "z": 0.03, "source": "camera_anchor_forward_projection"},
        "weapon_visibility_status": "candidate_geometry_preserved_no_materials",
        "fallback_used": False,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
        "no_physical_command_generated": True,
    }
    args.manifest.resolve().write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "manifest": str(args.manifest), "triangles": triangle_count, "format": stl_format}))


if __name__ == "__main__":
    main()
