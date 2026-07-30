# Ara Task 12.1 - Real Pico Read-Only Acceptance Test

## Yapılanlar

- Faz 12 raporu commit'e alındı.
- Branch doğrulandı: `feature/phase12-safe-hardware-discovery`.
- Port discovery gerçek sistem üzerinde çalıştırıldı.
- Pico aday portu bulunmadığı için gerçek Pico read-only connect yapılamadı.
- UI'da “No Pico candidate found” ve Pico candidate badge görünürlüğü iyileştirildi.
- Kontrollü `MOCK_READONLY` bağlantı ile read-only mode, telemetry unavailable warning ve risky command blocker doğrulandı.
- Serial command response içine `no_physical_command_generated=true` alanı eklendi.
- Self-test read-only telemetry yokken warning üretecek şekilde düzeltildi; critical failure üretmiyor.
- Screenshot kanıtları ve acceptance JSON kayıtları üretildi.

## Pico bağlı mıydı?

Hayır. Sistem port taramasında 32 adet `/dev/ttyS*` seri aygıtı gördü, ancak Pico/RP2040/RP2350/Raspberry Pi/Pico USB VID-PID göstergesi taşıyan aday port bulunmadı.

## Kullanılan port

- Gerçek Pico portu: yok
- Kontrollü read-only acceptance portu: `MOCK_READONLY`

`MOCK_READONLY` yalnız UI, blocker ve telemetry unavailable davranışını göstermek için kullanıldı; fiziksel komut üretmedi.

## Telemetry firmware var mıydı?

Gerçek Pico bağlı olmadığı için telemetry firmware doğrulanamadı.

Sonuç: `Pico telemetry firmware not available`

## Port discovery sonucu

- `GET /api/hardware/serial/ports`: başarılı
- Port count: 32
- Pico candidate count: 0
- UI sonucu: “No Pico candidate found. Connect Pico 2 USB, refresh ports, and keep read-only mode enabled.”
- Sistem crash etmedi.

Acceptance verisi:

- `reports/acceptance_data/phase12_readonly_before.jsonl`

## Read-only connect sonucu

Gerçek Pico olmadığı için gerçek port connect yapılmadı.

Kontrollü `MOCK_READONLY` sonucu:

- accepted: true
- reason: `read_only_serial_opened`
- transport: `real_readonly`
- physical commands: disabled
- no_physical_command_generated: true
- telemetry state: `OPEN_NO_TELEMETRY`

Acceptance verisi:

- `reports/acceptance_data/phase12_readonly_connect.json`

## Telemetry sonucu

Gerçek telemetry alınmadı.

Kontrollü read-only durumda:

- firmware_version: not available
- estop_state: not available
- driver_enabled: false
- pan/tilt steps: 0 / 0
- heartbeat age: not available
- last_error: `telemetry_unavailable`
- sistem crash etmedi

Acceptance verisi:

- `reports/acceptance_data/phase12_readonly_telemetry.json`

## Risky command blocker sonucu

Real read-only moddayken şu komutlar test edildi:

- `fire_request`
- `jog_motor`
- `set_motor_target`
- `set_servo_position`
- `enable_driver`
- `step_pulse`
- `pwm_write`

Tümü şu şekilde reddedildi:

- accepted=false
- reason=`physical_commands_disabled_in_phase12_readonly`
- no_physical_command_generated=true
- physical_command_enabled=false

Acceptance verisi:

- `reports/acceptance_data/phase12_risky_blocker_results.jsonl`

## Self-test sonucu

Self-test acceptance sonucu:

- run_id: `selftest-bfb8e42486`
- status: warning
- readiness_level: demo_ready
- critical_failures: 0
- no_physical_command_generated: true
- `hardware_discovery_config`: passed
- `real_serial_readonly_state`: passed
- `physical_command_disabled`: passed
- `readonly_telemetry_readable`: warning
- `phase12_risky_blocker`: passed

Generated report:

- `reports/self_tests/self_test_20260509_115300_selftest-bfb8e42486.md`
- `reports/self_tests/self_test_20260509_115300_selftest-bfb8e42486.json`

## Safety invariant kanıtı

Başlangıç ve bitiş invariant korundu:

- DISARMED
- NO_FIRE
- dry_run=true
- hardware_enabled=false
- physical_command_enabled=false
- allow_physical_motion=false
- allow_physical_fire=false

Motor hareketi, servo/tetik, atış, STEP/DIR/PWM output veya physical command yolu eklenmedi.

## Screenshot yolları

- `reports/screenshots/phase12_readonly_acceptance/01_ports_no_pico_or_before_connect.png`
- `reports/screenshots/phase12_readonly_acceptance/02_ports_pico_candidate.png`
- `reports/screenshots/phase12_readonly_acceptance/03_pico_readonly_connected.png`
- `reports/screenshots/phase12_readonly_acceptance/04_telemetry_or_unavailable_warning.png`
- `reports/screenshots/phase12_readonly_acceptance/05_risky_command_blocked.png`
- `reports/screenshots/phase12_readonly_acceptance/06_serial_real_readonly_monitor.png`
- `reports/screenshots/phase12_readonly_acceptance/07_self_test_readonly_steps.png`
- `reports/screenshots/phase12_readonly_acceptance/08_logs_hardware_events.png`

Not: Gerçek Pico adayı bulunmadığı için `02_ports_pico_candidate.png` no-candidate durumunu gösterir; sahada Pico takıldığında aynı panel candidate badge gösterecektir.

## Test/build sonuçları

- Backend: `uv run pytest -q` -> 156 passed
- Frontend: `pnpm typecheck` -> başarılı
- Frontend: `pnpm build` -> başarılı
- Manual smoke:
  - `/`: 200
  - `/pico`: 200
  - `/serial`: 200
  - `/self-test`: 200
  - `/logs`: 200
  - `/api/hardware/status`: 200
  - `/api/hardware/serial/ports`: 200
  - `/api/hardware/telemetry`: 200

## Commit hashleri

- Faz 12 raporu: `1d9cc2d docs: add phase 12 hardware discovery report`
- Acceptance commit: `test: verify real pico read-only acceptance` (hash final task yanitinda verildi)

## Kalan eksikler

- Gerçek Pico 2 bu makinede bağlı değildi; gerçek USB port üstünden telemetry doğrulanamadı.
- Telemetry-only firmware sahada Pico'ya yüklendiğinde aynı acceptance tekrar gerçek portla çalıştırılmalı.
- `OPEN_NO_TELEMETRY` durumu bilinçli warning olarak kalır; bu durum firmware yokken beklenen davranıştır.

## Sonraki önerilen hardware bring-up adımı

Sonraki adım hâlâ fiziksel komut içermemeli: önce telemetry-only Pico firmware yüklenip gerçek Pico portunda `firmware_version`, E-stop, driver disabled, pan/tilt step ve heartbeat değerleri doğrulanmalı. Bu doğrulama tamamlanmadan motor/servo/fire bring-up planına geçilmemeli.
