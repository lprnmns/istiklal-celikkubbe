# Phase 20.1 - Demo Readiness Semantic Consistency Hotfix

## Yapılanlar

- Demo readiness response semantiği ayrıştırıldı.
- Tek `blockers` alanı kaldırıldı; release demo, competition ve dataset readiness ayrı alanlara bölündü.
- `/demo` ekranında readiness nedenleri ayrı bölümler halinde gösterildi.
- Dashboard Demo Evidence kartı aynı ayrımı kullanacak şekilde güncellendi.
- Reports/KTR export içindeki `demo_readiness_summary.md` ve `demo_timeline.md` final verdict metinleri ayrıştırıldı.
- `demo.readiness_checked` log summary metni belirsiz toplam blocker sayısı yerine ayrı sayaçlar dönecek şekilde düzeltildi.

## Düzeltilen Semantik

Yeni alanlar:

- `release_demo_ready`
- `release_demo_warnings`
- `release_demo_blockers`
- `competition_ready`
- `competition_blockers`
- `dataset_ready_for_training`
- `dataset_blockers`
- `no_physical_command_generated`

Kurallar:

- `release_demo_ready=true` ise `release_demo_blockers=[]` olmalı.
- First-run current status not passed durumu release demo için warning olarak gösterilir; demo akışını tek başına engellemez.
- Production YOLO, Pico telemetry, real camera evidence ve completed self-test eksikleri competition blockers altında gösterilir.
- Dataset yetersizliği dataset blockers altında gösterilir.
- Mock/surrogate evidence release demo için kabul edilebilir, competition için blocker kalır.

## UI Sonucu

- `/demo` readiness kartında şu bölümler ayrı görünür:
  - Release demo warnings
  - Release demo blockers
  - Competition blockers
  - Dataset blockers
- Dashboard Demo Evidence kartı release blockers, competition blockers ve dataset blockers sayılarını ayrı gösterir.

## Reports/KTR Sonucu

- `demo_readiness_summary.md` içinde ayrı başlıklar yer alır:
  - Release Demo Warnings
  - Release Demo Blockers
  - Competition Blockers
  - Dataset Blockers
- `demo_timeline.md` final verdict bölümünde aynı ayrım bulunur.
- `blocker` kelimesi yalnızca ilgili readiness alanını gerçekten engelleyen durumlar için kullanılır.

## Logs Sonucu

Yeni summary formatı:

`Demo readiness checked; release_demo_ready=true; release_blockers=0; competition_blockers=4; dataset_blockers=1; no physical command generated.`

Generic `telemetry update` kullanılmadı.

## Test/Build Sonuçları

- `uv run pytest -q`: geçti, 227 passed.
- `pnpm typecheck`: geçti.
- `pnpm build`: geçti.
- `python3 scripts/check_release.py`: geçti.
- `bash -n release/linux/start_istiklal_c2.sh`: geçti.
- `bash -n start_linux.sh`: geçti.

## Manual Smoke

Port `8001` üzerinde kontrol edildi:

- `/demo`: 200
- `/dashboard`: 200
- `/reports`: 200
- `/logs`: 200
- `/api/demo/readiness`: 200
- `/api/demo/run`: 200
- `/api/demo/latest`: 200

## Screenshot Yolları

- `reports/screenshots/phase20_1_demo_readiness_semantic_hotfix/01_demo_readiness_split_sections.png`
- `reports/screenshots/phase20_1_demo_readiness_semantic_hotfix/02_dashboard_demo_semantics.png`
- `reports/screenshots/phase20_1_demo_readiness_semantic_hotfix/03_reports_readiness_summary_semantics.png`
- `reports/screenshots/phase20_1_demo_readiness_semantic_hotfix/04_logs_readiness_checked_summary.png`
- `reports/screenshots/phase20_1_demo_readiness_semantic_hotfix/05_api_demo_readiness_response.png`
- `reports/screenshots/phase20_1_demo_readiness_semantic_hotfix/06_safety_invariant_preserved.png`

## Safety Invariant

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmedi.

## Bilinen Eksikler

- Competition readiness hâlâ false: production YOLO, gerçek kamera evidence, Pico telemetry ve self-test eksik.
- Dataset readiness hâlâ false: mock/surrogate evidence ve yetersiz gerçek veri nedeniyle.

## Sonraki Önerilen Task

Faz 21’e geçmeden önce istenirse demo readiness UI’daki Türkçe metinler daha operatör-dostu hale getirilebilir. Faz 21’e geçilmedi.
