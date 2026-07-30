# Phase 25 - Legacy Perception Migration

## Amaç

Legacy stable tracker audit çıktılarından yalnızca güvenli perception/evidence bilgileri yeni İSTİKLAL C2 Console içine advisory preset olarak taşındı. Bu faz tracking-to-motion veya physical control fazı değildir.

## Kaynaklar

- `reports/049_legacy_tracker_audit.md`
- `reports/legacy_tracker_config_inventory.json`
- `reports/legacy_to_istiklal_migration_plan.md`
- `reports/legacy_safety_boundary_review.md`
- `reports/legacy_perception_candidates.json`
- `reports/legacy_serial_telemetry_candidates.json`

## Taşınan Güvenli Bilgiler

- Kamera profil adayları: camera_index, çözünürlük, FPS.
- HSV/red-pink OpenCV contour fallback aralıkları.
- Blur/morphology/min_area/circularity metadata.
- Target selection metadata: closest_to_crosshair, largest_area, Kalman/smoothing notları.
- FPS/latency overlay metadata.
- Data Lab annotation class adayları: red_balloon, blue_balloon.

## Taşınmayan Bilgiler

- Motor hareket komutları.
- Servo, fire/trigger/shoot/release yolları.
- GPIO/PWM/STEP/DIR çıkışları.
- TMC2209 enable/current değişiklikleri.
- Pico/Arduino serial write/TX yolları.
- hardware enable veya physical command path.

## Backend/UI Çıktısı

Yeni advisory endpointler:

- `GET /api/vision/legacy-presets`
- `GET /api/vision/legacy-presets/{preset_id}`

Vision ekranına Legacy Perception Presets kartı eklendi. Kart preset sayısı, aktif advisory preset, kaynak audit dosyası, HSV aralıkları, target selection ve Kalman metadata bilgisini gösterir.

## Safety Kanıtı

- advisory_only=true
- no_physical_command_generated=true
- physical_command_enabled=false
- Safety invariant: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false

## Commit

- Source commit before final phase commit: 29e8507

## Doğrulama Sonuçları

- `uv run pytest -q`: passed
- `pnpm --dir frontend typecheck`: passed
- `pnpm --dir frontend build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed
- Manual smoke: `/vision`, `/data-lab`, `/reports`, `/logs`, `/dashboard`, `/api/vision/legacy-presets`, `/api/vision/real-camera/status`, `/api/vision/real-camera/latest`, `POST /api/vision/real-camera/capture-evidence` returned HTTP 200.

## Screenshot Klasörü

- `reports/screenshots/phase25_26_legacy_perception_real_camera/`

## Bilinen Eksikler

- Gerçek kamera kanıtı bu çalıştırmada alınmadıysa endpoint kontrollü `real_camera_not_available` evidence üretir; gerçek laptop/USB kamera takıldığında ayrıca saha acceptance yapılmalıdır.
- Eski PID/motor/TMC/serial-write yolları bu fazda taşınmadı; ileride ayrı bench safety gate gerekir.

no_physical_command_generated=true
