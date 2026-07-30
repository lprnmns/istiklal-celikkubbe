# Ara Task 18.1 - Data Lab Evidence Export ve Log Polish

## Yapılanlar

- Data Lab export response alanları genişletildi: `export_id`, `created_at`, `output_dir`, `sessions_count`, `detection_events_count`, `no_physical_command_generated`.
- `/data-lab` Evidence Export kartı export sonrası latest export bilgilerini net göstermeye başladı.
- `/data-lab` ekranına son 5 Data Lab session için görünür evidence tablosu eklendi.
- Data Lab WebSocket/log event payload summary alanları anlamlı hale getirildi.
- Logs UI summary helper’ı `data_lab.session_recorded` ve `data_lab.export_completed` eventlerini generic telemetry yerine açık metinle gösterir hale getirildi.
- Reports export detail içinde Data Lab dosyaları ayrı metric olarak görünür hale getirildi.
- Replay readiness metni `replay_foundation_ready` / `replay_execution_not_implemented` semantiğine çekildi.
- Data Lab eventleri WebSocket mesaj akışına eklendi.

## Değiştirilen Dosyalar

- `backend/app/api/routes_ws.py`
- `backend/app/schemas/data_lab.py`
- `backend/app/services/data_lab_service.py`
- `backend/tests/test_phase18_data_lab_foundation.py`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/dataLab.ts`
- `frontend/src/views/DataLabView.vue`
- `frontend/src/views/ReportsView.vue`

## Test/Build Sonuçları

- `uv run pytest -q`: 222 passed
- `pnpm typecheck`: passed
- `pnpm build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed

## Manual Smoke

- `/data-lab`: HTTP 200
- `/logs?search=data_lab`: HTTP 200
- `/reports`: HTTP 200
- `/interfaces`: HTTP 200
- `/api/data-lab/sessions`: HTTP 200
- `/api/data-lab/sessions/latest`: HTTP 200
- `/api/data-lab/export`: HTTP 200

## Düzeltilen Görünürlük Problemleri

- Evidence Export kartında `not_exported` export sonrası kalmıyor; output path, session count, detection JSONL event count ve timestamp görünüyor.
- Session listesi sadece genel Phase 9 session tablosuna bağlı kalmadan son Data Lab evidence kayıtlarını gösteriyor.
- Logs ekranında Data Lab eventleri `data_lab` search/filter ile bulunabilir hale geldi.
- Reports detail içinde KTR export dosyaları arasında Data Lab evidence dosyaları ayrı satırlarda okunabiliyor.

## Log Summary Semantiği

- `data_lab.session_recorded`: `Data Lab session recorded; source=<source>; no physical command generated.`
- `data_lab.export_completed`: `Data Lab evidence export completed; sessions=<n>; detection_events=<n>; no physical command generated.`

## Replay Readiness Semantiği

Replay hazır olma metni “tam replay execution hazır” izlenimi vermeyecek şekilde ayrıldı:

- `replay_foundation_ready`: session metadata ve detection JSONL evidence UI/review için hazır.
- `replay_execution_not_implemented`: session evidence yok veya execution katmanı ayrı iş.

## Screenshot Yolları

- `reports/screenshots/phase18_1_data_lab_evidence_polish/01_data_lab_export_latest_info.png`
- `reports/screenshots/phase18_1_data_lab_evidence_polish/02_data_lab_recent_sessions_table.png`
- `reports/screenshots/phase18_1_data_lab_evidence_polish/03_data_lab_export_response_detail.png`
- `reports/screenshots/phase18_1_data_lab_evidence_polish/04_reports_data_lab_files_visible.png`
- `reports/screenshots/phase18_1_data_lab_evidence_polish/05_interfaces_replay_readiness_wording.png`
- `reports/screenshots/phase18_1_data_lab_evidence_polish/06_logs_data_lab_event_summaries.png`
- `reports/screenshots/phase18_1_data_lab_evidence_polish/07_ktr_data_lab_replay_preview.png`

## Safety Invariant

Korundu:

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- Data Lab çıktıları `advisory_only=true` ve `no_physical_command_generated=true`

## Commit Hashleri

- Bu raporu içeren commit hash’i final yanıtta belirtilmiştir.

## Bilinen Eksikler

- Replay execution hâlâ foundation seviyesinde; bu task replay oynatma motoru geliştirmedi.
- Data Lab evidence gerçek production YOLO yerine mock/surrogate metadata ile doğrulandı.

## Sonraki Önerilen Task

Faz 19’a geçmeden önce istenirse Data Lab acceptance smoke yapılabilir: export oluştur, Logs’ta `data_lab` filtrele, Reports detail’de Data Lab dosyalarını kontrol et.
