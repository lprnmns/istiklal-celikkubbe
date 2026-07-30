# Ara Task 16.4 - Cold-start Release Evidence and Operator Acceptance Polish

## Yapılanlar

- `/api/release/cold-start-check` endpointi eklendi.
- Cold-start check çıktısına platform, Python sürümü, uv varlığı, frontend static build, yazılabilir log/export klasörleri, config, model klasörü, aktif model türü, kamera kaynağı, Pico absent/verified ayrımı, launcher dosyaları ve safety invariant kanıtı eklendi.
- `release.cold_start_checked` WebSocket/log event'i eklendi.
- Event summary şu şekilde netleştirildi:
  `Cold-start release check completed; no physical command path enabled.`
- First Run ekranına Cold-start Evidence paneli eklendi.
- Dashboard release candidate ile competition rehearsal ayrımını cold-start evidence alanlarıyla güçlendirdi.
- KTR/report export içine şu dosyalar eklendi:
  - `cold_start_summary.json`
  - `cold_start_summary.md`
  - `launcher_inspection.md`
- `scripts/check_release.py` cold-start endpointini ve launcher static inspection kontrolünü çalıştıracak şekilde genişletildi.
- First Run reset/mark-complete backend state davranışı test edildi.
- Logs UI event summary resolver artık payload içindeki explicit `summary` alanını kullanıyor; `release.cold_start_checked` generic telemetry update olarak görünmüyor.

## Release / First Run Tutarlılığı

- Reset sonrası backend state `completed=false` dönüyor; UI ortak `firstRunStore.displayBadge` üzerinden `FIRST RUN: OPEN` gösteriyor.
- Mark complete sonrası backend state `completed=true` dönüyor; topbar, First Run ve Dashboard aynı store/state kaynağı üzerinden `FIRST RUN: PASSED` gösteriyor.
- Release candidate passed durumu competition rehearsal ready anlamına gelmiyor; UI metinlerinde bu ayrım açık hale getirildi.

## Cold-start Endpoint Sonucu

Manual smoke:

- `/api/release/cold-start-check` -> HTTP 200
- `status=passed`
- `safety_invariant_ok=true`
- `no_physical_command_generated=true`
- Aktif model türü: `fixture`
- Kamera kaynağı: `mock`
- Pico state: `absent`

## Report Export Kanıtı

Üretilen KTR export içinde cold-start ve launcher inspection dosyaları:

- `/home/alperen/teknofest/exports/reports/ktr_summary-20260510-183153-a3119e/cold_start_summary.md`
- `/home/alperen/teknofest/exports/reports/ktr_summary-20260510-183153-a3119e/launcher_inspection.md`

`launcher_inspection.md`, launcher scriptlerinin yazılımı başlatmak dışında motor/fire/GPIO endpoint çağrısı yapmadığını metinsel olarak raporlar.

## Test / Build Sonuçları

- `uv run pytest backend/tests/test_phase15_release_candidate.py backend/tests/test_phase13_portable_interfaces.py backend/tests/test_phase14_field_release_qa.py -q` -> geçti, `22 passed`
- `uv run pytest -q` -> geçti, `206 passed`
- `(cd frontend && pnpm typecheck)` -> geçti
- `(cd frontend && pnpm build)` -> geçti
- `python3 scripts/check_release.py` -> geçti
- `bash -n release/linux/start_istiklal_c2.sh` -> geçti
- `bash -n start_linux.sh` -> geçti

## Manual Smoke

Yerel backend `http://127.0.0.1:8016` üzerinde çalıştırıldı:

- `/` -> HTTP 200
- `/first-run` -> HTTP 200
- `/dashboard` -> HTTP 200
- `/reports` -> HTTP 200
- `/interfaces` -> HTTP 200
- `/logs` -> HTTP 200
- `/api/release/status` -> HTTP 200
- `/api/release/check` -> HTTP 200
- `/api/release/cold-start-check` -> HTTP 200

## Screenshot Yolları

- `reports/screenshots/phase16_4_cold_start_evidence/01_first_run_cold_start_evidence.png`
- `reports/screenshots/phase16_4_cold_start_evidence/02_dashboard_release_vs_competition.png`
- `reports/screenshots/phase16_4_cold_start_evidence/03_reports_cold_start_summary_detail.png`
- `reports/screenshots/phase16_4_cold_start_evidence/04_logs_release_cold_start_checked.png`
- `reports/screenshots/phase16_4_cold_start_evidence/05_interfaces_ktr_cold_start_preview.png`

## Commit Hashleri

- Başlangıç commit'i: `3306995 fix: clarify model activation log semantics`
- Faz 16.4 commit'i: commit sonrası final yanıtta verilecek

## Safety Invariant

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Bu taskta fiziksel komut, GPIO, motor, servo, tetik, STEP/DIR/PWM veya fire yolu eklenmedi.

## Bilinen Eksikler

- Windows launcher gerçek Windows host üzerinde ayrıca denenmelidir; bu taskta Linux ortamında static inspection yapıldı.
- Pico gerçek cihaz bağlı olmadığı için cold-start evidence `pico_state=absent` gösteriyor; release candidate için bu kabul edilebilir, competition rehearsal için bloklayıcıdır.
- Production YOLO modeli hâlâ görüntü işleme ekibinden bekleniyor; aktif fixture/test adapter yarışma modeli değildir.

## Faz 17 Durumu

Faz 17'ye geçilmedi.
