# Phase 28.1 Safety Boundary Check

Phase 28.1 is a pause gate. It does not add runtime control logic. It records that the project has reached a hardware-dependent acceptance boundary and must wait for real Pico/Arduino and camera hardware before proceeding.

## Safety Invariant

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

## Canonical Proof

`no_physical_command_generated=true`

## Forbidden Paths

The following paths remain forbidden and were not added:

- serial write
- Pico command TX
- motor jog
- step pulse
- DIR pin change
- PWM/GPIO output
- TMC current write
- hardware enable
- fire/trigger/shoot
- `physical_command_enabled=true`

## Allowed Phase 28 Evidence Paths

- serial port list
- RX-only telemetry read
- heartbeat/firmware parsing when the device publishes telemetry by itself
- disconnected/not_available evidence
- real camera evidence capture when camera hardware exists
- Data Lab export
- Reports/KTR export
- logs

## Pause Decision

Faz 29 should not start until the following have been completed with real hardware:

1. Pico/Arduino serial port appears in read-only discovery.
2. RX-only status proves `rx_only=true` and `tx_disabled=true`.
3. Telemetry evidence is captured without serial write/TX.
4. Real camera evidence is captured and not confused with mock/surrogate evidence.
5. Direction calibration profile is reviewed before any future movement gate.

No physical command was executed. This is documentation and acceptance planning only.

`no_physical_command_generated=true`
