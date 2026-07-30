# Phase 54 Hybrid Asset Decision

Hybrid output: `frontend/public/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb`.

Hybrid composition:
- primary colored geometry: `ktr1_step_hifi_phase54.glb`
- secondary translucent inspection layer: `ktr1_stl_geometry_phase54.glb`

Diagnostics:
- triangle count: 1515048
- mesh count: 137
- material status: `reconstructed_step_materials_plus_geometry_shadow_layer`

Default decision: `STEP HiFi` is selected as the default asset. Hybrid remains available in the Asset selector because it can reveal possible missing/hidden weapon geometry through the translucent STL evidence layer, but it is visually busier and therefore not the best default FreeCAD-match presentation.

UI asset selector modes:
- STEP HiFi
- STL Geometry
- Hybrid Fidelity
- Previous GLB
- FreeCAD Match

Evidence: `browser_hybrid_same_angle.png`, `asset_compare_selector_visible.png`, `previous_glb_vs_fixed_glb_comparison.png`.

Safety boundary: UI/asset-pipeline only. physical_command_enabled=false, serial_tx_enabled=false, no_physical_command_generated=true. No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path was added.
