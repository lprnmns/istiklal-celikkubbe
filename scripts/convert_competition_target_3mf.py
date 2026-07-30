#!/usr/bin/env python3
"""Convert the supplied competition-target 3MF package to lightweight GLB assets.

The original 3MF contains printable, high-poly meshes.  This converter keeps
their measured millimetre dimensions, centres each target at its own origin,
and applies deterministic vertex clustering so that the browser can display
multiple live targets without competing with vision inference for resources.
It only creates static visual assets; it has no command or hardware access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "work" / "competition_target_sources" / "Modeller_Kil6t.zip"
DEFAULT_OUTPUT = ROOT / "frontend" / "public" / "assets" / "targets"

# Object ids and names are read from the Bambu 3MF metadata in the supplied
# archive.  These names are mapped deliberately to the canonical model-package
# classes; no semantic class is inferred from geometry alone.
TARGETS = (
    ("ballistic_missile", "Balistik Füze", "object_18.model", 0xF97316, 500.0),
    ("helicopter", "Helikopter", "object_19.model", 0x60A5FA, 583.0),
    ("f16", "F-16", "object_20.model", 0xA78BFA, 500.0),
    ("mini_micro_uav", "Mini/Micro İHA", "object_21.model", 0x34D399, 375.0),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def namespace_free(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_mesh(payload: bytes) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    root = ET.fromstring(payload)
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for item in root.iter():
        tag = namespace_free(item.tag)
        if tag == "vertex":
            vertices.append((float(item.attrib["x"]), float(item.attrib["y"]), float(item.attrib["z"])))
        elif tag == "triangle":
            triangles.append((int(item.attrib["v1"]), int(item.attrib["v2"]), int(item.attrib["v3"])))
    if not vertices or not triangles:
        raise ValueError("3MF object has no mesh vertices or triangles")
    return vertices, triangles


def bounds(vertices: list[tuple[float, float, float]]) -> tuple[list[float], list[float]]:
    mins = [vertices[0][0], vertices[0][1], vertices[0][2]]
    maxs = list(mins)
    for point in vertices[1:]:
        for index, value in enumerate(point):
            mins[index] = min(mins[index], value)
            maxs[index] = max(maxs[index], value)
    return mins, maxs


def clustered_mesh(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    grid_resolution: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Collapse nearby printable vertices into a visual LOD mesh.

    This intentionally preserves the silhouette/relative size rather than
    printable topology. It is deterministic and dependency-free.
    """

    mins, maxs = bounds(vertices)
    max_extent = max(maxs[index] - mins[index] for index in range(3)) or 1.0
    scale = grid_resolution / max_extent
    sums: dict[tuple[int, int, int], list[float]] = {}
    source_to_cluster: dict[int, tuple[int, int, int]] = {}

    def cluster_key(index: int) -> tuple[int, int, int]:
        if index in source_to_cluster:
            return source_to_cluster[index]
        x, y, z = vertices[index]
        key = (
            int(math.floor((x - mins[0]) * scale)),
            int(math.floor((y - mins[1]) * scale)),
            int(math.floor((z - mins[2]) * scale)),
        )
        source_to_cluster[index] = key
        if key not in sums:
            sums[key] = [x, y, z, 1.0]
        else:
            sums[key][0] += x
            sums[key][1] += y
            sums[key][2] += z
            sums[key][3] += 1.0
        return key

    for triangle in triangles:
        cluster_key(triangle[0])
        cluster_key(triangle[1])
        cluster_key(triangle[2])

    keys = sorted(sums)
    key_to_index = {key: index for index, key in enumerate(keys)}
    clustered_vertices = [
        (value[0] / value[3], value[1] / value[3], value[2] / value[3])
        for key, value in ((key, sums[key]) for key in keys)
    ]
    clustered_triangles: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for triangle in triangles:
        result = tuple(key_to_index[cluster_key(vertex)] for vertex in triangle)
        if len(set(result)) < 3:
            continue
        canonical = tuple(sorted(result))
        if canonical in seen:
            continue
        seen.add(canonical)
        clustered_triangles.append(result)
    return clustered_vertices, clustered_triangles


def choose_lod(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    target_triangles: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], int]:
    # A single candidate avoids repeated multi-million-face passes. The value
    # caps visually complex target meshes around the requested range in practice.
    resolution = max(24, min(112, int(math.sqrt(max(target_triangles, 1)) * 0.55)))
    output_vertices, output_triangles = clustered_mesh(vertices, triangles, resolution)
    return output_vertices, output_triangles, resolution


def normalise_and_normals(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]], dict[str, object]]:
    mins, maxs = bounds(vertices)
    center = [(mins[index] + maxs[index]) / 2.0 for index in range(3)]
    dimensions_mm = [maxs[index] - mins[index] for index in range(3)]
    positions = [
        ((x - center[0]) / 1000.0, (y - center[1]) / 1000.0, (z - center[2]) / 1000.0)
        for x, y, z in vertices
    ]
    accum = [[0.0, 0.0, 0.0] for _ in positions]
    for first, second, third in triangles:
        a, b, c = positions[first], positions[second], positions[third]
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        for index in (first, second, third):
            accum[index][0] += nx
            accum[index][1] += ny
            accum[index][2] += nz
    normals: list[tuple[float, float, float]] = []
    for x, y, z in accum:
        length = math.sqrt(x * x + y * y + z * z) or 1.0
        normals.append((x / length, y / length, z / length))
    return positions, normals, {
        "unit": "millimeter",
        "dimensions_mm": [round(value, 3) for value in dimensions_mm],
        "center_mm": [round(value, 3) for value in center],
    }


