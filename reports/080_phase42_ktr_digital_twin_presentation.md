# Phase 42 KTR Digital Twin Presentation

The digital twin cockpit presents a read-only operational view that connects perception metadata to a 3D scene. It shows the STL-derived turret visualization, camera FOV, camera optical axis, launcher reference axis, 30 mm camera-to-launcher offset, target projection ray and estimated target depth.

The visual is intentionally labelled as a digital twin/evidence layer. It does not provide a fire solution and does not control hardware.

Modes:

- `FIXTURE_KTR_DEMO`: deterministic explanation mode for KTR screenshots; not live target evidence.
- Laptop camera development frame: UI verification only when available.
- External USB camera: offline expected in the current environment.
- Pico telemetry: offline expected in the current environment.

Projection logic:

- 2D bbox center maps to normalized x/y.
- Bbox area ratio maps to relative depth (`near`, `mid`, `far`).
- Target marker size changes with relative depth.
- Camera-to-target ray and aim-reference ray are visualized separately.

Safety boundary: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`.
