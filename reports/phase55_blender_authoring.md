# Phase 55 Blender Authoring

Result: Blender is not installed in this environment, so Phase 55 did not create Blender-authored empties inside the GLB.

Fallback authoring path:
- FreeCAD imports `work/ktr1.step` and exports a high-fidelity GLB with stable per-part node names.
- `frontend/public/assets/digital-twin/ktr1_kinematics.json` declares visualization-only groups, pivots and anchors.
- The Three.js runtime creates `static_root`, `yaw_pivot`, `yaw_group`, `pitch_pivot`, `pitch_group`, `camera_group`, and `launcher_group` at load time.

Manual Blender pass TODO:
- Install Blender with CAD import support.
- Import the Phase 55 GLB or original STEP-derived mesh.
- Add empties named `yaw_pivot`, `pitch_pivot`, `camera_origin`, `camera_axis`, `launcher_origin`, `launcher_axis`, `target_projection_anchor`, and `no_go_zone_anchor`.
- Parent meshes into static/yaw/pitch/camera/launcher groups and re-export GLB.

Safety: this is visualization-only authoring. No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path, serial TX, or Pico command sender is added.
