# Ara Task 20.4 - Evidence Endpoint Spacing Polish

## Amaç

Manual smoke ve report/KTR evidence screenshotlarında uzun label-value satırlarının üst üste binmesini engellemek.

## Yapılanlar

- `scripts/capture_phase20_4_screenshots.py` eklendi.
- Manual smoke endpointleri artık tek birleşik satır olarak render edilmiyor.
- Şu endpointler ayrı satır/value çifti olarak çiziliyor:
  - `/api/demo/readiness` -> `HTTP 200`
  - `/api/demo/run` -> `HTTP 200`
  - `/api/demo/latest` -> `HTTP 200`
- Uzun label değerleri için evidence renderer kuralı eklendi:
  - label genişliği aşarsa value alt satıra iner.
  - value kendi satırında wrap olur.
  - label/value aynı satırda çakışmaz.
- Reports/KTR evidence paneli aynı spacing kuralını kullanacak şekilde üretildi.
- Snapshot-level guard testleri eklendi.

## Değiştirilen/Oluşturulan Dosyalar

- `scripts/capture_phase20_4_screenshots.py`
- `backend/tests/test_phase20_4_evidence_spacing.py`
- `reports/screenshots/phase20_4_evidence_spacing_polish/01_manual_smoke_spacing_fixed.png`
- `reports/screenshots/phase20_4_evidence_spacing_polish/02_reports_ktr_spacing_clean.png`

## Test/build Sonuçları

- `uv run pytest backend/tests/test_phase20_4_evidence_spacing.py -q`: PASSED, 2 passed
- `uv run pytest -q`: PASSED, 231 passed
- `pnpm typecheck`: PASSED
- `pnpm build`: PASSED
- `python3 scripts/check_release.py`: PASSED
- `bash -n release/linux/start_istiklal_c2.sh`: PASSED
- `bash -n start_linux.sh`: PASSED

## Manual Smoke

- `/logs`: HTTP 200
- `/demo`: HTTP 200
- `/dashboard`: HTTP 200
- `/reports`: HTTP 200
- `/api/demo/readiness`: HTTP 200
- `/api/demo/run`: HTTP 200
- `/api/demo/latest`: HTTP 200

## Screenshot Yolları

- `reports/screenshots/phase20_4_evidence_spacing_polish/01_manual_smoke_spacing_fixed.png`
- `reports/screenshots/phase20_4_evidence_spacing_polish/02_reports_ktr_spacing_clean.png`

## Guard Sonucu

- Combined endpoint row artık yok:
  `/api/demo/readiness, /api/demo/run, /api/demo/latest`
- Her endpoint kendi HTTP status değeriyle ayrı item olarak render ediliyor.
- Report/KTR evidence label/value spacing temiz kaldı.

## Commit Hashleri

- Başlangıç commit'i: `3aed669 fix: guard no physical command summary wording`
- Task commit'i: final yanıtta raporlanmıştır.

## Safety Invariant Kanıtı

- `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false` korunmuştur.
- Bu task yalnızca evidence screenshot layout ve test guard eklemiştir.
- Fiziksel komut, motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmemiştir.

## Bilinen Eksikler

- Screenshotlar lokal evidence panel olarak üretilmiştir; tarayıcı piksel testi bu task kapsamında çalıştırılmadı.

## Sonraki Önerilen Task

- Faz 21'e geçmeden önce demo evidence panellerinin tamamı aynı spacing helper ile ortaklaştırılabilir.
