# Phase 49 - Real KTR Model Hero Scene

Phase 49 replaces the previous procedural/operator-twin hero visual with a real KTR STL-derived browser asset.

- Source asset: `frontend/public/assets/digital-twin/ktr1_binary.stl`
- Converted hero asset: `frontend/public/assets/digital-twin/ktr1_operator_hero.glb`
- Triangle count: 200512 before / 200512 after
- Conversion method: dependency-free binary STL to GLB
- Default cockpit scene mode: `Real Model`

The right cockpit panel now loads the converted real KTR model as the main visual and keeps tactical overlays on top: camera axis, launcher axis, transparent FOV volume, 30 mm camera-to-launcher offset, target projection, no-go zone and range/depth references.

The GLB is a visualization/evidence asset only. It does not create command authority and does not generate hardware output.

Safety invariants:

- physical_command_enabled=false
- serial_tx_enabled=false
- no_physical_command_generated=true

