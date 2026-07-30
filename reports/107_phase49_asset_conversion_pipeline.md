# Phase 49 - Asset Conversion Pipeline

`scripts/convert_ktr_asset_to_glb.py` implements the Phase 49 asset pipeline.

Pipeline behavior:

- Locates the KTR STL/CAD candidate assets.
- Reads binary STL without runtime browser parsing.
- Normalizes and centers geometry for operator-scene display.
- Writes `frontend/public/assets/digital-twin/ktr1_operator_hero.glb`.
- Writes `frontend/public/assets/digital-twin/ktr1_operator_hero_manifest.json`.
- Updates `frontend/public/assets/digital-twin/asset_manifest.json`.

Current conversion result:

- Source: `frontend/public/assets/digital-twin/ktr1_binary.stl`
- Output: `/assets/digital-twin/ktr1_operator_hero.glb`
- Triangles before: 200512
- Triangles after: 200512
- Converted size: 14438560 bytes
- Method: `dependency_free_binary_stl_to_glb`

No procedural replacement is used as the default hero scene. If GLB loading fails, the cockpit shows a visible blocker instead of silently pretending a fake model is the real KTR asset.

no_physical_command_generated=true

