# Ara Task 9.1 Raporu - Data Lab E2E Acceptance Test

## Yapılanlar

- Faz 9 raporu Git'e alındı.
- Data Lab E2E kabul senaryosu backend API ve çalışan frontend üzerinden doğrulandı.
- Model registry, metadata-only model upload, unsupported extension rejection, session recording, snapshot, annotation, YOLO export, replay, dataset health ve logs akışları test edildi.
- Screenshot kanıtları `reports/screenshots/phase9_e2e/` altında üretildi.
- Küçük stabilizasyon düzeltmeleri yapıldı:
  - Backend test fixture'ı `data/` ve `models/` runtime klasörlerini repo içinde kirletmeyecek şekilde `tmp_path` storage kullanıyor.
  - Data Lab sekmeleri screenshot/manual smoke için `?tab=` query parametresiyle açılabiliyor.
  - Annotation Review belirli session için `?session=` query parametresini okuyabiliyor.
  - Dataset export listesi image/label count ve `data_yaml_path` döndürüyor.
  - Logs ekranı `?search=` query parametresiyle filtrelenebiliyor.

## E2E senaryo sonucu

- OpenCV circle detector test adapter registry'de göründü ve active test adapter olarak doğrulandı.
- Dummy `e2e_model.yaml` metadata kaydı oluşturuldu.
- Unsupported `bad.exe` upload denemesi 400 ile reddedildi.
- Eksik class metadata için `class_names_missing` warning'i alındı.
- `phase9_e2e_capture` session başlatıldı, snapshot alındı, detection event kaydedildi ve session stop edildi.
- `helicopter` class annotation kaydedildi, `verified_by_operator=true` olarak UI'da göründü.
- `e2e_test_dataset-v0` YOLO export üretildi.
- `data.yaml`, image, label ve metadata dosyaları oluştu.
- Replay load/play/pause/step çalıştı.
- Dataset Health sessions/images/annotations/class/distance/lens/model dağılımlarını güncel gösterdi.
- Logs ekranında dataset event search/detail görünümü doğrulandı.
- Safety invariant doğrulandı: serial log sayısı 0, `no_physical_command_generated=true`.

## Üretilen dosya yolları

- E2E state: `reports/screenshots/phase9_e2e/e2e_state.json`
- Session JSON: `data/sessions/session-20260508-230307-06d120/session.json`
- Snapshot image: `data/sessions/session-20260508-230307-06d120/snapshots/frame-000001.jpg`
- Snapshot metadata: `data/sessions/session-20260508-230307-06d120/frames/frame-000001.json`
- YOLO export: `data/exports/yolo/e2e_test_dataset-v0`
- YOLO data.yaml: `data/exports/yolo/e2e_test_dataset-v0/data.yaml`
- YOLO label: `data/exports/yolo/e2e_test_dataset-v0/labels/val/frame-000001.txt`

Not: `data/` ve `models/` runtime çıktıları Git'e alınmadı; screenshot kanıtları commit'e alındı.

## Screenshot yolları

- `reports/screenshots/phase9_e2e/01_models_registry_active_adapter.png`
- `reports/screenshots/phase9_e2e/02_capture_session_started.png`
- `reports/screenshots/phase9_e2e/03_session_detail_snapshot.png`
- `reports/screenshots/phase9_e2e/04_annotation_review_verified.png`
- `reports/screenshots/phase9_e2e/05_yolo_export_result.png`
- `reports/screenshots/phase9_e2e/06_replay_loaded.png`
- `reports/screenshots/phase9_e2e/07_dataset_health.png`
- `reports/screenshots/phase9_e2e/08_logs_filtered_dataset_events.png`

## Test/build sonuçları

- `cd backend && uv run pytest -q`: 117 passed.
- `cd frontend && pnpm typecheck`: başarılı.
- `cd frontend && pnpm build`: başarılı.
- Manual smoke:
  - `/data-lab`: 200
  - `/vision`: 200
  - `/logs`: 200
  - `/api/models`: 200
  - `/api/sessions`: 200
  - `/api/datasets`: 200
  - `/api/replay/status`: 200

## Commit hashleri

- `6fcc76b` - `docs: add phase 9 model dataset replay report`
- `fe5d71d` - `test: verify data lab e2e workflow`

## Bulunan ve düzeltilen buglar

- Backend testleri repo runtime `data/` ve `models/` klasörlerini kirletiyordu. Test fixture geçici storage'a taşındı.
- Preview portu CORS dışında olduğu için screenshotlarda API fetch hatası görüldü. Kanıt screenshotları backend CORS listesinde olan Vite dev portu `5173` üzerinden tekrar alındı.
- Annotation Review reload sonrası doğru session annotationlarını göstermiyordu. `?session=` query desteği eklendi.
- YOLO Export reload sonrası image/label count görünmüyordu. Export list endpoint'i ve frontend gösterimi genişletildi.

## Kalan eksikler

- Binary model upload hâlâ metadata/file-name temelli; gerçek büyük artifact upload akışı ayrıca tasarlanmalı.
- Runtime E2E çıktıları Git dışında tutuluyor; saha kullanımında retention/cleanup politikası gerekir.
- Annotation review bu fazda tablo tabanlı; gerçek canvas bbox editörü yok.

## Faz 10'a geçiş önerisi

Faz 10'a geçilebilir. Bir sonraki task öncesinde bu raporun ayrı docs commit'i olarak alınması önerilir.
