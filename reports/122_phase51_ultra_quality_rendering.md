# Phase 51 - Ultra Quality Rendering

Quality modes:

- `quality=ultra`: 60 FPS target, antialias, pixel ratio up to 2, ACES tone mapping, stronger lighting, shadows enabled.
- `quality=high`: 30 FPS target, antialias, good lighting, real model.
- `quality=balanced`: 15 FPS cap, real model.
- `quality=low`: 10 FPS cap, real model with reduced rendering load.

No quality mode replaces the STEP model with a procedural fallback.

Renderer settings:
- `THREE.SRGBColorSpace`
- `THREE.ACESFilmicToneMapping`
- exposure: 1.25-1.42 depending quality
- HemisphereLight + key/fill/rim lights

no_physical_command_generated=true
