# Phase 43 Frontend Performance Stabilization

Phase 43 adds frontend-only performance controls for laptop development mode without changing detection, tracking or backend command logic.

Performance changes:

- Three.js render loop is capped:
  - `BALANCED`: 15 FPS
  - `LOW`: 10 FPS
  - KTR demo fixture mode: 10 FPS
- Render loop skips active rendering work when `document.hidden` is true.
- WebGL pixel ratio is capped lower than raw device pixel ratio to reduce laptop GPU/CPU pressure.
- Digital twin metadata polling is documented and shown as `metadata 2Hz`.
- Main runtime refresh remains throttled and separate from camera frame rendering.
- KTR demo mode can use the simplified digital twin visual to avoid expensive STL-heavy presentation while keeping STL asset evidence truthful.

Performance mode:

- `/cockpit?perf=low`
- `/cockpit?ktr_demo=1&perf=low`

This mode keeps safety/evidence panels intact and reduces 3D render cost. It does not disable safety display and does not fake camera evidence.

No backend detection/tracking pipeline was modified.

Safety boundary preserved:

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
