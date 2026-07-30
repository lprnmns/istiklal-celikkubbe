# Faz 12 - Safe Hardware Discovery ve Read-Only Pico Telemetry Raporu

## Yapılanlar

- `feature/phase12-safe-hardware-discovery` branch'i açıldı.
- PySerial tabanlı transport altyapısı eklendi.
- `mock` ve `real_readonly` transport modları net ayrıldı.
- Hardware discovery config bayrakları eklendi.
- `physical_command_enabled`, `allow_physical_motion`, `allow_physical_fire` güvenlik validasyonları eklendi.
- Read-only hardware API endpointleri eklendi.
- JSON-line read-only telemetry parser eklendi.
- Invalid JSON ve unknown message warning/error akışı eklendi.
- Riskli komutlar için Phase 12 blocker eklendi.
- Pico ekranına Real Hardware Discovery paneli eklendi.
- Serial ekranında Real Read-Only modu ve TX disabled davranışı gösterildi.
- Dashboard'a Hardware Status kartı eklendi.
- Self-test'e hardware discovery/read-only/risky blocker adımları eklendi.
- WebSocket eventleri eklendi: `hardware.status`, `hardware.telemetry`, `hardware.warning`, `hardware.error`, `hardware.risky_command_blocked`.
- Dokümantasyon eklendi: `docs/hardware_discovery_phase12.md`.
- Screenshot kanıtları üretildi.

## Değiştirilen dosyalar

- `backend/app/api/hardware.py`
- `backend/app/api/routes_ws.py`
- `backend/app/main.py`
- `backend/app/schemas/config.py`
- `backend/app/schemas/hardware.py`
- `backend/app/schemas/self_test.py`
- `backend/app/schemas/serial.py`
- `backend/app/services/hardware_service.py`
- `backend/app/services/runtime_state.py`
- `backend/app/services/self_test_service.py`
- `backend/app/services/serial_service.py`
- `backend/app/transports/*`
- `backend/pyproject.toml`
- `backend/uv.lock`
- `backend/tests/test_config.py`
- `backend/tests/test_hardware_phase12.py`
- `config/config.yaml`
- `docs/hardware_discovery_phase12.md`
- `frontend/src/api/hardware.ts`
- `frontend/src/stores/hardwareStore.ts`
- `frontend/src/types/hardware.ts`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/stores/serialStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/selfTest.ts`
- `frontend/src/types/serial.ts`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/PicoView.vue`
- `frontend/src/views/SerialView.vue`
- `reports/screenshots/phase12_hardware_discovery/*`

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
  - `/api/hardware/capabilities`: 200
  - `/api/serial/status`: 200

## Commit hashleri

- `e0f79a4 feat: add safe hardware discovery and read-only telemetry`

## Read-only hardware discovery özeti

Yeni `/api/hardware/*` endpointleri serial port tarama, read-only bağlantı, telemetry okuma, capability gösterimi ve disconnect akışını sağlıyor.

Varsayılan config güvenli:

- `hardware_discovery_enabled=false`
- `physical_command_enabled=false`
- `allow_real_serial_readonly=false`
- `allow_physical_motion=false`
- `allow_physical_fire=false`
- `serial.transport_mode=mock`
- `serial.real_serial_readonly=true`
- `serial.auto_connect=false`

Demo/screenshot sırasında geçici config ile yalnızca read-only discovery açıldı. `physical_command_enabled=false` kaldı.

## Transport mode özeti

- `mock`: varsayılan geliştirme ve test modu.
- `real_readonly`: gerçek serial port açılabilir, yalnız Pico -> PC telemetry okunur.
- `real_command_disabled`: gelecekteki ayrım için enum seviyesinde tutuldu; bu fazda komut gönderimi yok.

Read-only modda backend hiçbir DISARM, motor, servo, STEP/DIR/PWM veya fire komutu göndermez.

## Risky command blocker özeti

Read-only modda şu komutlar kesin reddedilir:

- `fire_request`
- `jog_motor`
- `set_motor_target`
- `set_servo_position`
- `set_servo`
- `enable_driver`
- `set_pin`
- `pwm_write`
- `step_pulse`

Reddedilen response:

- `accepted=false`
- `reason=physical_commands_disabled_in_phase12_readonly`
- `no_physical_command_generated=true`

## UI ekranları özeti

- Pico ekranı: Real Hardware Discovery paneli, port listesi, read-only connect/disconnect, latest telemetry, raw message, parse errors, heartbeat age ve safe state alanları eklendi.
- Serial ekranı: `MOCK` / `REAL READ-ONLY` ayrımı, physical commands disabled badge'i ve read-only modda TX disabled davranışı eklendi.
- Dashboard: Physical Pico, Mock Pico, Physical commands, telemetry age ve safe state gösteren Hardware Status kartı eklendi.
- Self-Test: hardware discovery config, read-only state, physical command disabled, telemetry-if-connected ve risky blocker adımları eklendi.
- Logs: hardware/risky command blocker eventleri WebSocket latest events akışına dahil edildi.

## Safety invariant kanıtı

- Tüm testler `physical_command_enabled=false` invariant'ı ile geçti.
- Read-only connect response içinde `no_physical_command_generated=true`.
- Riskli `fire_request` denemesi read-only modda reddedildi.
- Self-test sonucu: `critical_failures=0`, `no_physical_command_generated=true`.
- Motion/fire/servo/STEP/DIR/PWM üretimi eklenmedi.

## Screenshot yolları

- `reports/screenshots/phase12_hardware_discovery/01_pico_hardware_discovery_panel.png`
- `reports/screenshots/phase12_hardware_discovery/02_serial_real_readonly_mode.png`
- `reports/screenshots/phase12_hardware_discovery/03_dashboard_hardware_status.png`
- `reports/screenshots/phase12_hardware_discovery/04_self_test_hardware_readonly_steps.png`
- `reports/screenshots/phase12_hardware_discovery/05_logs_risky_command_blocked.png`

## Bilinen eksikler

- Gerçek Pico bağlı değilse telemetry `OPEN_NO_TELEMETRY` warning'i verir; sistem bilinçli olarak crash etmez.
- Bu fazda Pico firmware yazılmadı; beklenen telemetry formatı dokümante edildi.
- Read-only modda PC -> Pico otomatik DISARM dahil hiçbir komut gönderilmez.
- Hardware enable, gerçek motion ve gerçek fire bring-up bu fazın dışında bırakıldı.

## Bir sonraki önerilen task

Bir sonraki adım ayrı bir hardware bring-up planı olmalı: telemetry-only Pico firmware doğrulaması, fiziksel E-stop/limit switch saha testi ve ancak ayrıca onaylanırsa kontrollü command-enable prosedür tasarımı. Faz 12 içinde fiziksel komut yolu açılmadı.
