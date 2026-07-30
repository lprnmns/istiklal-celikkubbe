# Phase 36 ISTIKLAL Serial Protocol v1

Safety invariant: `no_physical_command_generated=true`

## Completed

- Added `ISTIKLAL Serial Packet Protocol v1` as a framed binary PC/Pico telemetry protocol.
- Added pure Python codec functions: `encode_packet`, `decode_packet`, `validate_crc`, and stream resynchronization through `decode_stream`.
- Added read-only Pico protocol endpoints:
  - `GET /api/pico/protocol/status`
  - `GET /api/pico/protocol/latest-telemetry`
  - `GET /api/pico/protocol/contract`
  - `POST /api/pico/protocol/read-sample`
- Added digital twin telemetry protocol mapping fields under `/api/digital-twin/state`.
- Added cockpit/debug UI visibility for protocol status, CRC status, heartbeat age, pose source, and physical TX disabled state.
- Added tests for packet roundtrip, CRC mismatch, stream resync, unknown message type, telemetry ingestion, digital twin fallback, and safety boundary.

## Safety Boundary

Phase 36 is telemetry/read-only first. It does not add live motor movement, fire, trigger, servo, GPIO, PWM, STEP/DIR, hardware-enable, or legacy raw physical command TX paths.

Explicitly disabled legacy commands:

- `SPD`
- `LZR`
- `STP`

Canonical proof fields:

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

## KTR Value

The protocol creates a professional foundation for later hardware acceptance while keeping this phase safe. It supports discovery, heartbeat, telemetry parsing, ACK/NACK parsing, fault/status parsing, and digital twin pose ingestion without transmitting physical commands.

The digital twin can now distinguish telemetry pose from tracker estimate or fixture pose. If telemetry is missing, the cockpit remains honest and shows `telemetry_missing` with fallback pose source.

## Validation

- `uv run pytest -q`: passed
- `pnpm --dir frontend typecheck`: passed
- `pnpm --dir frontend build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed

Manual smoke:

- `/cockpit`: HTTP 200
- `/debug`: HTTP 200
- `/evidence`: HTTP 200
- `/api/digital-twin/state`: HTTP 200, `telemetry_protocol.protocol_version=1`
- `/api/pico/protocol/status`: HTTP 200, `serial_tx_enabled=false`, `physical_tx_disabled=true`
- `/api/pico/protocol/latest-telemetry`: HTTP 200
- `/api/pico/protocol/contract`: HTTP 200
- `/api/person-safety/status`: HTTP 200
