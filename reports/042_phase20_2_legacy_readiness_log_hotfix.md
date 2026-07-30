# Ara Task 20.2 - Legacy Demo Readiness Log Confusion Hotfix

## Yapılanlar

- `demo.readiness_checked` log renderer sözleşmesi geriye uyumlu hale getirildi.
- Yeni split readiness payload'ları aynı formatta korunuyor:
  `release_demo_ready`, `release_demo_blockers`, `competition_blockers`, `dataset_blockers`.
- Eski payload'lar artık doğrudan `Demo readiness checked; blockers=...` olarak gösterilmiyor.
- Eski payload'lar şu şekilde etiketleniyor:
  `Legacy demo readiness event; old combined blockers=...; see newer split readiness events for release/competition/dataset semantics; no_physical_command_generated=true.`
- Logs ekranına eski sözleşmeli readiness eventleri için `LEGACY FORMAT` / `OLD READINESS CONTRACT` etiketi eklendi.
- Event detail raw JSON alanı payload bilgisini de gösterecek şekilde genişletildi.
- Demo readiness rapor markdown'ına legacy log format notu eklendi.

## Düzeltilen Semantik Problem

- Eski `demo.readiness_checked` eventleri artık release demo readiness ile competition/dataset blocker ayrımını bozacak şekilde görünmüyor.
- Yeni event summary formatı korunuyor:
  `Demo readiness checked; release_demo_ready=true; release_blockers=0; competition_blockers=4; dataset_blockers=1; no_physical_command_generated=true.`
- Eski birleşik `blockers=4` bilgisi yalnızca legacy contract olarak açıklanıyor.

## Değiştirilen Dosyalar

- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/system.ts`
- `frontend/src/views/LogsView.vue`
- `backend/app/services/demo_timeline_service.py`
- `backend/tests/test_phase20_demo_timeline.py`

## Test/build Sonuçları

- `uv run pytest backend/tests/test_phase20_demo_timeline.py -q`: PASSED, 6 passed
- `uv run pytest -q`: PASSED, 229 passed
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

- `reports/screenshots/phase20_2_legacy_readiness_log_hotfix/01_logs_legacy_readiness_summary.png`
- `reports/screenshots/phase20_2_legacy_readiness_log_hotfix/02_logs_new_split_readiness_summary.png`
- `reports/screenshots/phase20_2_legacy_readiness_log_hotfix/03_demo_readiness_split_contract.png`
- `reports/screenshots/phase20_2_legacy_readiness_log_hotfix/04_dashboard_demo_semantics_after_hotfix.png`
- `reports/screenshots/phase20_2_legacy_readiness_log_hotfix/05_reports_legacy_log_note.png`
- `reports/screenshots/phase20_2_legacy_readiness_log_hotfix/06_api_manual_smoke.png`

## Reports/KTR Kontrolü

- Latest KTR export: `exports/reports/ktr_summary-20260511-183143-b9a29c`
- `demo_readiness_summary.md` içinde `Legacy Log Format Note` bulundu.
- Yeni readiness summary split semantics kullanıyor; eski combined blocker formatı legacy olarak açıklanıyor.

## Commit Hashleri

- Başlangıç commit'i: `4d91524 fix: align demo readiness blocker semantics`
- Task commit'i: final yanıtta ve `git log -1 --oneline` çıktısında raporlanmıştır.

## Safety Invariant Kanıtı

- `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false` korunmuştur.
- Demo readiness, timeline, report ve log eventlerinde `no_physical_command_generated=true` korunmuştur.
- Fiziksel komut, motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmemiştir.

## Bilinen Eksikler

- Eski log kayıtları fiziksel dosyada tarihsel veri olarak kalabilir; UI renderer artık bunları legacy contract olarak gösterir.
- Screenshotlar local evidence panel olarak üretildi; gerçek tarayıcı piksel testi bu ortamda Playwright olmadığı için çalıştırılmadı.

## Sonraki Önerilen Task

- Faz 21'e geçmeden önce demo sırasında kullanılacak log filtre presetlerinin operatör akışında yeterli olup olmadığı gözden geçirilebilir.
