# Ara Task 17.2 - First Run / Release Profile Status Consistency Hotfix

## Yapılanlar
- First Run current state ile historical evidence ayrıldı.
- Backend `FirstRunStatus` içine tekil snapshot alanları eklendi:
  - `current_first_run_status`
  - `current_profile_id`
  - `current_profile_evaluation_status`
  - `last_successful_first_run`
  - `stale_evidence`
- Reset sonrası current status `open`, current profile evaluation `not_evaluated` oluyor.
- Önceden başarılı bir çalışma varsa reset sonrasında current pass gibi gösterilmiyor; `last_successful_first_run` altında historical evidence olarak kalıyor.
- Topbar, Dashboard ve First Run sayfası current status için aynı store/API kaynağını kullanır hale getirildi.
- Dashboard’daki “Release profile: passed” stale fallback’i kaldırıldı; current profile evaluation yoksa `PROFILE EVAL: NOT EVALUATED` gösteriliyor.
- Reports/KTR export metadata ve summary alanlarına current/historical first-run alanları eklendi.

## Current vs Historical Sonucu
- Current readiness state ile historical evidence ayrıldı.
- Stale release profile pass artık current status gibi gösterilmiyor.
- Reset sonrası:
  - `current_first_run_status=open`
  - `current_profile_evaluation_status=not_evaluated`
  - `stale_evidence=true` olabilir, ancak bu yalnızca previous evidence olarak gösterilir.
- Acceptance sonrası:
  - `current_first_run_status=passed`
  - `current_profile_evaluation_status=passed`
  - `stale_evidence=false`

## Reports/KTR Export Sonucu
Export metadata içine eklendi:
- `current_first_run_status`
- `current_profile_id`
- `current_profile_evaluation_status`
- `last_successful_first_run_run_id`
- `last_successful_first_run_profile_id`
- `last_successful_first_run_timestamp`
- `stale_evidence`

Son doğrulanan export:
`exports/reports/ktr_summary-20260511-000623-5c32a4`

Bu export acceptance sonrası üretildi:
- `current_first_run_status=passed`
- `current_profile_evaluation_status=passed`
- `stale_evidence=false`

Backend testleri ayrıca reset sonrası open/not_evaluated + previous evidence ayrımını doğruluyor.

## Test/Build Sonuçları
- `uv run pytest -q` -> başarılı
- `pnpm typecheck` -> başarılı
- `pnpm build` -> başarılı
- `python3 scripts/check_release.py` -> `status: passed`
- `bash -n release/linux/start_istiklal_c2.sh` -> başarılı
- `bash -n start_linux.sh` -> başarılı

## Manual Smoke
- `/` -> 200
- `/dashboard` -> 200
- `/first-run` -> 200
- `/self-test` -> 200
- `/reports` -> 200
- `/vision` -> 200
- `/interfaces` -> 200
- `/logs` -> 200
- `/api/first-run/status` -> 200
- `/api/first-run/report` -> 200
- `/api/reports/status` -> 200
- `/api/reports/exports` -> 200

## Screenshot Yolları
- `reports/screenshots/phase17_2_first_run_status_consistency/01_first_run_reset_open_not_evaluated.png`
- `reports/screenshots/phase17_2_first_run_status_consistency/02_dashboard_open_not_evaluated_no_stale_pass.png`
- `reports/screenshots/phase17_2_first_run_status_consistency/03_first_run_acceptance_passed.png`
- `reports/screenshots/phase17_2_first_run_status_consistency/04_dashboard_passed_after_acceptance.png`
- `reports/screenshots/phase17_2_first_run_status_consistency/05_reports_current_vs_previous_evidence.png`
- `reports/screenshots/phase17_2_first_run_status_consistency/06_topbar_profile_eval_consistent.png`

## Safety Invariant
Korundu:
`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya fiziksel serial command yolu eklenmedi.

## Commit Hashleri
- Önceki commit: `411313e`
- Faz 17.2 commit: `bf33acb`

## Bilinen Eksikler
- Current profile backend tarafında şu an `release_candidate_ready` varsayılanı üzerinden yönetiliyor; gelecekte profile selector backend’e POST ile bağlanabilir.
- Gerçek production YOLO ve Pico telemetry olmadığı için competition readiness blocked/warning ayrımı korunuyor.

## Sonraki Önerilen Task
- Gerçek kamera ile `real_capture` kanıtı ve ardından production model handoff acceptance yapılmalı.
- Faz 18’e geçilmedi.
