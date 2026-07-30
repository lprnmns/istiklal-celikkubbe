#!/usr/bin/env python3
"""Generate a Phase 54 high-fidelity STEP-derived GLB without decimation."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from convert_ktr_step_to_glb import PROJECT_ROOT, run_conversion


DEFAULT_SOURCE = PROJECT_ROOT / "work/ktr1.step"
DEFAULT_OUTPUT = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_step_hifi_phase54.glb"
DEFAULT_MANIFEST = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_step_hifi_phase54_manifest.json"
PUBLIC_MANIFEST = PROJECT_ROOT / "frontend/public/assets/digital-twin/asset_manifest.json"


def phase54_patch_manifest(manifest_path: Path, output_path: Path, tolerance: float) -> dict[str, object]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_asset = f"/{output_path.relative_to(PROJECT_ROOT / 'frontend/public')}"
    data.update({
        "phase": 54,
        "selected_asset_type": "REAL_STEP_HIFI_GLB",
        "selected_asset_path": output_asset,
        "preferred_browser_asset": output_asset,
        "output_asset": output_asset,
        "output_asset_absolute": str(output_path),
        "conversion_method": "freecad_headless_step_hifi_tessellation_no_decimation_phase54",
        "conversion_status": "converted_step_hifi_phase54",
        "tessellation_tolerance": tolerance,
        "decimation_used": False,
        "weapon_visibility_status": "candidate_requires_browser_visual_check",
        "front_weapon_assembly_expected": True,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
        "no_physical_command_generated": True,
    })
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--tolerance", type=float, default=1.2)
    parser.add_argument("--update-public-manifest", action="store_true")
    args = parser.parse_args()

    run_conversion(args.source.resolve(), args.output.resolve(), args.manifest.resolve(), args.tolerance)
    data = phase54_patch_manifest(args.manifest.resolve(), args.output.resolve(), args.tolerance)
    if args.update_public_manifest:
        PUBLIC_MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        # The shared converter writes the public manifest as a side effect; restore
        # the previous default until Phase 54 comparison selects a candidate.
        previous = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json"
        if previous.exists():
            shutil.copyfile(previous, PUBLIC_MANIFEST)
    print(json.dumps({
        "output": str(args.output),
        "manifest": str(args.manifest),
        "triangle_count": data.get("triangle_count"),
        "tolerance": args.tolerance,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