def pad4(payload: bytes, fill: bytes = b"\x00") -> bytes:
    return payload + fill * ((4 - len(payload) % 4) % 4)


def pack_vec3(values: list[tuple[float, float, float]]) -> bytes:
    return b"".join(struct.pack("<3f", *value) for value in values)


def write_glb(
    path: Path,
    *,
    class_name: str,
    label: str,
    positions: list[tuple[float, float, float]],
    normals: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    color_hex: int,
    extras: dict[str, object],
) -> None:
    position_blob = pack_vec3(positions)
    normal_blob = pack_vec3(normals)
    flat_indices = [index for triangle in triangles for index in triangle]
    index_format = "<" + ("H" if len(positions) <= 65535 else "I") * len(flat_indices)
    index_blob = struct.pack(index_format, *flat_indices)
    index_component = 5123 if len(positions) <= 65535 else 5125
    position_offset = 0
    normal_offset = len(pad4(position_blob))
    index_offset = normal_offset + len(pad4(normal_blob))
    binary = pad4(position_blob) + pad4(normal_blob) + pad4(index_blob)
    mins, maxs = bounds(positions)
    color = [((color_hex >> shift) & 0xFF) / 255.0 for shift in (16, 8, 0)]
    gltf = {
        "asset": {"version": "2.0", "generator": "ISTIKLAL competition target 3MF visual LOD converter"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": f"target_{class_name}", "mesh": 0}],
        "meshes": [{
            "name": label,
            "primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": 0, "mode": 4}],
        }],
        "materials": [{
            "name": f"{class_name}_target_material",
            "pbrMetallicRoughness": {"baseColorFactor": [*color, 1.0], "metallicFactor": 0.08, "roughnessFactor": 0.62},
        }],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": position_offset, "byteLength": len(position_blob), "target": 34962},
            {"buffer": 0, "byteOffset": normal_offset, "byteLength": len(normal_blob), "target": 34962},
            {"buffer": 0, "byteOffset": index_offset, "byteLength": len(index_blob), "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3", "min": mins, "max": maxs},
            {"bufferView": 1, "componentType": 5126, "count": len(normals), "type": "VEC3"},
            {"bufferView": 2, "componentType": index_component, "count": len(flat_indices), "type": "SCALAR"},
        ],
        "extras": {**extras, "class_name": class_name, "no_physical_command_generated": True},
    }
    json_blob = pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    total_length = 12 + 8 + len(json_blob) + 8 + len(binary)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        struct.pack("<4sII", b"glTF", 2, total_length)
        + struct.pack("<I4s", len(json_blob), b"JSON")
        + json_blob
        + struct.pack("<I4s", len(binary), b"BIN\x00")
        + binary
    )


def source_3mf(source: Path) -> tuple[bytes, str]:
    if source.suffix.lower() == ".3mf":
        return source.read_bytes(), source.name
    with zipfile.ZipFile(source) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".3mf")]
        if len(names) != 1:
            raise ValueError("archive must contain exactly one .3mf target package")
        return archive.read(names[0]), names[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target-triangles", type=int, default=24000)
    args = parser.parse_args()
    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"target archive not found: {source}")

    package, package_name = source_3mf(source)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_targets: list[dict[str, object]] = []
    with zipfile.ZipFile(__import__("io").BytesIO(package)) as archive:
        for class_name, label, object_name, color, reference_span_mm in TARGETS:
            raw_vertices, raw_triangles = parse_mesh(archive.read(f"3D/Objects/{object_name}"))
            lod_vertices, lod_triangles, grid_resolution = choose_lod(raw_vertices, raw_triangles, args.target_triangles)
            positions, normals, geometry = normalise_and_normals(lod_vertices, lod_triangles)
            output = output_dir / f"{class_name}.glb"
            source_sha = hashlib.sha256(archive.read(f"3D/Objects/{object_name}")).hexdigest()
            extras = {
                "source_archive": source.name,
                "source_3mf": package_name,
                "source_object": object_name,
                "source_object_sha256": source_sha,
                "raw_triangle_count": len(raw_triangles),
                "lod_triangle_count": len(lod_triangles),
                "lod_vertex_count": len(lod_vertices),
                "lod_grid_resolution": grid_resolution,
                "reference_span_mm": reference_span_mm,
                "geometry": geometry,
            }
            write_glb(output, class_name=class_name, label=label, positions=positions, normals=normals, triangles=lod_triangles, color_hex=color, extras=extras)
            manifest_targets.append({
                "class_name": class_name,
                "label": label,
                "asset_path": "/assets/targets/" + output.name,
                "source_object": object_name,
                "source_object_sha256": source_sha,
                "reference_span_mm": reference_span_mm,
                "dimensions_mm": geometry["dimensions_mm"],
                "raw_triangle_count": len(raw_triangles),
                "lod_triangle_count": len(lod_triangles),
                "lod_vertex_count": len(lod_vertices),
                "lod_grid_resolution": grid_resolution,
                "asset_size_bytes": output.stat().st_size,
                "no_physical_command_generated": True,
            })
    manifest = {
        "schema_version": "competition_target_assets.v1",
        "source_archive": str(source),
        "source_archive_sha256": sha256(source),
        "source_3mf": package_name,
        "source_units": "millimeter",
        "targets": manifest_targets,
        "no_physical_command_generated": True,
        "physical_command_enabled": False,
    }
    (output_dir / "target_asset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "targets": manifest_targets}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
