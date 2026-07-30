# Phase 50 - STEP to GLB Conversion Pipeline

Pipeline script: `scripts/convert_ktr_step_to_glb.py`

Tool chain used:
- FreeCAD headless console
- STEP geometry import
- FreeCAD tessellation
- dependency-free GLB writer
- material reconstruction by part label and geometry role

Generated metadata:
- selected_asset_type: `REAL_STEP_GLB`
- conversion_method: `freecad_headless_step_tessellation_to_glb_material_reconstruction`
- material_preserved: `false`
- materials_reconstructed: `true`
- color_count: `6`
- mesh_count: `136`
- triangle_count: `406344`

The converter fails explicitly if `ktr1.step` is absent or cannot be imported. It does not silently fall back to STL or a procedural hero model.

no_physical_command_generated=true
