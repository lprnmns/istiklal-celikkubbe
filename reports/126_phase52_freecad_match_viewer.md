# Phase 52 - FreeCAD Match Viewer

Phase 52 changes the primary inspection route to a FreeCAD-match viewer. `/cockpit/world?quality=ultra&mode=freecad` now opens a light, CAD-style scene with an OrthographicCamera, strong edge outlines, minimal labels, and the complete `work/ktr1.step` derived GLB centered in frame.

- Source STEP: `work/ktr1.step`
- Browser asset: `frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb`
- Default `/cockpit/world` mode: FreeCAD Match
- Physical command boundary: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`

