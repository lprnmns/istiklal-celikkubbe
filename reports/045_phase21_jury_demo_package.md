# Faz 21 - Jury Demo Evidence Package

## Amaç

ISTIKLAL C2 Console'u jüri/demo sunumu için tek bakışta anlaşılır, taşınabilir ve kanıtlanabilir release/demo paketine dönüştürmek.

## Yapılanlar

- `/demo` sayfası Jury Demo Center olarak genişletildi.
- `Run full demo evidence` akışı safety snapshot, first-run/profile state, vision evidence, Data Lab session, replay, annotation, dataset health, readiness ve KTR/report export adımlarını tek timeline altında birleştiriyor.
- Demo Verdict kartı split readiness alanlarını ayrı gösteriyor:
  - `release_demo_ready`
  - `release_demo_blockers`
  - `release_demo_warnings`
  - `competition_ready`
  - `competition_blockers`
  - `dataset_ready_for_training`
  - `dataset_blockers`
  - `no_physical_command_generated`
- Known Limitations kartı eklendi.
- Evidence Index kartı eklendi.
- Reports ekranına Latest Demo Package bölümü eklendi.
- KTR/report export içine yeni demo package dosyaları eklendi:
  - `jury_demo_summary.md`
  - `release_demo_verdict.json`
  - `evidence_index.md`
  - `known_limitations.md`
  - `demo_operator_script.md`
- Interfaces/KTR 4.3 metnine Jury Demo Center ve demo package kanıt dosyaları eklendi.
- Yeni log eventleri eklendi:
  - `demo.jury_package_generated`
  - `demo.evidence_index_generated`
  - `demo.operator_script_generated`

## Jüri Demo Merkezi Özeti

- Sistem güvenliği tek kartta görünüyor.
- Release demo readiness ve competition readiness ayrı tutuluyor.
- Dataset readiness ayrı tutuluyor.
- Latest Data Lab session, latest replay, annotation review ve latest report export özetleri tek yerde görünüyor.
- Her kritik kartta `NO PHYSICAL COMMAND` / `no_physical_command_generated=true` kanıtı korunuyor.

## KTR/Report Katkısı

- `jury_demo_summary.md`: jüriye tek sayfalık demo özeti.
- `release_demo_verdict.json`: release/demo, competition ve dataset verdict ayrımı.
- `evidence_index.md`: önemli kanıt dosyalarının indeksi.
- `known_limitations.md`: production YOLO, gerçek kamera, Pico telemetry, self-test eksikleri.
- `demo_operator_script.md`: jüri önünde izlenecek demo akışı.

## Test/build Sonuçları

- `uv run pytest backend/tests/test_phase21_jury_demo_package.py -q`: PASSED, 4 passed
- `uv run pytest -q`: PASSED, 235 passed
- `pnpm typecheck`: PASSED
- `pnpm build`: PASSED
- `python3 scripts/check_release.py`: PASSED
- `bash -n release/linux/start_istiklal_c2.sh`: PASSED
- `bash -n start_linux.sh`: PASSED

## Manual Smoke

- `/demo`: HTTP 200
- `/dashboard`: HTTP 200
- `/data-lab`: HTTP 200
- `/reports`: HTTP 200
- `/interfaces`: HTTP 200
- `/logs`: HTTP 200
- `/api/demo/readiness`: HTTP 200
- `/api/demo/run`: HTTP 200
- `/api/demo/latest`: HTTP 200
- `/api/demo/timeline`: HTTP 200

## Screenshot Yolları

- `reports/screenshots/phase21_jury_demo_package/01_demo_center_overview.png`
- `reports/screenshots/phase21_jury_demo_package/02_demo_verdict_split_semantics.png`
- `reports/screenshots/phase21_jury_demo_package/03_evidence_index.png`
- `reports/screenshots/phase21_jury_demo_package/04_known_limitations.png`
- `reports/screenshots/phase21_jury_demo_package/05_reports_latest_demo_package.png`
- `reports/screenshots/phase21_jury_demo_package/06_logs_jury_package_events.png`
- `reports/screenshots/phase21_jury_demo_package/07_interfaces_jury_demo_section.png`

## Commit Hashleri

- Başlangıç commit'i: `2af61de fix: polish evidence endpoint spacing`
- Task commit'i: final yanıtta raporlanmıştır.

## Bilinen Eksikler

- Production YOLO modeli henüz yüklenmedi.
- Gerçek laptop/USB kamera kanıtı henüz alınmadı.
- Pico telemetry doğrulaması henüz yapılmadı.
- Self-test current state tamamlanmadan competition readiness geçmez.
- Mock/surrogate evidence yalnızca release/demo kanıtıdır, yarışma/prod kanıtı değildir.

## Safety Invariant Kanıtı

- `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false` korunmuştur.
- Yeni demo/report/log çıktılarında `no_physical_command_generated=true` korunmuştur.
- Fiziksel komut, motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmemiştir.

## Sonraki Önerilen Task

- Faz 22'ye geçmeden önce gerçek demo provasında Jury Demo Center akışının operatör süreleri ve ekran sırası gözden geçirilebilir.
