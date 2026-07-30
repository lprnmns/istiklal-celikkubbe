# Serial Protocol Safety Boundary

Safety invariant: `no_physical_command_generated=true`

- Phase 36 is telemetry/read-only first.
- `serial_tx_enabled=false` by default.
- `physical_command_enabled=false`.
- Legacy raw commands `SPD`, `LZR`, and `STP` are documented as disabled unsafe/debug commands.
- No motor movement, fire, trigger, servo, GPIO, PWM, STEP/DIR, or hardware-enable path is added.
- `POST /api/pico/protocol/read-sample` parses a provided sample or buffered telemetry; it does not transmit physical commands.

