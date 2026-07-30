#!/usr/bin/env python3
"""Generate FreeCAD-geometry reference PNGs for Phase 51 evidence."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "work/ktr1.step"
DEFAULT_OUTDIR = PROJECT_ROOT / "reports/screenshots/phase51_freecad_fidelity_reference"

WORKER = r'''
from __future__ import annotations

import math
from pathlib import Path

import FreeCAD
import Import
from PIL import Image, ImageDraw

source = Path(__SOURCE__)
outdir = Path(__OUTDIR__)
outdir.mkdir(parents=True, exist_ok=True)

doc = FreeCAD.newDocument("phase51_reference")
Import.insert(str(source), doc.Name)
doc.recompute()

objects = []
mins = [float("inf"), float("inf"), float("inf")]
maxs = [float("-inf"), float("-inf"), float("-inf")]
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
    mins[0] = min(mins[0], bb.XMin)
    mins[1] = min(mins[1], bb.YMin)
    mins[2] = min(mins[2], bb.ZMin)
    maxs[0] = max(maxs[0], bb.XMax)
    maxs[1] = max(maxs[1], bb.YMax)
    maxs[2] = max(maxs[2], bb.ZMax)

center = [(mins[i] + maxs[i]) * 0.5 for i in range(3)]
extent = [maxs[i] - mins[i] for i in range(3)]
scale = 3.75 / (max(extent) or 1.0)

def scene_point(p):
    return ((p.x - center[0]) * scale, (p.z - mins[2]) * scale - 0.42, -(p.y - center[1]) * scale)

def color(label, bb):
    s = (label or "").lower()
    if "kamera" in s:
        return (0, 205, 238)
    if "rulman" in s or "dişli" in s or "disli" in s or "nema" in s:
        return (174, 178, 181)
    if "tabla" in s or "alt gövde" in s or "alt govde" in s:
        return (40, 43, 50)
    if "namlu" in s or (bb.YLength > max(bb.XLength, bb.ZLength) * 2.0 and bb.YLength > 80):
        return (28, 30, 34)
    if "sol" in s or "sağ" in s or "sag" in s or "kapak" in s or "yan gövde" in s or "yan govde" in s or "üst" in s or "ust" in s:
        return (188, 18, 17)
    return (230, 235, 226)

triangles = []
for obj in objects:
    pts, facets = obj.Shape.tessellate(4.5)
    mat = color(getattr(obj, "Label", ""), obj.Shape.BoundBox)
    for tri in facets:
        verts = [scene_point(pts[int(i)]) for i in tri[:3]]
        triangles.append((verts, mat))

def shade(base, normal_factor):
    factor = 0.62 + 0.38 * normal_factor
    return tuple(max(0, min(255, int(c * factor))) for c in base)

views = {
    "freecad_reference_operator.png": ((0.92, 0.22, -0.32), (0.08, 0.96, 0.26)),
    "freecad_reference_front.png": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    "freecad_reference_top.png": ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
}

for name, (right, up) in views.items():
    w, h = 1600, 1000
    projected = []
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for verts, mat in triangles:
        pts2 = []
        depths = []
        for x, y, z in verts:
            sx = x * right[0] + y * right[1] + z * right[2]
            sy = x * up[0] + y * up[1] + z * up[2]
            depth = x * 0.18 + y * 0.34 - z * 0.48
            pts2.append((sx, sy))
            depths.append(depth)
            minx, maxx = min(minx, sx), max(maxx, sx)
            miny, maxy = min(miny, sy), max(maxy, sy)
        projected.append((sum(depths) / 3, pts2, mat))
    margin = 80
    sx = (w - margin * 2) / max(1e-6, maxx - minx)
    sy = (h - margin * 2) / max(1e-6, maxy - miny)
    s = min(sx, sy)
    image = Image.new("RGB", (w, h), (232, 236, 240))
    draw = ImageDraw.Draw(image)
    for depth, pts2, mat in sorted(projected, key=lambda item: item[0]):
        poly = [(margin + (x - minx) * s, h - margin - (y - miny) * s) for x, y in pts2]
        draw.polygon(poly, fill=shade(mat, 0.92), outline=(86, 90, 94))
    draw.rectangle((0, 0, w - 1, h - 1), outline=(120, 128, 136), width=2)
    draw.text((24, 22), f"FreeCAD geometry reference · {source.name} · {name}", fill=(20, 25, 31))
    image.save(outdir / name)

print({"source": str(source), "outdir": str(outdir), "views": list(views)})
'''


def find_freecad() -> str | None:
    for candidate in [shutil.which("freecad"), shutil.which("FreeCAD"), str(Path.home() / ".local/bin/freecad")]:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    args = parser.parse_args()
    freecad = find_freecad()
    if not freecad:
        raise SystemExit("FreeCAD executable not found")
    worker = WORKER.replace("__SOURCE__", repr(str(args.source.resolve()))).replace("__OUTDIR__", repr(str(args.outdir.resolve())))
    with tempfile.NamedTemporaryFile("w", suffix="_phase51_ref.py", delete=False, encoding="utf-8") as handle:
        handle.write(worker)
        worker_path = Path(handle.name)
    try:
        result = subprocess.run([freecad, "--console", str(worker_path)], cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=600)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(result.returncode)
        print(result.stdout.strip())
    finally:
        worker_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
