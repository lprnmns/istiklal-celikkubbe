# Phase 43 Cockpit Visual Parity Redesign

Phase 43 focuses only on frontend cockpit visual hierarchy and operator readability. It does not modify the real tracking/detection pipeline and does not add any hardware command path.

Implemented UI changes:

- Header was compacted into a premium C2 top bar: `İSTİKLAL C2 — Digital Twin Cockpit`.
- Status badges were reduced and grouped around operationally relevant states: phase/demo, DISARMED, DRY_RUN, camera mode, Pico status, performance mode, NO-FIRE and NO PHYSICAL COMMAND.
- Main cockpit area now uses a stable two-column visual hierarchy: left camera HUD and right 3D digital twin.
- Bottom panels were kept to operator summaries with short status rows rather than repeated debug-like text.
- A controlled backend warning banner is shown if the backend is disconnected: `Backend bağlantısı yok — canlı veri güncellenmiyor.`
- The bottom safety strip remains the canonical safety anchor: `SYSTEM MODE: DRY_RUN | physical_command_enabled=false | serial_tx_enabled=false | NO PHYSICAL COMMAND GENERATED`.

KTR demo truth remains explicit: fixture data is labelled as fixture and is not presented as live camera evidence.

Safety boundary preserved:

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

No motor/fire/servo/GPIO/PWM/STEP/DIR/hardware-enable path was added.
