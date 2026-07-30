# Phase 44 Frontend Performance Mode

Phase 44 keeps the real tracking/detection pipeline untouched and reduces cockpit UI load from the presentation layer.

## Stabilization

- Three.js render loop remains capped:
  - balanced/dev: 15 FPS
  - KTR demo or low performance: 10 FPS
- The render loop pauses active rendering while `document.hidden`.
- Digital twin metadata polling remains separate from the main cockpit refresh.
- Main cockpit runtime refresh remains low frequency and does not run per camera frame.
- Heavy visual effects such as shadows and postprocessing remain disabled.
- KTR demo uses simplified digital twin geometry when appropriate.

## Operator Indicator

The header displays the active performance mode and render cap, for example `PERF LOW / 10 FPS CAP`.

## Safety Boundary

No physical command path was added. `physical_command_enabled=false`, `serial_tx_enabled=false`, and `no_physical_command_generated=true` remain preserved.
