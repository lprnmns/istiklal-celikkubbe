# Phase 55 Visual Validation

Phase 55 changes the digital twin from a static STEP viewer into a kinematic, read-only 3D asset runtime. The source asset remains `work/ktr1.step`; the generated browser asset is `/assets/digital-twin/ktr1_kinematic_world_phase55.glb`, and the runtime metadata is `/assets/digital-twin/ktr1_kinematics.json`.

## FreeCAD Match

- Browser view uses the same STEP-derived high-fidelity GLB as the Phase 54 best candidate.
- CAD edge outlines remain available and enabled in FreeCAD Match mode.
- The front weapon/launcher/camera area is inspectable through `Weapon Focus` and `Front Weapon Closeup`.
- The browser view is expected to match Phase 54 better because it no longer treats the model as a flat anonymous mesh; named parts are grouped and inspectable.

## Kinematic Validation

- `static_root`, `yaw_group`, `pitch_group`, `camera_group`, and `launcher_group` exist in `ktr1_kinematics.json`.
- Exact STEP joint hierarchy was not exposed by the installed FreeCAD import. The grouping is heuristic/manual-curated from labels, bounding boxes and geometry roles.
- Yaw preview rotates the runtime yaw group only.
- Pitch preview rotates the runtime pitch group, including the camera and launcher groups.
- Camera/launcher anchors are loaded from the kinematics metadata and remain visualization-only.

## Screenshots

Captured folder: `reports/screenshots/phase55_kinematic_digital_twin/`

Required evidence:
- `freecad_reference.png`
- `browser_freecad_match.png`
- `browser_operator_view.png`
- `browser_front_weapon_closeup.png`
- `browser_yaw_preview_left.png`
- `browser_yaw_preview_right.png`
- `browser_pitch_preview_up.png`
- `browser_pitch_preview_down.png`
- `browser_clean_mode.png`
- `browser_debug_inspector.png`
- `browser_tactical_overlay.png`
- `browser_safety_strip.png`

All required Phase 55 screenshots were generated from the actual `/cockpit` or `/cockpit/world` routes. The screenshots show the kinematic STEP asset as the primary model, visible yaw/pitch preview controls, clean mode without a center-covering debug panel, tactical overlay mode, and debug inspector mode.

## Safety

Yaw and pitch controls are local browser preview controls only. They do not call backend endpoints, send serial traffic, generate Pico packets, or create physical command paths.
