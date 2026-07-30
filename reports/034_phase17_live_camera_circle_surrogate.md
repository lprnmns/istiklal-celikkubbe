# Ara Task 17 - Live Camera + OpenCV Circle Surrogate

## Yapılanlar
- OpenCV tabanlı `opencv_live_circle_surrogate` adapter eklendi.
- Adapter gerçek kamera runtime servisinden frame okuyabilir hale getirildi; mock kamera seçiliyken açık şekilde mock/surrogate kaynak kullanıyor.
- Circle detection parametreleri runtime profile içine eklendi: radius, blur/kernel, threshold/edge, min area, circularity, max_det, target color mode, ROI, frame skip ve smoothing.
- Vision UI’da “OpenCV Live Circle Surrogate” seçeneği, parametre paneli ve açık güvenlik badge’leri eklendi.
- Dashboard Live Target Summary, `live_camera_surrogate` / `mock_camera_surrogate` kaynağını ve advisory/no-physical-command durumunu gösterir hale getirildi.
- Self-Test’e live camera surrogate kontrol adımları eklendi.
- Reports/KTR export içine surrogate özet dosyaları ve KTR 4.3 açıklaması eklendi.
- Logs tarafında `vision.surrogate_*` eventleri insan okunur summary ve `no_physical_command_generated=true` kanıtıyla üretiliyor.

## Değiştirilen/Oluşturulan Dosyalar
- `.gitignore`
- `backend/app/services/opencv_live_circle_surrogate.py`
- `backend/app/services/camera_runtime_service.py`
- `backend/app/services/vision_pipeline.py`
- `backend/app/services/vision_runtime_settings_service.py`
- `backend/app/services/runtime_state.py`
- `backend/app/services/self_test_service.py`
- `backend/app/services/report_export_service.py`
- `backend/app/services/interface_inventory_service.py`
- `backend/app/api/vision.py`
- `backend/app/api/routes_ws.py`
- `backend/app/schemas/vision_runtime_settings.py`
- `backend/app/schemas/config.py`
- `backend/tests/test_phase17_live_camera_surrogate.py`
- `frontend/src/views/VisionView.vue`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/types/deviceRuntime.ts`
- `frontend/src/stores/deviceRuntimeStore.ts`
- `scripts/capture_phase17_screenshots.py`
- `reports/screenshots/phase17_live_camera_circle_surrogate/*.png`

## Test/Build Sonuçları
- `uv run pytest -q` -> `210 passed in 23.97s`
- `pnpm typecheck` -> başarılı
- `pnpm build` -> başarılı
- `python3 scripts/check_release.py` -> `status: passed`
- `bash -n release/linux/start_istiklal_c2.sh` -> başarılı
- `bash -n start_linux.sh` -> başarılı

## Manual Smoke
- `/` -> 200
- `/dashboard` -> 200
- `/vision` -> 200
- `/devices` -> 200
- `/models` -> 200
- `/self-test` -> 200
- `/reports` -> 200
- `/interfaces` -> 200
- `/logs` -> 200
- `/api/vision/runtime/status` -> 200
- `/api/camera/runtime/status` -> 200
- `/api/release/status` -> 200
- `/api/reports/status` -> 200

## Backend Surrogate Özeti
- Adapter adı: `opencv_live_circle_surrogate`.
- Effective adapter: `live_camera_surrogate`.
- Production model değildir; `production_ready=false`, `competition_ready=false`.
- Her detection/snapshot event’i `advisory_only=true` ve `no_physical_command_generated=true` taşır.
- Kamera açılamazsa controlled warning üretir; mock kamera seçiliyken mock/surrogate state açık görünür.

## Runtime Parametreleri
- `circle_min_radius`
- `circle_max_radius`
- `circle_blur_kernel`
- `circle_threshold`
- `circle_edge_param`
- `circle_min_area`
- `circle_circularity`
- `circle_target_color_mode`
- `circle_roi_enabled`
- `circle_smoothing`
- `max_det`, `frame_skip`

## UI Özeti
- Vision ekranında surrogate adapter seçimi ve parametre paneli eklendi.
- Görsel uyarılar:
  - `SURROGATE ONLY`
  - `NOT PRODUCTION YOLO`
  - `NO PHYSICAL COMMAND`
  - `UI/PIPELINE TEST ONLY`
- Dashboard hedef özetinde source, circle count, target center, advisory/mock-live ayrımı gösteriliyor.

## Reports/KTR Özeti
Son KTR export klasörü:
`exports/reports/ktr_summary-20260510-184635-46351b`

Eklenen dosyalar:
- `live_camera_surrogate_summary.md`
- `live_camera_surrogate_summary.json`
- `vision_circle_detection_sample.json`
- `snapshot_manifest.json`

KTR doğrulama cümlesi dosyalarda bulundu:
“OpenCV yuvarlak algılayıcı yalnızca arayüz/görüntü aktarımı/overlay/loglama testi içindir; production YOLO veya yarışma modeli değildir.”

## Screenshot Yolları
- `reports/screenshots/phase17_live_camera_circle_surrogate/01_vision_live_circle_surrogate_settings.png`
- `reports/screenshots/phase17_live_camera_circle_surrogate/02_vision_overlay_circle_detection_or_no_detection.png`
- `reports/screenshots/phase17_live_camera_circle_surrogate/03_dashboard_surrogate_target_summary.png`
- `reports/screenshots/phase17_live_camera_circle_surrogate/04_self_test_surrogate_checks.png`
- `reports/screenshots/phase17_live_camera_circle_surrogate/05_reports_surrogate_export.png`
- `reports/screenshots/phase17_live_camera_circle_surrogate/06_logs_surrogate_events.png`
- `reports/screenshots/phase17_live_camera_circle_surrogate/07_interfaces_ktr_surrogate_preview.png`

## Safety Invariant Kanıtı
- `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false` korunmuştur.
- Surrogate adapter, model/camera çıktısını yalnızca advisory metadata olarak üretir.
- Snapshot, detection, self-test ve report export akışlarında fiziksel komut üretilmez.
- `no_physical_command_generated=true` event/report payload’larında korunur.

## Commit Hashleri
- Önceki commit: `08fdb33`
- Faz 17 commit: `76b5f40`

## Bilinen Eksikler
- Gerçek production YOLO modeli hâlâ görüntü işleme ekibinden bekleniyor.
- Gerçek Pico bağlı olmadığı için hardware telemetry acceptance ayrı kalıyor.
- Gerçek laptop/USB kamera ortamında kamera izinleri ve FPS/latency saha bilgisayarında ayrıca doğrulanmalı.
- OpenCV surrogate yarışma tespit modeli değildir; sadece UI/pipeline/overlay/log/snapshot kanıtıdır.

## Sonraki Önerilen Task
- Gerçek production model paketi geldiğinde model handoff acceptance ve gerçek kamera ile inference smoke test yapılmalı.
- Faz 18’e geçilmedi.
