# Phase 37 Cockpit Visual Parity

Safety invariant: `no_physical_command_generated=true`

Phase 37 rebuilds `/cockpit` into a professional C2 digital-twin operations view while preserving the existing tracking, safety, camera, Pico, reports and telemetry behavior.

Implemented layout:
- Full-width ISTIKLAL C2 Digital Twin Cockpit status bar.
- Large left live camera/HUD panel with crosshair, FOV boundary, target boxes, source badge and person-safety overlay.
- Large right Three.js digital twin panel with turret pose, FOV frustum, optical axis, target markers, pose-source badge and safety/no-go state.
- Bottom operational dashboard panels: Device Manager, Model/Runtime, Engagement, Plan View, Replay/Evidence and Operator Log.
- Persistent bottom safety strip: `SYSTEM MODE: DRY_RUN` and `NO PHYSICAL COMMAND GENERATED`.

Operator-facing safety language:
- Fire state remains NO-FIRE / FIRE-BLOCKED in dry-run mode.
- Pose source is shown as TELEMETRY, TRACKER_ESTIMATE or FIXTURE.
- Real camera, laptop camera and mock/surrogate states are visually distinct.
- Fixture/surrogate camera data is not presented as real evidence.

No physical command path was added. The cockpit remains a read-only visualization and operator-awareness layer for this phase.

