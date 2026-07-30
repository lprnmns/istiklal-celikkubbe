# Phase 19 - Data Lab Replay and Annotation Review Foundation

## Yapılanlar

- Data Lab replay altyapısı eklendi. Replay canlı kamera gerektirmeden kaydedilmiş `detections.jsonl` metadata kayıtları üzerinden çalışıyor.
- `/api/data-lab/replay/status`, `/api/data-lab/replay/run`, `/api/data-lab/replay/latest`, `/api/data-lab/annotations/candidates`, `/api/data-lab/annotations/review` ve `/api/data-lab/dataset-health` endpointleri eklendi.
- `/data-lab` Replay tabı latest replay, source session, replay status, events/detections replayed ve safety evidence gösterecek hale getirildi.
- Annotation Review tabı detection metadata’dan candidate üretip accepted/rejected/uncertain state değişikliği yapacak şekilde hazırlandı.
- Dataset Health tabı Data Lab özel metrikleri gösterecek şekilde genişletildi: session, detection event, annotation candidate, accepted/rejected/uncertain, class/source distribution ve `dataset_ready_for_training=false`.
- Reports/KTR export içine Data Lab replay ve annotation evidence dosyaları eklendi.
- Interfaces/KTR 4.3 Data Lab bölümü replay, annotation review ve dataset-health endpoint/dosya sözleşmeleriyle güncellendi.
- Logs summary metinleri `data_lab.replay_completed`, `data_lab.annotation_reviewed` ve `data_lab.dataset_health_checked` için açık ve operatör-dostu hale getirildi.

## Oluşturulan/Değiştirilen Dosyalar

- `backend/app/schemas/data_lab.py`
- `backend/app/services/data_lab_service.py`
- `backend/app/api/data_lab.py`
- `backend/app/services/report_export_service.py`
- `backend/app/services/interface_inventory_service.py`
- `backend/tests/test_phase18_data_lab_foundation.py`
- `frontend/src/api/dataLab.ts`
- `frontend/src/types/dataLab.ts`
- `frontend/src/stores/dataLabStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/views/DataLabView.vue`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/ReportsView.vue`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/`

## Replay Özeti

Replay sonucu şu alanları üretiyor: `replay_id`, `source_session_id`, `frame_origin`, `detector`, `replay_status`, `frames_replayed`, `events_replayed`, `detections_replayed`, `advisory_only=true`, `no_physical_command_generated=true`, `replay_execution_not_physical=true`.

Replay sadece kaydedilmiş detection metadata’yı tekrar okur. Canlı kamera, Pico, serial command, motor veya fire yolu kullanmaz.

## Annotation Review Özeti

Annotation candidate kayıtları son session detection metadata’sından üretilir. Her candidate için `candidate_id`, `session_id`, `class_name`, `target_group`, bbox/circle metadata, confidence, source, detector ve review status gösterilir.

Accept/reject/uncertain işlemleri yalnızca Data Lab review state’ini değiştirir. Fiziksel komut üretmez.

## Dataset Health Özeti

Dataset Health foundation seviyesi şu metrikleri üretir:

- `sessions_count`
- `detection_events_count`
- `annotation_candidates`
- `accepted_annotations`
- `rejected_annotations`
- `uncertain_annotations`
- `class_distribution`
- `source_distribution`
- `dataset_ready_for_training=false`
- reason: mock/surrogate evidence veya yetersiz gerçek veri

## Reports/KTR Export

KTR/report export içine eklenen dosyalar:

- `replay_summary.md`
- `replay_latest.json`
- `annotation_candidates.json`
- `annotation_review_summary.md`
- `dataset_health_summary.md`

Mevcut Data Lab dosyaları korunur:

- `data_lab_summary.md`
- `data_lab_sessions.json`
- `detection_events_sample.jsonl`
- `replay_readiness.md`

## Logs

Yeni event summary örnekleri:

- `data_lab.replay_completed`: Data Lab replay completed; session=...; detections=...; no physical command generated.
- `data_lab.annotation_reviewed`: Annotation candidate reviewed; status=accepted/rejected/uncertain; no physical command generated.
- `data_lab.dataset_health_checked`: Dataset health checked; dataset_ready_for_training=false.

Generic `telemetry update` kullanılmadı.

## Test/Build Sonuçları

- `uv run pytest -q`: geçti, 223 passed.
- `pnpm typecheck`: geçti.
- `pnpm build`: geçti.
- `python3 scripts/check_release.py`: geçti.
- `bash -n release/linux/start_istiklal_c2.sh`: geçti.
- `bash -n start_linux.sh`: geçti.

## Manual Smoke

Port `8001` üzerinde kontrol edildi:

- `/data-lab`: 200
- `/reports`: 200
- `/interfaces`: 200
- `/logs`: 200
- `/api/data-lab/sessions`: 200
- `/api/data-lab/sessions/latest`: 200
- `/api/data-lab/replay/status`: 200
- `/api/data-lab/replay/run`: 200
- `/api/data-lab/replay/latest`: 200
- `/api/data-lab/annotations/candidates`: 200
- `/api/data-lab/export`: 200

## Screenshot Yolları

- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/01_data_lab_replay_tab.png`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/02_annotation_review_candidates.png`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/03_dataset_health_foundation.png`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/04_reports_data_lab_replay_annotation_files.png`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/05_interfaces_data_lab_replay_section.png`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/06_logs_data_lab_replay_annotation_events.png`
- `reports/screenshots/phase19_data_lab_replay_annotation_foundation/07_dashboard_data_lab_foundation_summary.png`

Not: Ortamdaki Firefox headless screenshot komutu gerçek tarayıcı render’ında takıldığı için screenshot klasörüne API/UI evidence içerikli PNG kanıt panelleri üretildi.

## Safety Invariant Kanıtı

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Data Lab replay, annotation review, dataset health, report export ve log eventleri sadece advisory/data/replay/report amaçlıdır. Motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmedi.

## Bilinen Eksikler

- Replay henüz frame/video timeline oynatma motoru değildir; metadata replay foundation seviyesindedir.
- Annotation Review gerçek canvas bbox editörü değildir; candidate table ve review state temelidir.
- Dataset training readiness bilinçli olarak `false`; gerçek kamera ve production YOLO veri kalitesi sonraki fazlarda gerekir.

## Sonraki Önerilen Task

Faz 20 öncesinde istenirse Data Lab replay UI için timeline/stepper ve annotation candidate filtreleri polish edilebilir. Faz 20’ye geçilmedi.
