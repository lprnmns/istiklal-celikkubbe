# Phase 54 Asset Inventory

Scope: KTR STEP/STL/GLB assets discovered in `work/`, project root, and `frontend/public/assets/digital-twin/`.

| Path | Ext | Size | Loads | Geometry | Materials | Weapon/front evidence |
| --- | --- | ---: | --- | --- | --- | --- |
| `frontend/public/assets/digital-twin/ktr1_binary.stl` | `.stl` | 10025684 | True | triangle_count=200512 | False | True |
| `frontend/public/assets/digital-twin/ktr1_colored_step_hero.glb` | `.glb` | 29333316 | True | mesh_count=136<br>triangle_count=406344 | True | True |
| `frontend/public/assets/digital-twin/ktr1_colored_step_hero_manifest.json` | `.json` | 4695 | True | n/a | n/a | False |
| `frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb` | `.glb` | 31990320 | True | mesh_count=136<br>triangle_count=443246 | True | True |
| `frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json` | `.json` | 5795 | True | n/a | n/a | False |
| `frontend/public/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb` | `.glb` | 109161316 | True | mesh_count=137<br>triangle_count=1515048 | True | True |
| `frontend/public/assets/digital-twin/ktr1_hybrid_fidelity_phase54_manifest.json` | `.json` | 6370 | True | n/a | n/a | False |
| `frontend/public/assets/digital-twin/ktr1_operator_hero.glb` | `.glb` | 14438560 | True | mesh_count=1<br>triangle_count=200512 | True | True |
| `frontend/public/assets/digital-twin/ktr1_operator_hero_manifest.json` | `.json` | 2651 | True | n/a | n/a | False |
| `frontend/public/assets/digital-twin/ktr1_step_hifi_phase54.glb` | `.glb` | 94723640 | True | mesh_count=136<br>triangle_count=1314536 | True | True |
| `frontend/public/assets/digital-twin/ktr1_step_hifi_phase54_manifest.json` | `.json` | 5970 | True | n/a | n/a | False |
| `frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54.glb` | `.glb` | 14437792 | True | mesh_count=1<br>triangle_count=200512 | True | True |
| `frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54_manifest.json` | `.json` | 1619 | True | n/a | n/a | False |
| `ktr1.step` | `.step` | 27237470 | True | advanced_face_count=15600<br>closed_shell_count=46 | True | True |
| `ktr1.stl` | `.stl` | 57136553 | True | triangle_count=200512 | False | True |
| `reports/cockpit_phase40_ktr_demo_contract.json` | `.json` | 636 | True | n/a | n/a | False |
| `reports/cockpit_phase41_operator_panel_contract.json` | `.json` | 878 | True | n/a | n/a | False |
| `reports/digital_twin_asset_contract.json` | `.json` | 643 | True | n/a | n/a | False |
| `reports/digital_twin_asset_registry.json` | `.json` | 2536 | True | n/a | n/a | False |
| `reports/digital_twin_asset_transform_contract.json` | `.json` | 674 | True | n/a | n/a | False |
| `reports/digital_twin_ktr_story_contract.json` | `.json` | 1574 | True | n/a | n/a | False |
| `reports/digital_twin_live_state_contract.json` | `.json` | 927 | True | n/a | n/a | False |
| `reports/digital_twin_phase32_replay_fixture.json` | `.json` | 6196 | True | n/a | n/a | False |
| `reports/digital_twin_phase39_asset_manifest.json` | `.json` | 395 | True | n/a | n/a | False |
| `reports/digital_twin_phase39_scene_contract.json` | `.json` | 451 | True | n/a | n/a | False |
| `reports/digital_twin_phase40_asset_manifest.json` | `.json` | 607 | True | n/a | n/a | False |
| `reports/digital_twin_phase40_scene_contract.json` | `.json` | 884 | True | n/a | n/a | False |
| `reports/digital_twin_projection_contract.json` | `.json` | 1680 | True | n/a | n/a | False |
| `reports/digital_twin_projection_semantics_contract.json` | `.json` | 566 | True | n/a | n/a | False |
| `reports/digital_twin_state_contract.json` | `.json` | 3700 | True | n/a | n/a | False |
| `reports/hardware_required_next_steps.json` | `.json` | 2168 | True | n/a | n/a | False |
| `reports/operator_panel_data_contract.json` | `.json` | 882 | True | n/a | n/a | False |
| `reports/phase50_colored_step_asset_contract.json` | `.json` | 424 | True | n/a | n/a | False |
| `reports/phase50_step_conversion_manifest_contract.json` | `.json` | 511 | True | n/a | n/a | False |
| `reports/phase51_freecad_visual_reference_contract.json` | `.json` | 342 | True | n/a | n/a | False |
| `reports/phase52_freecad_match_contract.json` | `.json` | 384 | True | n/a | n/a | False |

Notes:
- STEP color availability is inferred from `COLOUR_RGB` records; installed headless FreeCAD still may not expose face colors directly.
- STL/STR files do not carry material data, but high triangle count can preserve weapon geometry for geometry-only fallback.
- No physical command, serial TX, motor, fire, servo, GPIO, PWM, STEP/DIR, or hardware-enable path is created by this audit.
