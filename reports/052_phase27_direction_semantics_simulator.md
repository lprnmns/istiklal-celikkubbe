# Phase 27 - Motion Direction Semantics Simulator and Calibration Wizard

## Amaç

Bu faz, gerçek motor hareketinden önce görüntü koordinatı, hedef hata yönü, required camera motion ve expected image response semantiğini güvenli şekilde tanımlar. Sistem operatör gözlemiyle advisory direction calibration profile üretebilir.

## Eklenen Backend Endpointleri

- `GET /api/calibration/direction/status`
- `POST /api/calibration/direction/simulate`
- `POST /api/calibration/direction/record-observation`
- `POST /api/calibration/direction/save-profile`
- `POST /api/calibration/direction/reset`
- `GET /api/calibration/direction/latest`

## UI Özeti

Calibration ekranına Direction Simulator, Operator Observation, Suggested Mapping, Saved Calibration Profile ve Safety Boundary alanları eklendi. Kullanıcı target left/right/up/down/center simüle eder; sistem required camera motion ve expected image response üretir.

## Data Lab / Reports/KTR Evidence

Eklenen dosyalar:

- `direction_calibration_profile.json`
- `direction_simulation_summary.md`
- `direction_observation_log.json`
- `motion_semantics_contract.md`
- `direction_safety_boundary.md`

KTR 4.3 içine `Motion Direction Semantics and Calibration Interface` bölümü eklendi.

## Safety Boundary

Bu faz fiziksel motor testi değildir. Motor, servo, GPIO, PWM, STEP/DIR, TMC current, Pico/Arduino serial write, hardware enable veya fire yolu eklenmedi.

- advisory_only=true
- physical_command_enabled=false
- no_physical_command_generated=true
- Safety invariant: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false

## Doğrulama Sonuçları

- `uv run pytest -q`: passed
- `pnpm --dir frontend typecheck`: passed
- `pnpm --dir frontend build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed
- Manual smoke: `/calibration`, `/data-lab`, `/reports`, `/logs`, `/api/calibration/direction/status`, `/api/calibration/direction/simulate`, `/api/calibration/direction/latest` returned HTTP 200.

## Screenshot Klasörü

- `reports/screenshots/phase27_direction_semantics_simulator/`

## Bilinen Eksikler

- Gerçek motor hareket testi yapılmadı ve bu fazda amaçlanmadı.
- Axis swap şüphesi yalnızca operator observation metadata ile işaretlenir; fiziksel doğrulama ileride ayrı bench micro-jog safety gate ister.

no_physical_command_generated=true
