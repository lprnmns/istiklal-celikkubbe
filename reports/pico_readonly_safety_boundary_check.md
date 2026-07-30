# Pico Read-Only Safety Boundary Check

Phase 28 adds Pico/Arduino serial discovery and telemetry evidence in RX-only mode.

- serial write: disabled
- Pico command TX: disabled
- motor jog: disabled
- STEP/DIR/PWM/GPIO output: disabled
- TMC current write: disabled
- hardware enable: disabled
- fire/trigger/shoot: disabled
- physical_command_enabled=false
- no_physical_command_generated=true

The connection path opens a serial port only for reading telemetry that the device publishes by itself. It does not send startup commands, firmware commands, motor commands, direction tests or safety-state changes.

Safety invariant remains:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`
