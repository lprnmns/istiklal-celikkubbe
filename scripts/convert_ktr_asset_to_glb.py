#!/usr/bin/env python3
"""Convert the real KTR STL asset into a browser-ready GLB hero model.

The script is intentionally dependency-free so Phase 49 can run on the field
laptop without Blender/trimesh. It supports binary STL input, normalizes the
mesh into operator-scene units, and writes a GLB plus metadata manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "frontend" / "public" / "assets" / "digital-twin"
DEFAULT_OUTPUT = ASSET_DIR / "ktr1_operator_hero.glb"
DEFAULT_MANIFEST = ASSET_DIR / "ktr1_operator_hero_manifest.json"
DEFAULT_ASSET_MANIFEST = ASSET_DIR / "asset_manifest.json"


def candidate_sources() -> list[Path]:
    return [
        ASSET_DIR / "ktr1_binary.stl",
        ROOT / "assets" / "digital-twin" / "ktr1_binary.stl",
        ROOT / "assets" / "digital-twin" / "ktr1.stl",
        ROOT / "ktr1.stl",
        ROOT / "ktr1.step",
        ROOT / "ktr1.stp",
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_source(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            return path
        raise SystemExit(f"KTR source asset not found: {path}")

    for path in candidate_sources():
        if path.exists():
            return path
    searched = "\n".join(str(path) for path in candidate_sources())
    raise SystemExit(f"No KTR STL/STEP asset found. Searched:\n{searched}")


def read_binary_stl(path: Path) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]], int]:
    data = path.read_bytes()
    if path.suffix.lower() in {".step", ".stp"}:
        raise SystemExit("STEP/STP source found but no local STEP conversion backend is available. Provide STL or install FreeCAD conversion flow.")
    if len(data) < 84:
        raise SystemExit(f"Invalid STL: file too small ({path})")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if expected_size > len(data):
        raise SystemExit(f"Invalid binary STL: header expects {triangle_count} triangles but file is truncated")

    positions: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    offset = 84
    for _ in range(triangle_count):
        nx, ny, nz = struct.unpack_from("<3f", data, offset)
        offset += 12
        vertices = [struct.unpack_from("<3f", data, offset + index * 12) for index in range(3)]
        offset += 36 + 2
        normal = normalize((nx, ny, nz))
        if normal == (0.0, 0.0, 0.0):
            normal = face_normal(vertices)
        for vertex in vertices:
            positions.append(vertex)
            normals.append(normal)
    return positions, normals, triangle_count


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = vector
    length = math.sqrt(x * x + y * y + z * z)
    if length <= 1e-12:
        return (0.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


def face_normal(vertices: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    ax, ay, az = vertices[0]
    bx, by, bz = vertices[1]
    cx, cy, cz = vertices[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    return normalize((uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx))


def bounds(points: Iterable[tuple[float, float, float]]) -> tuple[list[float], list[float]]:
    iterator = iter(points)
    try:
        first = next(iterator)
    except StopIteration:
        raise SystemExit("STL contains no vertices")
    mins = [first[0], first[1], first[2]]
    maxs = [first[0], first[1], first[2]]
    for point in iterator:
        for index in range(3):
            mins[index] = min(mins[index], point[index])
            maxs[index] = max(maxs[index], point[index])
    return mins, maxs


def normalize_positions(positions: list[tuple[float, float, float]]) -> tuple[list[tuple[float, float, float]], dict[str, object]]:
    mins, maxs = bounds(positions)
    center = [(mins[index] + maxs[index]) / 2.0 for index in range(3)]
    extents = [maxs[index] - mins[index] for index in range(3)]
    max_extent = max(extents) or 1.0
    scene_max_extent = 2.45
    scale = scene_max_extent / max_extent
    normalized = [
        (
            (x - center[0]) * scale,
            (y - center[1]) * scale,
            (z - center[2]) * scale,
        )
        for x, y, z in positions
    ]
    out_mins, out_maxs = bounds(normalized)
    metadata = {
        "raw_bounds": {"min": mins, "max": maxs, "extents": extents},
        "normalized_bounds": {"min": out_mins, "max": out_maxs, "extents": [out_maxs[i] - out_mins[i] for i in range(3)]},
        "normalization_center": center,
        "normalization_scale": scale,
        "scene_max_extent": scene_max_extent,
    }
    return normalized, metadata


def pack_vec3(values: list[tuple[float, float, float]]) -> bytes:
    return b"".join(struct.pack("<3f", *value) for value in values)


def pad4(data: bytes, fill: bytes = b"\x00") -> bytes:
    return data + fill * ((4 - len(data) % 4) % 4)


def write_glb(path: Path, positions: list[tuple[float, float, float]], normals: list[tuple[float, float, float]], metadata: dict[str, object]) -> None:
    position_bytes = pack_vec3(positions)
    normal_bytes = pack_vec3(normals)
    bin_blob = pad4(position_bytes + normal_bytes)
    pos_mins, pos_maxs = bounds(positions)

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "ISTIKLAL Phase 49 dependency-free STL to GLB pipeline",
            "copyright": "ISTIKLAL C2 project asset conversion; no_physical_command_generated=true",
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "ktr1_operator_hero_real_stl_mesh", "mesh": 0}],
        "meshes": [{
            "name": "KTR1 real STL-derived hero mesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "mode": 4,
                "material": 0,
            }],
        }],
        "materials": [{
            "name": "matte graphite real KTR mesh",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.19, 0.22, 0.25, 1.0],
                "metallicFactor": 0.18,
                "roughnessFactor": 0.62,
            },
        }],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(position_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(position_bytes), "byteLength": len(normal_bytes), "target": 34962},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(positions),
                "type": "VEC3",
                "min": pos_mins,
                "max": pos_maxs,
            },
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": len(normals),
                "type": "VEC3",
            },
        ],
        "extras": {
            "source": "real KTR STL-derived browser asset",
            "normalization": metadata,
            "no_physical_command_generated": True,
        },
    }
    json_blob = pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    total_length = 12 + 8 + len(json_blob) + 8 + len(bin_blob)
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    json_chunk = struct.pack("<I4s", len(json_blob), b"JSON") + json_blob
    bin_chunk = struct.pack("<I4s", len(bin_blob), b"BIN\x00") + bin_blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + json_chunk + bin_chunk)


def write_manifests(source: Path, output: Path, manifest_path: Path, asset_manifest_path: Path, triangle_count: int, metadata: dict[str, object]) -> None:
    relative_output = "/" + str(output.relative_to(ROOT / "frontend" / "public"))
    manifest = {
        "schema_version": "phase49.ktr_operator_hero.v1",
        "selected_asset_type": "REAL_GLB",
        "selected_asset_path": relative_output,
        "preferred_browser_asset": relative_output,
        "source_asset": str(source),
        "source_asset_sha256": sha256(source),
        "source_asset_size_bytes": source.stat().st_size,
        "converted_asset": str(output),
        "converted_asset_size_bytes": output.stat().st_size,
        "triangle_count_before": triangle_count,
        "triangle_count_after": triangle_count,
        "conversion_method": "dependency_free_binary_stl_to_glb",
        "conversion_status": "converted_real_stl_to_glb",
        "scale": metadata["normalization_scale"],
        "rotation": {"x": 0, "y": 0, "z": 0},
        "position": {"x": 0, "y": 0, "z": 0},
        "estimated_camera_anchor": {"x": -0.34, "y": 0.98, "z": 0.12, "source": "estimated_from_operator_mount_reference"},
        "estimated_launcher_anchor": {"x": 0.0, "y": 0.74, "z": -0.34, "source": "estimated_from_launcher_axis_reference"},
        "estimated_base_anchor": {"x": 0.0, "y": -0.38, "z": 0.0, "source": "normalized_stl_bounds_center"},
        "normalization": metadata,
        "scale_units": "normalized_scene_units_from_stl",
        "coordinate_notes": "Binary STL coordinates are normalized and centered for browser operator visualization; anchors are estimated overlays, not physical command references.",
        "camera_mount_reference_available": True,
        "launcher_axis_reference_available": True,
        "no_physical_command_generated": True,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    public_manifest = {
        "selected_asset_type": "REAL_GLB",
        "selected_asset_path": relative_output,
        "preferred_browser_asset": relative_output,
        "source_stl_path": str(source),
        "source_stl_sha256": manifest["source_asset_sha256"],
        "source_cad_path": str(source),
        "conversion_status": "converted_real_stl_to_glb",
        "conversion_method": "dependency_free_binary_stl_to_glb",
        "derived_web_asset_size_bytes": output.stat().st_size,
        "triangle_count_before": triangle_count,
        "triangle_count_after": triangle_count,
        "fallback_reason": "real KTR STL converted to GLB and used as the default hero scene",
        "scale_units": "normalized_scene_units_from_stl",
        "coordinate_notes": manifest["coordinate_notes"],
        "asset_transform": {
            "scale": {"x": 1, "y": 1, "z": 1},
            "rotation_deg": {"x": 0, "y": 0, "z": 0},
            "position": {"x": 0, "y": 0, "z": 0},
            "camera_mount_anchor": manifest["estimated_camera_anchor"],
            "launcher_axis_anchor": manifest["estimated_launcher_anchor"],
            "base_anchor": manifest["estimated_base_anchor"],
        },
        "camera_mount_reference_available": True,
        "launcher_axis_reference_available": True,
        "asset_fallback_reason": "real KTR model is the hero asset; procedural replacement is not used by default",
        "no_physical_command_generated": True,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
    }
    asset_manifest_path.write_text(json.dumps(public_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert real KTR STL asset to GLB hero model.")
    parser.add_argument("--source", default=None, help="Optional explicit STL source path")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output GLB path")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Output conversion manifest JSON path")
    parser.add_argument("--asset-manifest", default=str(DEFAULT_ASSET_MANIFEST), help="Frontend public asset manifest JSON path")
    args = parser.parse_args()

    source = locate_source(args.source)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    asset_manifest_path = Path(args.asset_manifest)
    if not asset_manifest_path.is_absolute():
        asset_manifest_path = ROOT / asset_manifest_path

    positions, normals, triangle_count = read_binary_stl(source)
    normalized_positions, metadata = normalize_positions(positions)
    write_glb(output, normalized_positions, normals, metadata)
    write_manifests(source, output, manifest_path, asset_manifest_path, triangle_count, metadata)
    print(json.dumps({
        "source_asset": str(source),
        "converted_asset": str(output),
        "triangle_count_before": triangle_count,
        "triangle_count_after": triangle_count,
        "converted_asset_size_bytes": output.stat().st_size,
        "manifest": str(manifest_path),
        "asset_manifest": str(asset_manifest_path),
        "no_physical_command_generated": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
