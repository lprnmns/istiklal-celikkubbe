# Phase 22 - Portable Release ZIP / Launcher / Runbook

## Ne Eklendi?

- Ara Task 21.1 kapsaminda Jury Demo Center icindeki Known Limitations satir duzeni duzeltildi.
- Uzun Turkce aciklama metinleri ile sagdaki `competition blocker` / `demo limitation` etiketleri artik cakismayacak sekilde wrap ve spacing guard ile render ediliyor.
- Portable release package workflow eklendi:
  - `GET /api/release/package/latest`
  - `POST /api/release/package/build`
- Release package uretimi `exports/release/istiklal_c2_release_<timestamp>/` altinda klasor ve ZIP uretiyor.
- Reports/KTR export icine release package dosyalari eklendi:
  - `release_package_summary.md`
  - `release_package_manifest.json`
  - `release_zip_check.md`
- Demo ve Reports ekranlarina Portable Release Package kartlari eklendi.
- Release package log eventleri eklendi:
  - `release.package_generated`
  - `release.zip_generated`
  - `release.package_validated`
- Topbar/release manifest/release check phase etiketi Phase 22 olarak guncellendi.

## ZIP Icindekiler

Uretilen paket:

- Package id: `istiklal_c2_release_20260511_231652`
- Output dir: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260511_231652`
- ZIP: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260511_231652.zip`
- Files count: `58`
- Manifest: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260511_231652/package_manifest.json`
- Checksums: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260511_231652/checksums.json`
- Checksum status: `passed`

Paket icinde temel olarak sunlar var:

- `frontend_dist/`
- `release/linux/start_istiklal_c2.sh`
- `release/windows/start_istiklal_c2.bat`
- `start_linux.sh`
- `start_windows.bat`
- `demo_evidence_package/`
- `README_RELEASE.md`
- `RUNBOOK_DEMO.md`
- `.env.example`
- `config.example.yaml`
- `package_manifest.json`
- `checksums.json`

## Bilerek Yok

ZIP paketi demo/evidence paketidir; competition-ready iddiasi tasimaz.

Bilerek eklenmeyenler:

- Gercek hardware enable yolu
- Fiziksel seri komut yolu
- Motor/servo/tetik/fire kontrolu
- GPIO, PWM, STEP/DIR output
- Production YOLO modeli
- Pico telemetry verified kaniti
- Gercek laptop/USB kamera capture kaniti
- Training-ready dataset iddiasi

ZIP static inspection sonucunda `.git`, `node_modules`, `.venv`, `__pycache__` gibi runtime/developer klasorleri pakete alinmadi.

## Release Demo Ready / Competition Ready Ayrimi

- `release_demo_ready=true`
- `competition_ready=false`
- `dataset_ready_for_training=false`
- `no_physical_command_generated=true`

Portable release paketi demo, rapor, runbook, evidence ve guvenli dry-run sunumu icindir. Production YOLO modeli, gercek kamera kaniti, Pico telemetry verification ve self-test current pass olmadan competition readiness gecmez.

## Known Limitations Layout Hotfix

Known Limitations satirlari overlap-safe hale getirildi:

- Sol aciklama `minmax(0, 1fr)` alaninda wrap oluyor.
- Sag kategori etiketi `max-content` alanda sabit kaliyor.
- Uzun label ve uzun value icin guard test eklendi.
- Screenshot kaniti: `reports/screenshots/phase22_portable_release_package/01_known_limitations_layout_fixed.png`

## Test Sonuclari

- `uv run pytest -q`: `240 passed in 43.03s`
- `frontend/ pnpm typecheck`: passed
- `frontend/ pnpm build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed

Manual smoke sonuc dosyasi:

- `reports/phase22_smoke_results.json`

Manual smoke endpointleri HTTP 200 dondu:

- `/api/demo/readiness`
- `/api/demo/run`
- `/api/demo/latest`
- `/api/release/package/latest`
- `/api/release/package/build`
- `/api/release/status`

## Screenshot Klasoru

`reports/screenshots/phase22_portable_release_package/`

Dosyalar:

- `01_known_limitations_layout_fixed.png`
- `02_portable_release_package_overview.png`
- `03_release_package_manifest_zip_summary.png`
- `04_reports_latest_release_package.png`
- `05_logs_release_package_events.png`
- `06_ktr_portable_release_section.png`
- `07_safety_invariant_preserved.png`

## Degistirilen Ana Dosyalar

- `backend/app/api/release.py`
- `backend/app/schemas/release.py`
- `backend/app/services/release_service.py`
- `backend/app/services/report_export_service.py`
- `backend/tests/test_phase22_portable_release_package.py`
- `frontend/src/api/release.ts`
- `frontend/src/stores/releaseStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/release.ts`
- `frontend/src/views/DemoView.vue`
- `frontend/src/views/ReportsView.vue`
- `frontend/src/components/layout/AppShell.vue`
- `scripts/check_release.py`

## Safety Invariant

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Tum yeni release package metadata, log ve report ciktilarinda canonical kanit korunur:

`no_physical_command_generated=true`

## Bilinen Eksikler

- Windows launcher bu Linux host uzerinde static inspection ile dogrulandi; gercek Windows host uzerinde ayrica denenmeli.
- Portable package competition-ready degildir; production YOLO, gercek kamera kaniti, Pico telemetry ve self-test current pass eksiktir.
- ZIP paketinin dependency wheelhouse/offline binary kurulumu bu fazda eklenmedi; mevcut launcher dependency eksigini kullaniciya raporlar.

## Commit Hash

`b82c434 feat: add portable release package workflow`

