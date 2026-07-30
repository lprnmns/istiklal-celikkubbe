# Faz 13 - Portable Release, First Run Wizard ve Interface Inventory Hardening

## Yapılanlar

- Windows/Linux portable launcher yapısı eklendi.
- Backend production modda `frontend/dist` static serve ve SPA fallback destekleyecek hale getirildi.
- Runtime mode config alanları eklendi.
- First Run Wizard backend API ve frontend ekranı eklendi.
- Interface Inventory backend servisi, API endpointleri ve `/interfaces` frontend ekranı eklendi.
- Reports/KTR export içine KTR 4.3 arayüz metni ve geniş interface inventory entegre edildi.
- Logs ekranında gerçek JSONL client event export eklendi.
- Self-Test ekranına filtreler, kategori gruplama ve first-run acceptance aksiyonu eklendi.
- Devices, Vision, Dashboard ve Topbar üzerinde Phase 13 polish yapıldı.
- Portable ve KTR interface dokümantasyonu eklendi.

## Portable Launcher Özeti

- Root launcherlar: `start_linux.sh`, `start_windows.bat`
- Release launcherlar:
  - `release/linux/start_istiklal_c2.sh`
  - `release/windows/start_istiklal_c2.bat`
- Launcher davranışı:
  - Python 3.12+ kontrolü
  - `uv` kontrolü
  - port 8000 kontrolü
  - backend dependency sync
  - `frontend/dist` yoksa pnpm ile frontend build denemesi
  - backend’i `127.0.0.1:8000` üzerinde başlatma
  - launcher loglarını `logs/launcher/` altına yazma

## First Run Wizard Özeti

- Endpointler:
  - `GET /api/first-run/status`
  - `POST /api/first-run/check`
  - `POST /api/first-run/mark-complete`
  - `POST /api/first-run/reset`
  - `GET /api/first-run/report`
- UI route: `/first-run`
- Kontroller backend, frontend static, config, writable logs/exports, device manager, camera source, Pico safe absence, model registry, self-test, interface inventory, launcher files ve no physical command invariant alanlarını kapsar.

## Interface Inventory Özeti

- Endpointler:
  - `GET /api/interfaces/inventory`
  - `GET /api/interfaces/ktr-section`
  - `POST /api/interfaces/export`
- UI route: `/interfaces`
- Envanter; UI, REST, WebSocket, MJPEG, camera, vision model adapter, Pico telemetry, serial protocol, safety, config, logging, dataset/replay, reports, deployment ve elektronik/sinyal placeholder arayüzlerini içerir.

## KTR 4.3 Export Özeti

- KTR export paketine `ktr_4_3_interfaces.md` eklendi.
- `interface_inventory.md` yeni servis üzerinden ayrıntılı matrix olarak üretiliyor.
- KTR metni kullanıcı arayüzü, yazılım arayüzleri, donanım arayüzleri, görüntü/veri aktarımı, mesaj protokolleri, güvenlik arayüzleri, kullanılan teknolojiler ve arıza/güvenli durum davranışlarını kapsıyor.

## UI Polish Özeti

- Sidebar’a `First Run` ve `Interfaces` eklendi.
- Topbar build bilgisi Phase 13 olarak güncellendi.
- Dashboard’a portable mode, first-run, interface inventory, selected camera, active adapter, Pico candidate/verified ve KTR readiness alanları eklendi.
- Devices ekranında düşük relevance serial portlar varsayılan collapse edildi.
- Vision runtime inputları açık label’larla düzenlendi.
- Logs ekranında human-readable detail summary ve gerçek JSONL export eklendi.
- Self-Test ekranında Critical/Warning/Passed filtreleri ve category accordion eklendi.

## Test/Build Sonuçları

- `uv run pytest tests/test_phase13_portable_interfaces.py -q`: 7 passed
- `uv run pytest -q`: 179 passed
- `pnpm typecheck`: passed
- `pnpm build`: passed
- `bash -n start_linux.sh && bash -n release/linux/start_istiklal_c2.sh`: passed
- Manual smoke:
  - `/`: 200
  - `/first-run`: 200
  - `/interfaces`: 200
  - `/devices`: 200
  - `/vision`: 200
  - `/self-test`: 200
  - `/reports`: 200
  - `/logs`: 200
  - `/api/first-run/status`: 200
  - `/api/interfaces/inventory`: 200
  - `/api/interfaces/ktr-section`: 200
  - `/api/reports/status`: 200

## Screenshot Yolları

- `reports/screenshots/phase13_portable_interfaces/01_first_run_wizard.png`
- `reports/screenshots/phase13_portable_interfaces/02_interfaces_inventory.png`
- `reports/screenshots/phase13_portable_interfaces/03_ktr_interface_preview.png`
- `reports/screenshots/phase13_portable_interfaces/04_devices_filtered_view.png`
- `reports/screenshots/phase13_portable_interfaces/05_vision_settings_labeled.png`
- `reports/screenshots/phase13_portable_interfaces/06_self_test_filtered.png`
- `reports/screenshots/phase13_portable_interfaces/07_dashboard_release_readiness.png`
- `reports/screenshots/phase13_portable_interfaces/08_logs_jsonl_export.png`

## Commit Hashleri

- `1b2c037` - `feat: add portable release and interface inventory hardening`

## Bilinen Eksikler

- Windows launcher bu ortamda çalıştırılamadı; batch dosyası statik olarak eklendi.
- Portable ZIP paketleme scripti ayrı bir release-pack adımı olarak eklenmedi.
- First Run Wizard, gerçek Pico bağlı olmadığı için Pico verified durumunu yalnızca güvenli absence/read-only state olarak raporlar.
- Gerçek YOLO model yükleme acceptance testi vision team model dosyası gelince yapılmalı.

## Sonraki Önerilen Task

- Faz 14’e geçmeden önce bir paketleme kabul testi yapılması önerilir:
  - Temiz klasöre ZIP açma
  - `start_linux.sh` ile offline başlatma
  - `/first-run` acceptance
  - `/interfaces` KTR export doğrulama
  - `Reports` demo pack export doğrulama

Safety invariant korunmuştur: `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`.
