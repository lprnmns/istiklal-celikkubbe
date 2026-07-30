# Faz 18 - Data Lab Foundation ve Session Evidence Altyapısı

## Yapılanlar

- `/api/data-lab` altında Data Lab status, session list, latest session, latest detection sample ve evidence export endpointleri eklendi.
- `DataLabService` ile Vision mock/surrogate detection çıktıları session-level metadata olarak `detections.jsonl` içine kaydedilir hale getirildi.
- `/data-lab` ekranı Data Lab Foundation, latest detection evidence ve evidence export panelleriyle gerçek session evidence modülüne çevrildi.
- Reports/KTR export paketine `data_lab_summary.md`, `data_lab_sessions.json`, `detection_events_sample.jsonl` ve `replay_readiness.md` eklendi.
- Interfaces/KTR 4.3 metnine “Veri Seti, Oturum Kaydı ve Replay Arayüzü” bölümü eklendi.
- Data Lab log eventleri `data_lab.session_recorded` ve `data_lab.export_completed` için human-readable summary üretildi.
- `exports/data_lab/**` runtime export çıktısı olarak `.gitignore` kapsamına alındı.
- Topbar/release manifest phase etiketi Phase 18 olarak güncellendi.

## Oluşturulan/Değiştirilen Dosyalar

- `backend/app/services/data_lab_service.py`
- `backend/app/schemas/data_lab.py`
- `backend/app/api/data_lab.py`
- `backend/app/main.py`
- `backend/app/services/runtime_state.py`
- `backend/app/services/report_export_service.py`
- `backend/app/services/interface_inventory_service.py`
- `frontend/src/views/DataLabView.vue`
- `frontend/src/api/dataLab.ts`
- `frontend/src/stores/dataLabStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/dataLab.ts`
- `scripts/capture_phase18_screenshots.py`
- `backend/tests/test_phase18_data_lab_foundation.py`
- `.gitignore`

## Test/Build Sonuçları

- `uv run pytest -q`: 221 passed
- `pnpm typecheck`: passed
- `pnpm build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed
- Manual smoke: `/data-lab`, `/vision`, `/reports`, `/interfaces`, `/logs`, `/api/data-lab/status`, `/api/data-lab/sessions`, `/api/data-lab/sessions/latest`, `/api/data-lab/detection-events-sample`, `/api/reports`, `/api/interfaces/ktr-section`: HTTP 200

## Data Lab Özeti

Data Lab artık mock/surrogate vision eventlerinden oturum seviyesinde kanıt üretebiliyor. `record-latest` endpointi mevcut Vision pipeline’dan latest event alır, aktif session yoksa güvenli bir `data_lab_evidence` session oluşturur ve detection metadata’yı `detections.jsonl` içine yazar.

## Session Evidence Özeti

Session evidence çıktıları `source`, `camera_source_kind`, `frame_origin`, `detector_kind`, body/circle count, latency/FPS ve detection listesi içerir. Tüm kayıtlarda `advisory_only=true` ve `no_physical_command_generated=true` tutulur.

## Reports/KTR Entegrasyonu

KTR export artık Data Lab kanıt dosyalarını üretir:

- `data_lab_summary.md`
- `data_lab_sessions.json`
- `detection_events_sample.jsonl`
- `replay_readiness.md`

Interface Inventory KTR 4.3 metninde Data Lab’in dataset/session/replay arayüzü olduğu ve fiziksel komut üretmediği açıkça yazıldı.

## Screenshot Yolları

- `reports/screenshots/phase18_data_lab_foundation/01_data_lab_foundation_status.png`
- `reports/screenshots/phase18_data_lab_foundation/02_data_lab_session_evidence.png`
- `reports/screenshots/phase18_data_lab_foundation/03_data_lab_export_detail.png`
- `reports/screenshots/phase18_data_lab_foundation/04_reports_data_lab_export_files.png`
- `reports/screenshots/phase18_data_lab_foundation/05_interfaces_data_lab_ktr_section.png`
- `reports/screenshots/phase18_data_lab_foundation/06_logs_data_lab_events.png`
- `reports/screenshots/phase18_data_lab_foundation/07_ktr_data_lab_preview.png`

## Safety Invariant Kanıtı

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- Data Lab record/export responses include `no_physical_command_generated=true`
- Reports/KTR Data Lab files include `advisory_only=true` and `no_physical_command_generated=true`

## Commit Hashleri

- Bu raporu içeren Faz 18 commit hash’i final yanıtta belirtilmiştir.

## Bilinen Eksikler

- Bu faz Data Lab foundation’dır; gelişmiş replay timeline ve full annotation editor eklenmedi.
- Detection event sample şimdilik mock/surrogate Vision metadata üzerinden üretilir.
- Gerçek production YOLO çıktısı geldiğinde aynı Data Lab session evidence yapısına bağlanması gerekir.

## Sonraki Önerilen Task

Faz 19’a geçmeden önce Data Lab export çıktıları üzerinde küçük bir acceptance smoke yapılabilir: yeni session kaydı, KTR export dosya kontrolü ve Logs filtresiyle Data Lab event kanıtı doğrulaması.
