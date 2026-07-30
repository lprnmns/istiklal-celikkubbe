# Phase 61 Tactical Digital Operation Scene

Phase 61 replaces the previous realistic/desert range attempt with a tactical digital operation scene. The goal is operator readability: camera FOV, selected target direction, fire gate state, and digital twin status.

## Implemented

- Operator title changed to `TAKTİK DİJİTAL SAHNE`.
- Operator subtitle changed to `Kamera görüşü, hedef yönü ve güvenlik kapısı görselleştirmesi`.
- Engineer title changed to `3D KALİBRASYON SAHNESİ`.
- Brown terrain/desert-style environment replaced with a dark tactical grid floor.
- Added cyan center/grid texture, radar range rings, forward scan sector, and abstract dashed horizon lines.
- Reworked platform into a low-profile tactical pedestal with dark metal material and cyan ring detail.
- Operator mode hides asset/debug controls and target STL meshes.
- Operator mode keeps only view selection, Full 3D World, FOV toggle, and Target toggle.
- Camera FOV is a single cyan transparent frustum with cyan dashed/tube edges.
- Selected target uses tactical marker styling instead of a dominant toy aircraft/drone mesh.
- Engagement beam is only rendered for selected targets. Blocked fire gate uses one amber dashed ray; ready state uses one green ray.

## Mode Behavior

- Operator: clean tactical digital scene, one FOV, selected target marker, one engagement beam only when selected.
- Engineer: calibration scene with technical controls retained.
- Debug/CAD: detailed controls and diagnostics remain available outside the operator workflow.

## Safety

Visualization only. No physical command path was added.
