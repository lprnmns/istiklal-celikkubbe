# Phase 37 Cockpit Safety Boundary

Safety invariant: `no_physical_command_generated=true`

Phase 37 is UI, camera-source stabilization and read-only visualization work only.

Explicitly unchanged:
- No live motor movement command path was added.
- No fire/trigger/servo actuation command path was added.
- No GPIO/PWM/STEP/DIR/hardware-enable path was added.
- No physical serial TX path was enabled.
- Existing safety gates remain in place.

Default safety values:
- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `dry_run=true`
- `hardware_enabled=false`
- `NO_FIRE` / `FIRE_BLOCKED` remains visible in the cockpit.

The cockpit can visualize camera, target, telemetry and digital twin state, but it has no new physical command authority in this phase.

