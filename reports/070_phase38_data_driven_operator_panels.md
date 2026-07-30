# Phase 38 Data-Driven Operator Panels

Safety invariant: `no_physical_command_generated=true`

The cockpit bottom panels now use meaningful runtime/offline data instead of repeated placeholder rows.

Panel data rules:
- Device Manager distinguishes laptop camera, external USB camera, Pico, pan actuator, tilt actuator, fire/servo and safety.
- Model / Runtime shows active model, classes, confidence, NMS, tracker and camera source mode.
- Target / Engagement shows selected target, confidence, direction, depth source, tracking and fire-blocked state.
- Scene Plan maps target direction consistently with the camera panel.
- Replay & Evidence reports source type, timestamp and evidence/screenshot path.
- Operator Log reports camera source decisions, Pico `OFFLINE_EXPECTED`, safety events and warnings.

Missing physical hardware is shown as controlled offline state, not a broken cockpit.

