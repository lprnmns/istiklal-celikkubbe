# Phase 54 STL Geometry Fallback

Source: `ktr1.stl`.

Output: `frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54.glb`.

Diagnostics:
- STL format: `ascii`
- triangle count: 200512
- material status: `geometry_only`
- bounding box: `{'min': [-1.875, -0.42, -1.0377362252466131], 'max': [1.875, 2.8945190592141703, 1.0377362252466131]}`

Decision: STL is valid as geometry fallback and comparison evidence, but it has no original material/color data. It is not selected as the default because STEP HiFi better preserves colored panel readability and still exposes the front weapon assembly.

Evidence: `browser_stl_geometry_same_angle.png`, `wireframe_weapon_debug.png`, and `xray_weapon_debug.png`.

Safety boundary: UI/asset-pipeline only. physical_command_enabled=false, serial_tx_enabled=false, no_physical_command_generated=true. No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path was added.
