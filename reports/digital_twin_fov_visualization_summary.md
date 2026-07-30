# Digital Twin FOV Visualization Summary

Safety invariant: `no_physical_command_generated=true`

## Cockpit Visualization

The right-side digital twin panel now renders:

- Pan/tilt turret pose from read-only state.
- A launcher/camera optical axis indicator.
- A semi-transparent camera FOV frustum.
- Dotted sparse FOV boundary lines.
- Target billboards inside the frustum.
- Target labels with id, class, confidence, and relative range band.
- Selected target highlighting.
- Person safety/no-go overlay when the software safety gate is active.
- Live/replay source badge.
- Pose source badge: telemetry, tracker estimate, or fixture.
- Legend: green tracking, yellow selected/locked, red blocked/no-go/person safety, gray estimated/uncertain.

## Operator Meaning

The view communicates that the physical turret is mirrored in real time while the camera detections are projected into an estimated 3D scene. This supports operator situational awareness, remote monitoring, debugging, and KTR demonstration without modifying the working tracker.

## Boundary

The panel reads `/api/digital-twin/state` and `/api/digital-twin/replay/latest` only. It does not call motion, fire, serial-write, hardware, GPIO, PWM, STEP/DIR, or servo command endpoints.

