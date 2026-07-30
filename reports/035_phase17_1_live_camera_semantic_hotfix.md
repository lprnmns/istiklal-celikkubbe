# Ara Task 17.1 - Live Camera Surrogate Evidence Semantics Hotfix

## Yapılanlar
- Topbar/build etiketi `PHASE 17` olacak şekilde güncellendi.
- OpenCV surrogate kaynak semantiği ayrıştırıldı:
  - Mock kamera: `mock_camera_circle_surrogate`, `camera_source_kind=mock`, `frame_origin=mock_frame`
  - Gerçek kamera: `live_camera_circle_surrogate`, `camera_source_kind=real_camera`, `frame_origin=real_capture`
- Vision runtime status artık mock kamera seçiliyken `effective_adapter=mock_camera_surrogate` döndürüyor; gerçek kamera seçiliyse `live_camera_surrogate` kullanıyor.
- FPS/latency alanları ayrıldı:
  - `camera_fps`
  - `detector_fps`
  - `preprocess_ms`
  - `inference_ms`
  - `postprocess_ms`
  - `total_ms`
- Dashboard Live Target Summary mock/synthetic evidence ile real camera frame evidence ayrımını gösterir hale getirildi.
- Reports/KTR export surrogate summary dosyalarına kamera kaynak kanıt alanları eklendi.
- Logs eventleri mock/live ayrımıyla netleştirildi:
  - `vision.mock_surrogate_started`
  - `vision.mock_surrogate_detection`
  - `vision.live_camera_surrogate_started`
  - `vision.live_camera_surrogate_detection`
  - `vision.surrogate_snapshot_saved`
- Self-Test içinde mock surrogate ve real camera evidence check’leri ayrıldı.
- Backend dependency manifestine `opencv-python-headless` ve `numpy` eklendi.

## Semantik Düzeltme Sonucu
Bu hotfix Phase 17’nin “gerçek kamera” iddiasını netleştirir; mock frame ile çalışan surrogate ve gerçek camera capture birbirinden ayrılmıştır.

Bu çalıştırmada kamera kaynağı mock idi:
- Source: `mock_camera_circle_surrogate`
- Camera source kind: `mock`
- Frame origin: `mock_frame`
- Detector kind: `opencv_circle_surrogate`
- Production YOLO loaded: `false`
- Competition ready: `false`
- Advisory only: `true`
- No physical command generated: `true`

Son KTR export açık şekilde şunu yazıyor:
`Real camera capture not proven in this run.`

## Phase/Build Label Sonucu
- UI topbar: `ISTIKLAL C2 CONSOLE · PHASE 17 · BUILD <hash/dev-local>`
- Release manifest/check script phase alanı: `Phase 17`
- Release build id: `phase17-<commit>`

## First Run Tutarlılığı
- Backend first-run reset/check/mark-complete akışı test edildi.
- Reset sonrası backend status `completed=false`.
- Check sonrası first-run otomatik passed sayılmıyor.
- Mark complete sonrası backend status `completed=true`.
- Frontend topbar ve First Run sayfası `firstRunStore.displayBadge` üzerinden aynı kaynakla gösteriyor.

## Reports/KTR Export Sonucu
Son export klasörü:
`exports/reports/ktr_summary-20260510-190334-924ae5`

`live_camera_surrogate_summary.md` içinde:
- `Camera source kind: mock`
- `Frame origin: mock_frame`
- `Detector kind: opencv_circle_surrogate`
- `Production YOLO loaded: false`
- `Real camera capture not proven in this run.`

KTR 4.3 metni mock frame çıktısının gerçek kamera doğrulaması olarak değerlendirilmediğini açıkça belirtiyor.

## Test/Build Sonuçları
- `uv run pytest -q` -> başarılı, `212 passed`
- `pnpm typecheck` -> başarılı
- `pnpm build` -> başarılı
- `python3 scripts/check_release.py` -> `status: passed`, phase `Phase 17`
- `bash -n release/linux/start_istiklal_c2.sh` -> başarılı
- `bash -n start_linux.sh` -> başarılı

## Manual Smoke
- `/` -> 200
- `/dashboard` -> 200
- `/vision` -> 200
- `/devices` -> 200
- `/models` -> 200
- `/self-test` -> 200
- `/first-run` -> 200
- `/reports` -> 200
- `/interfaces` -> 200
- `/logs` -> 200
- `/api/vision/runtime/status` -> 200
- `/api/camera/runtime/status` -> 200
- `/api/release/status` -> 200
- `/api/reports/status` -> 200

## Screenshot Yolları
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/01_topbar_phase17_build_label.png`
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/02_vision_mock_surrogate_clear_label.png`
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/03_dashboard_source_kind_clear.png`
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/04_self_test_mock_vs_real_camera_checks.png`
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/05_reports_camera_source_evidence.png`
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/06_logs_mock_or_live_surrogate_events.png`
- `reports/screenshots/phase17_1_live_camera_semantic_hotfix/07_interfaces_ktr_camera_source_wording.png`

## Safety Invariant
Korundu:
`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya fiziksel serial command yolu eklenmedi.

## Commit Hashleri
- Önceki commit: `4ae98cd`
- Faz 17.1 commit: `2ca2d38`

## Bilinen Eksikler
- Bu run mock kamera ile kanıtlandı; gerçek kamera capture hâlâ saha/laptop kamera ortamında ayrıca denenmeli.
- Production YOLO modeli yok; competition readiness bilinçli olarak blocked kalıyor.
- Pico telemetry verified değil; hardware telemetry acceptance ayrı görev olarak kalıyor.

## Sonraki Önerilen Task
- Gerçek laptop/USB kamera seçilip `camera_source_kind=real_camera` ve `frame_origin=real_capture` kanıtı alınmalı.
- Faz 18’e geçilmedi.
