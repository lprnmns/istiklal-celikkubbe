# Phase 46 Tactical Digital Twin Scene

The right-side 3D scene is now a command visualization, not a raw CAD viewer.

## Design Decision

- STL asset remains available as engineering evidence.
- Main cockpit render uses tactical simplified geometry derived from the CAD reference.
- Visible label: `STL-derived tactical twin`.
- The scene does not claim exact CAD or physics simulation.

## Scene Improvements

- Turret visual is larger and cleaner.
- FOV cone remains low-opacity wireframe and no longer dominates the model.
- Scene has perspective grid, range rings, optical axis, launcher reference axis, target marker, no-go reference and 30 mm offset.
- Target card is compact: Target, BALON confidence, relative depth.

## Performance

No shadows or postprocessing were added. KTR demo remains capped at 10 FPS.
