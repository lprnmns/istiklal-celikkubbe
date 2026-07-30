# Ara Task 20.3 - No Physical Summary Guard

## Amaç

`demo.readiness_checked` log, UI ve report metinlerinde fiziksel komut güvenlik kanıtının yanlış okunmasını engellemek.

## Yapılanlar

- Yeni split readiness summary canonical hale getirildi:
  `no_physical_command_generated=true.`
- Legacy readiness summary canonical hale getirildi:
  `no_physical_command_generated=true.`
- `demo.readiness_checked` summary metinlerinde tek başına `physical command generated` gibi okunabilecek son ifade kaldırıldı.
- Logs ekranında summary kolonu multiline/wrap-safe hale getirildi:
  `whitespace-normal break-words`
- Reports/KTR demo readiness markdown çıktısında canonical ifade kullanıldı:
  `no_physical_command_generated: true`
- Phase 20.2 raporundaki örnek summary metinleri de canonical formatla güncellendi.

## Düzeltilen Güvenlik Semantiği

Önceki risk:

- Görselde satır kırılması veya truncate nedeniyle `no physical command generated` ifadesi `physical command generated` gibi okunabiliyordu.

Yeni durum:

- UI/log/report içinde demo readiness güvenlik kanıtı boolean-safe token olarak görünür:
  `no_physical_command_generated=true`
- Legacy eventler de aynı token ile render edilir.

## Değiştirilen Dosyalar

- `frontend/src/stores/systemStore.ts`
- `frontend/src/views/LogsView.vue`
- `backend/app/services/demo_timeline_service.py`
- `backend/tests/test_phase20_demo_timeline.py`
- `reports/042_phase20_2_legacy_readiness_log_hotfix.md`

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

- `reports/screenshots/phase20_3_no_physical_summary_guard/01_logs_split_summary_canonical_no_physical.png`
- `reports/screenshots/phase20_3_no_physical_summary_guard/02_logs_legacy_summary_canonical_no_physical.png`
- `reports/screenshots/phase20_3_no_physical_summary_guard/03_logs_multiline_summary_wrap_guard.png`
- `reports/screenshots/phase20_3_no_physical_summary_guard/04_reports_ktr_canonical_no_physical.png`
- `reports/screenshots/phase20_3_no_physical_summary_guard/05_demo_readiness_api_canonical_field.png`
- `reports/screenshots/phase20_3_no_physical_summary_guard/06_manual_smoke_spacing_guard.png`

## Reports/KTR Kontrolü

- Latest KTR export: `exports/reports/ktr_summary-20260511-211920-e120cc`
- `demo_readiness_summary.md` içinde bulundu:
  `no_physical_command_generated: true`
- `Legacy Log Format Note` korunmuştur.

## Commit Hashleri

- Başlangıç commit'i: `9bf5914 fix: clarify legacy demo readiness log summaries`
- Task commit'i: final yanıtta raporlanmıştır.

## Safety Invariant Kanıtı

- `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false` korunmuştur.
- Demo readiness/log/report çıktılarında `no_physical_command_generated=true` korunmuştur.
- Fiziksel komut, motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmemiştir.

## Bilinen Eksikler

- Screenshotlar local evidence panel olarak üretildi; bu ortamda Playwright bulunmadığı için gerçek browser pixel screenshot alınmadı.

## Sonraki Önerilen Task

- Faz 21'e geçmeden önce demo ekranında kullanılacak log filtre presetleri ve evidence panelleri operatör akışıyla son kez gözden geçirilebilir.
