# Phase 38 Offline Hardware Safety Boundary

Safety invariant: `no_physical_command_generated=true`

The real prototype is not present for Phase 38. This is expected.

Offline expected:
- Pico USB telemetry is not required.
- External USB camera is not required.
- Pan/tilt actuator movement is not tested.
- Fire/servo actuation is not tested.

Hard boundary:
- No motor movement command path was added.
- No fire/trigger/servo command path was added.
- No GPIO/PWM/STEP/DIR/hardware-enable path was added.
- Serial TX remains disabled.
- Fire remains disabled.

Default safety values remain:
- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `dry_run=true`
- `no_physical_command_generated=true`

