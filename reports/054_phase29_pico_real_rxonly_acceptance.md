# Phase 29 - Pico Real RX-only Hardware Acceptance

## Karar

- Pico real RX-only acceptance: partial
- Selected port: /dev/ttyACM0
- Port count: 34
- Candidate count: 2
- Telemetry frames: 0
- Firmware version: not_available
- Evidence status: not_available

## Bulgular

Host Pico/Arduino seri portunu gördü. RX-only connect denemesi `read_only=true` ile yapıldı. Bu hostta port açma sonucu `DTR/RTS reset behavior may reboot microcontroller on some adapters; no command bytes are sent.; readonly_open_failed:[Errno 13] could not open port /dev/ttyACM0: [Errno 13] Permission denied: '/dev/ttyACM0'` olarak raporlandı. Telemetry frame alınamadığı için kabul sonucu `partial` olarak tutuldu; bu production acceptance değildir.

## Contract Alanları

- rx_only=True
- tx_disabled=True
- serial_write_enabled=false
- command_tx_enabled=false
- physical_command_enabled=false
- no_physical_command_generated=true

## Üretilen Dosyalar

- `reports/pico_real_port_inventory.json`
- `reports/pico_real_readonly_status.json`
- `reports/pico_real_latest_telemetry.json`
- `reports/pico_real_acceptance_result.json`
- `reports/pico_real_rxonly_safety_boundary.md`

## Safety Boundary

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added.

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

`no_physical_command_generated=true`

## Doğrulama

- `uv run pytest -q`: geçti
- `pnpm --dir frontend typecheck`: geçti
- `pnpm --dir frontend build`: geçti
- `python3 scripts/check_release.py`: geçti
- `bash -n release/linux/start_istiklal_c2.sh`: geçti
- `bash -n start_linux.sh`: geçti
- Manual smoke Pico endpoints: HTTP 200

## Son Karar

- Pico real RX-only acceptance: partial
- Gerekçe: Port host tarafından görüldü, ancak bu hostta `/dev/ttyACM0` read-only open permission nedeniyle telemetry frame alınamadı.
- serial_write_enabled=false
- command_tx_enabled=false
- physical_command_enabled=false
- no_physical_command_generated=true
