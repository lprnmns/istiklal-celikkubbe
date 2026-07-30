# Ara Task 12.2 - Telemetry-only Pico Firmware ve Read-only Acceptance

## Yapılanlar

- `firmware/pico2_telemetry_only/` altında MicroPython tabanlı telemetry-only firmware iskeleti eklendi.
- Firmware dokümantasyonu ve JSON-line telemetry protokolü yazıldı.
- Backend hardware parser `firmware_version`, `safe_state`, `physical_outputs_enabled`, `timestamp_ms`, `limits`, E-stop, driver ve pan/tilt step alanlarını okuyacak şekilde genişletildi.
- Hardware state ayrımı netleştirildi: `port_open`, `telemetry_received`, `pico_verified`, `telemetry_firmware_detected`, `physical_commands_disabled`.
- Connection state isimleri netleştirildi: `PORT_OPEN_NO_TELEMETRY`, `READONLY_CONNECTED_UNVERIFIED`, `PICO_READONLY_VERIFIED`, `MOCK_READONLY_CONNECTED`.
- Serial ve Pico UI mock/real read-only ayrımını daha açık gösterecek şekilde güncellendi.
- Self-test hardware adımlarına Pico telemetry firmware detection, Pico verification, physical outputs disabled, telemetry age ve read-only path kontrolleri eklendi.
- Riskli hardware command blocker için read-only kanıt endpoint'i eklendi: `POST /api/hardware/block-risky-command`.
- Gerçek Pico bağlı olmadığı için real Pico acceptance tamamlanmış sayılmadı; no-pico durumu ve controlled `MOCK_READONLY` akışı raporlandı.

## Firmware özeti

- Dosya: `firmware/pico2_telemetry_only/main.py`
- Çalışma modu: USB serial JSON-line telemetry, 2 Hz.
- Komut işleme: Yok.
- GPIO output: Yok.
- PWM/STEP/DIR/servo/tetik/atış: Yok.
- Firmware safety alanı: `physical_outputs_enabled=false`.

## Gerçek Pico bağlı mıydı?

Hayır. Test ortamında 32 adet `/dev/ttyS*` portu görüldü; Pico/RP2040/RP2350/Raspberry Pi/Pico VID adayı bulunmadı.

Bu nedenle Faz 12.2 real Pico acceptance **tamamlanmış sayılmadı**. Firmware ve UI/backend hazırlığı tamamlandı; gerçek Pico takıldığında aynı acceptance yeniden çalıştırılmalı.

## Kullanılan port

- Gerçek port: Yok.
- Controlled UI/backend smoke: `MOCK_READONLY`.
- `MOCK_READONLY` sonucu: `MOCK_READONLY_CONNECTED`, `transport_source=mock`, `pico_verified=false`, `telemetry_received=false`.

## Telemetry sonucu

- Gerçek Pico telemetry alınamadı.
- Telemetry firmware doğrulanamadı.
- Backend no-telemetry durumunda çökmedi.
- Controlled state: `telemetry_received=false`, `physical_command_enabled=false`, `no_physical_command_generated=true`.

## Pico verification sonucu

- Gerçek Pico yok: `pico_verified=false`.
- Verification için beklenen koşullar:
  - `device=pico2`
  - `firmware_version=telemetry-only-*`
  - `physical_outputs_enabled=false`

## Risky command blocker sonucu

Şu komutlar blocker üzerinden reddedildi:

- `fire_request`
- `jog_motor`
- `set_motor_target`
- `set_servo_position`
- `enable_driver`
- `step_pulse`
- `pwm_write`

Her response `accepted=false`, `reason=physical_commands_disabled_in_phase12_readonly`, `no_physical_command_generated=true` döndürdü.

## Self-test sonucu

- Run ID: `selftest-af35b0db0a`
- Status: `warning`
- Readiness: `demo_ready`
- Critical failures: `0`
- Warnings: `4`
- `no_physical_command_generated=true`
- Self-test raporu:
  - `reports/self_tests/self_test_20260509_120251_selftest-af35b0db0a.md`
  - `reports/self_tests/self_test_20260509_120251_selftest-af35b0db0a.json`

Warning sebebi: Gerçek Pico ve telemetry firmware bağlı olmadığı için verification adımları pass değil warning durumunda kaldı.

## Safety invariant kanıtı

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- `allow_physical_motion=false`
- `allow_physical_fire=false`
- `no_physical_command_generated=true`

Firmware tarafında GPIO, PWM, STEP/DIR, servo, tetik veya atış output'u yoktur.

## Screenshot yolları

- `reports/screenshots/phase12_telemetry_firmware_acceptance/01_firmware_readme_or_file.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/02_ports_pico_candidate_real.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/03_pico_readonly_verified.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/04_telemetry_fields_visible.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/05_serial_real_readonly_verified.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/06_risky_commands_blocked_real_pico.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/07_self_test_pico_verified.png`
- `reports/screenshots/phase12_telemetry_firmware_acceptance/08_logs_pico_telemetry_events.png`

Not: Gerçek Pico bağlı olmadığı için bu screenshotlar no-candidate/not-verified durumunu ve controlled mock-read-only ayrımını gösterir.

## Test/build sonuçları

- Backend: `uv run pytest -q` geçti.
- Backend collection: `159 tests collected`.
- Frontend: `pnpm typecheck` geçti.
- Frontend: `pnpm build` geçti.
- Manual smoke:
  - `/` -> 200
  - `/pico` -> 200
  - `/serial` -> 200
  - `/self-test` -> 200
  - `/logs` -> 200
  - `/api/hardware/status` -> 200
  - `/api/hardware/serial/ports` -> 200
  - `/api/hardware/telemetry` -> 200

## Commit hashleri

- Acceptance commit: `feat: add telemetry-only pico firmware and verified read-only flow` (hash final task yanitinda verildi)

## Kalan eksikler

- Gerçek Pico 2 bu ortamda bağlı olmadığı için real Pico acceptance tamamlanmadı.
- Telemetry-only MicroPython `main.py` gerçek Pico'ya yüklenip tekrar test edilmelidir.
- UI screenshotları gerçek Pico verified state'i değil, no-pico/mock-read-only state'i gösteriyor.
- C/C++ Pico SDK production firmware bu fazın kapsamına alınmadı.

## Sonraki önerilen adım

Pico 2'ye `firmware/pico2_telemetry_only/main.py` yüklenip USB ile bağlandıktan sonra Ara Task 12.2 acceptance tekrar çalıştırılsın. Hedef sonuç `PICO_READONLY_VERIFIED`, `telemetry_received=true`, `physical_outputs_enabled=false`, self-test `critical_failures=0` olmalıdır.
