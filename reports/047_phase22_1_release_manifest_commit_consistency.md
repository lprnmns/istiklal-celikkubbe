# Ara Task 22.1 - Release Package Manifest Commit/Hash Consistency Hotfix

## Sorun

Faz 22 sonrasi uretilen release evidence ekraninda `Commit hash` alani eski Phase 21 commit'i olan `045ebb3` gibi algilanabilecek stale commit semantigi tasiyordu. Portable release package hangi workflow ve hangi checkout uzerinden uretildiyse bunu ayri ve net gostermeliydi.

## Neden Riskliydi?

Juri/demo kanit paketinde eski Phase 21 commit'inin gorunmesi, Phase 22 portable release workflow'unun pakete dahil edilmedigi veya yanlis committen paket uretildigi izlenimi verebilirdi. Bu nedenle tek `commit_hash` alani yerine rol bazli commit alanlari kullanildi.

## Duzeltilen Alanlar

`package_manifest.json`, release package API response, Reports/KTR export ve UI evidence kartlari su alanlari ayri tasiyor:

- `source_commit`: `b82c434`
- `package_generated_commit`: `a352398`
- `package_workflow_commit`: `b82c434`
- `report_commit`: `5c751c1`
- `commit_hash`: `a352398`

Ek olarak `commit_semantics` nesnesi manifest icinde her alanin anlamini acikliyor.

## Yeni Package / ZIP

- Package id: `istiklal_c2_release_20260512_135431`
- Package path: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260512_135431`
- ZIP path: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260512_135431.zip`
- Manifest path: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260512_135431/package_manifest.json`
- Checksums path: `/home/alperen/teknofest/exports/release/istiklal_c2_release_20260512_135431/checksums.json`
- Checksum status: `passed`
- `no_physical_command_generated=true`

Eski ZIP kalabilir; latest package artik yukaridaki yeni pakettir.

## Test Sonuclari

- `uv run pytest -q`: `240 passed in 43.53s`
- `frontend/ pnpm typecheck`: passed
- `frontend/ pnpm build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed

Manual smoke:

- `/demo`: HTTP 200
- `/dashboard`: HTTP 200
- `/reports`: HTTP 200
- `/logs`: HTTP 200
- `/api/release/package/latest`: HTTP 200
- `/api/release/package/build`: HTTP 200

Manual smoke kanit dosyalari:

- `reports/phase22_1_smoke_results.json`
- `reports/phase22_1_manual_smoke_routes.json`

## Screenshot Klasoru

`reports/screenshots/phase22_1_release_manifest_commit_consistency/`

Dosyalar:

- `01_release_manifest_zip_summary_commit_fixed.png`
- `02_portable_release_package_overview_latest.png`
- `03_reports_latest_release_package_commit_fixed.png`
- `04_ktr_portable_release_section_commit_fixed.png`
- `05_safety_invariant_preserved.png`

## Guard Testleri

Eklenen/guncellenen testler:

- Manifest commit alanlari stale `045ebb3` degerini tasimaz.
- Commit alanlari bos veya `unknown` degildir.
- `source_commit` ve `package_workflow_commit` Phase 22 workflow commit'i `b82c434` olarak kalir.
- `package_generated_commit` paket uretim anindaki checkout commit'i `a352398` olarak yazilir.
- `release_zip_check.md` checksum status bilgisini `passed` olarak verir.
- ZIP icinde `.git`, `node_modules`, `.venv`, `__pycache__`, secret/token benzeri yollar yoktur.
- `no_physical_command_generated=true` korunur.

## Safety Invariant

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Bu hotfix yalnizca release package manifest commit/hash semantigini, KTR/report evidence alanlarini ve kanit screenshotlarini duzeltir. Hardware/fire/motor/servo/GPIO/PWM/STEP/DIR/physical command path eklenmedi.

## Commit Hash

- Code commit: `a352398 fix: align release package manifest commit metadata`
- Report/evidence commit: `7b0e1d1 docs: add phase 22.1 release manifest consistency report`

