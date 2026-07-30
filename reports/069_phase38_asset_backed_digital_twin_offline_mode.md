# Phase 38 Asset-Backed Digital Twin Offline Mode

Safety invariant: `no_physical_command_generated=true`

The digital twin now exposes an asset contract even when the real Pico/turret is offline.

Asset decision:
- Browser-friendly `.glb` / `.gltf` files are preferred when available.
- `.obj`, `.stl`, `.step` and `.stp` files are inventoried as source/fallback assets.
- If no model asset is available, the Three.js panel renders the procedural turret model and explicitly reports `model asset unavailable`.

Offline pose hierarchy:
1. `telemetry` only when real read-only telemetry exists.
2. `tracker_estimate` from vision/tracker state.
3. `replay_fixture` from replay data.
4. `static_demo_pose` / fixture fallback.

Pico absence is expected in Phase 38 and must not be presented as failed telemetry.

