# Phase 39 Cockpit Camera Truthfulness

Safety invariant: `no_physical_command_generated=true`

Phase 39 tightens camera-source wording so the cockpit only claims live laptop camera when a real frame has been captured by the runtime.

Rules implemented:
- `REAL_LAPTOP_CAMERA_LIVE` is displayed as live only when `is_real_camera_evidence=true`.
- If the backend is still waiting for a rendered frame, the cockpit shows `LAPTOP CAMERA FRAME PENDING`.
- Fixture target overlays remain labelled as fixture/surrogate and are not USB acceptance evidence.
- External USB camera absence remains `OFFLINE_EXPECTED`.
- Pico absence remains `OFFLINE_EXPECTED`.

Target labels are clamped inside the camera panel to prevent right-edge clipping.

