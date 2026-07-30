# Pico Protocol Safety Boundary

Safety invariant: `no_physical_command_generated=true`

The Pico protocol layer is a professional communication foundation for later hardware acceptance, but Phase 36 remains read-only.

Allowed:

- discover Pico-like serial ports
- parse framed heartbeat packets
- parse telemetry packets
- parse driver/limit/fault state packets
- parse ACK/NACK packets
- ingest telemetry pose into the digital twin

Not allowed:

- live motor movement commands
- fire/trigger/servo actuation
- GPIO/PWM/STEP/DIR/hardware-enable output
- `SPD`, `LZR`, `STP` legacy command TX
- any serial write path for physical control

