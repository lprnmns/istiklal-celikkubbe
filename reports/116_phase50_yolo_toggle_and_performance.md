# Phase 50 - YOLO Toggle and Performance

Camera panel controls preserve the Phase 49 YOLO toggle:
- YOLO ON: detection active
- YOLO OFF: camera-only mode, no live target claim

Quality modes:
- `quality=high`: 30 FPS target, colored STEP model visible
- `quality=balanced`: 15 FPS cap, colored STEP model visible
- `quality=low`: 10 FPS cap, colored STEP model visible

The low mode does not replace the colored STEP model with a fake procedural object.

Performance boundaries:
- No runtime STL parsing
- GLB is loaded by GLTFLoader
- Three.js rendering is capped by quality mode
- metadata polling remains 2 Hz
- no postprocessing requirement is introduced

no_physical_command_generated=true
