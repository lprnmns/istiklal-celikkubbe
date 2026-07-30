# Pre-Phase 9 Hotfix Raporu

## Yapılanlar

- `reports/012_ui_consistency_final_fixes.md` housekeeping commit'i alındı.
- Pico Apply/Save butonu invalid/critical/non-DISARMED durumda gri disabled görünecek şekilde düzeltildi.
- Safety gate reason metinlerinde `System Mode` ve `Armed for Dry-run` ayrımı netleştirildi.
- Calibration lens comparison tablosu capture pixel ve YOLO inference pixel değerlerini ayrı gösterecek şekilde güncellendi.
- Logs ekranına filtered count, clear filters, empty filter state ve boş detail state eklendi.
- Topbar build bilgisi boş kalmayacak şekilde `Phase 8 - build 0faa53b` fallback etiketiyle güncellendi.
- Önceki screenshot kanıtları silinip hotfix sonrası güncel screenshot seti yeniden üretildi.
- Screenshot alma script'i tekrar kullanılabilir geliştirme aracı olarak dokümante edildi.

## Değiştirilen dosyalar

- `backend/app/services/decision_engine.py`
- `frontend/src/views/PicoView.vue`
- `frontend/src/views/CalibrationView.vue`
- `frontend/src/views/LogsView.vue`
- `frontend/src/components/layout/AppShell.vue`
- `docs/dev_scripts.md`
- `scripts/capture_ui_screenshots.py`
- `reports/screenshots/ui_safety_polish/*.png`
- `reports/013_pre_phase9_hotfix.md`

## Test/build sonuçları

- Backend: `uv run pytest` -> 101 passed
- Frontend: `pnpm typecheck` -> passed
- Frontend: `pnpm build` -> passed
- Manual smoke:
  - `/pico` -> 200
  - `/safety` -> 200
  - `/calibration` -> 200
  - `/logs` -> 200

## Commit hashleri

- `5222427` - `docs: add final UI consistency fixes report`
- `5835466` - `fix: clean pre phase 9 UI details`

## Untracked artefact kararı

- Screenshotlar küçük ve raporlama kanıtı olduğu için `reports/screenshots/ui_safety_polish/` altında commit'e alındı.
- `scripts/capture_ui_screenshots.py` geçici silinmedi; aynı UI kanıt setini tekrar üretmek için tekrar kullanılabilir dev aracı olarak tutuldu.
- Script kullanım notu `docs/dev_scripts.md` içine eklendi.

## Faz 9'a geçiş önerisi

- Faz 9'a geçilebilir.
- Geçişte mevcut güvenlik varsayımları korunmalı: `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false`.
- Dataset/replay geliştirmesi vision output veya color decision bilgisini fiziksel aksiyona bağlamamalı.
