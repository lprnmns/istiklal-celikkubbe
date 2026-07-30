# Faz 11 - KTR Export, Demo Polish ve Operasyon Prosedürü Raporu

## Yapılanlar

- KTR/report export backend katmanı eklendi.
- `/api/reports/*` endpointleri eklendi.
- KTR Summary, Demo Pack ve Readiness Pack markdown export akışları eklendi.
- Interface inventory, safety summary, self-test summary, model registry summary, dataset summary, demo runbook ve operation checklist üretimi eklendi.
- Screenshot manifest üretimi eklendi.
- Report export eventleri JSONL log ve WebSocket akışına eklendi.
- `config/config.yaml` içine `reports` ayarları eklendi.
- Frontend Reports ekranı `/reports` rotasıyla eklendi.
- Sidebar menüsü Operations, Engineering, Data & Reports olarak gruplandı.
- Dashboard'a Reports/KTR kartı eklendi.
- Reports eventleri global event store ve Logs akışına dahil edildi.
- Faz 11 dokümantasyonu `docs/ktr_reports_phase11.md` olarak yazıldı.

## Oluşturulan/değiştirilen dosyalar

- `.gitignore`
- `backend/app/api/reports.py`
- `backend/app/api/routes_ws.py`
- `backend/app/main.py`
- `backend/app/schemas/config.py`
- `backend/app/schemas/report_export.py`
- `backend/app/services/ktr_export_service.py`
- `backend/app/services/report_export_service.py`
- `backend/app/services/runtime_state.py`
- `backend/tests/conftest.py`
- `backend/tests/test_reports_phase11.py`
- `config/config.yaml`
- `docs/ktr_reports_phase11.md`
- `frontend/src/api/reports.ts`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/router/index.ts`
- `frontend/src/stores/reportsStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/reports.ts`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/ReportsView.vue`

## Test/build sonuçları

- `uv run pytest -q`: 141 passed
- `pnpm typecheck`: başarılı
- `pnpm build`: başarılı
- Manuel smoke:
  - `/`: 200
  - `/reports`: 200
  - `/self-test`: 200
  - `/data-lab`: 200
  - `/logs`: 200
  - `/api/reports/status`: 200
  - `/api/reports/exports`: 200
  - `/api/self-test/status`: 200
  - `/api/models`: 200
  - `/api/sessions`: 200

## Git commit hashleri

- `9c3a234 feat: add KTR report export and demo runbook`

## Reports/KTR ekranı özeti

- KTR Summary, Demo Pack ve Readiness Pack üretme butonları eklendi.
- Latest self-test özeti ve export servis durumu gösteriliyor.
- Export listesi, dosya yolları ve summary JSON ön izlemesi gösteriliyor.
- Ekranda `REPORTS DO NOT ENABLE PHYSICAL COMMANDS` ve `NO PHYSICAL COMMAND` badge'leri var.

## Üretilen export dosyaları

Smoke sırasında örnek KTR export üretildi:

- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/ktr_summary.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/interface_inventory.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/safety_summary.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/self_test_summary.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/model_registry_summary.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/dataset_summary.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/demo_runbook.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/operation_checklist.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/screenshots_manifest.json`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260509-102427-53f0fa/export_metadata.json`

`exports/reports/**` Git ignore kapsamındadır; runtime export çıktıları commit'e alınmadı.

## Interface inventory özeti

Export içinde şu çekirdek arayüzler tablo olarak üretiliyor:

- Frontend <-> Backend REST
- Frontend <-> Backend WebSocket
- Backend <-> Pico Serial JSON-line
- Backend <-> Pico Binary protocol
- Camera <-> Backend
- Vision model <-> Inference adapter
- Motion service <-> Serial layer
- Dataset/replay <-> Vision pipeline
- Self-test <-> all services

## Safety/self-test/report entegrasyonu özeti

- Report export safety state değiştirmiyor.
- Report export fiziksel komut üretmiyor.
- Export metadata içinde `no_physical_command_generated=true` tutuluyor.
- Self-test run mevcutsa readiness özeti rapora dahil ediliyor.
- Safety summary `NO_FIRE`, `dry_run=true`, `hardware_enabled=false` ve fire request rejection modelini açık yazıyor.

## Bilinen eksikler

- KTR metinleri yarışma başvuru formatı kesinleşince saha diliyle tekrar gözden geçirilmeli.
- Report export şimdilik Markdown ve JSON metadata üretir; PDF/ZIP paketleme eklenmedi.
- Download endpointi yerine UI dosya yolunu gösteriyor.
- Screenshot manifest mevcut PNG dosyalarını listeler; otomatik screenshot alma bu fazda eklenmedi.

## Riskler

- KTR metinlerinin teknik doğruluğu koddan besleniyor, ancak resmi KTR şablonu değişirse manuel güncelleme gerekir.
- Runtime export klasörü büyüyebilir; `exports/reports/**` Git ignore kapsamında tutulmalı.
- Gerçek hardware fazına geçmeden önce raporlardaki placeholder pin/E-stop notları saha doğrulamasıyla güncellenmeli.

## Bir sonraki önerilen task

Faz 12'ye geçmeden önce kısa bir kabul/polish adımı önerilir: Reports ekranından demo pack ve readiness pack üretip jüri demosu için tek sayfalık sunum akışını ve gerekli ekran görüntülerini doğrulamak.
