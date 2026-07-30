# Phase 26 - Real Camera Evidence Foundation

## Amaç

Gerçek kamera kanıtını mock/surrogate kanıtından ayıran evidence-only endpointler ve rapor çıktıları eklendi. Kamera yoksa sistem crash etmez ve mock fallback yapmaz; açıkça `real_camera_not_available` evidence döner.

## Endpointler

- `GET /api/vision/real-camera/status`
- `POST /api/vision/real-camera/capture-evidence`
- `GET /api/vision/real-camera/latest`

## Evidence Contract

Her real camera evidence çıktısı şu alanları taşır:

- camera_source
- frame_origin
- detector
- preset_id
- frame_width / frame_height
- fps_estimate
- detections_count
- target_center_metadata
- advisory_only=true
- no_physical_command_generated=true
- physical_command_enabled=false

## Data Lab ve Reports/KTR Entegrasyonu

Eklenen dosyalar:

- `real_camera_evidence_summary.md`
- `real_camera_evidence_latest.json`
- `legacy_perception_presets.json`
- `legacy_perception_migration_summary.md`

KTR 4.3 içine `Legacy Perception and Real Camera Evidence Interface` bölümü eklendi.

## Safety Kanıtı

Real camera evidence yalnızca görüntü işleme metadata üretir. Motor, servo, fire, GPIO, PWM, STEP/DIR, TMC, hardware enable veya physical serial command yolu eklenmedi.

no_physical_command_generated=true

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
