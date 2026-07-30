# Ara Task 8.2 - Final UI Consistency Fixes Before Dataset/Replay

## Yapılanlar

- Pico pin Apply/Save akışı validasyon, DISARMED durumu ve critical issue durumuna bağlandı.
- Pico pinout üzerinde safety-critical, ESTOP, servo PWM, STEP/DIR motor ve limit switch pinleri ayrı renk/badge ile görünür hale getirildi.
- Serial Safe JSON sender auto-increment seq davranışına geçirildi; manual seq ve duplicate seq warning eklendi.
- Safety gate label/reason gösterimleri operatör dostu hale getirildi; teknik id ikincil metin olarak bırakıldı.
- Fire Request Evaluation sonrası ana Safety ekranına structured response card eklendi.
- Arm Dry-run butonu armed durumda yeniden arm çağrısı yapmayacak şekilde güncellendi; re-evaluate ve disarm akışı ayrıldı.
- Color Preview Mask sonrası mock/placeholder mask visualization görünür hale getirildi; mask preview ve latest decision mask alanları ayrıştırıldı.
- Calibration ekranında capture/stream/YOLO width ayrımı görünür hale getirildi; lens comparison notları netleştirildi.
- Logs ekranındaki export ifadesi JSONL placeholder olarak netleştirildi.
- Frontend HTTP aksiyonları için backend CORS middleware eklendi.

## Değiştirilen dosyalar

- `backend/app/main.py`
- `frontend/src/components/pico/PicoBoard.vue`
- `frontend/src/stores/decisionStore.ts`
- `frontend/src/utils/safetyLabels.ts`
- `frontend/src/views/CalibrationView.vue`
- `frontend/src/views/ColorView.vue`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/LogsView.vue`
- `frontend/src/views/PicoView.vue`
- `frontend/src/views/SafetyView.vue`
- `frontend/src/views/SerialView.vue`
- `reports/012_ui_consistency_final_fixes.md`

## Test/build sonuçları

- Backend: `uv run pytest` -> 101 passed
- Frontend: `pnpm typecheck` -> passed
- Frontend: `pnpm build` -> passed
- Manual smoke:
  - `/pico` -> 200
  - `/serial` -> 200
  - `/safety` -> 200
  - `/color` -> 200
  - `/calibration` -> 200
  - `/logs` -> 200
  - `/api/health` -> 200
  - `/api/pico/status` -> 200
  - `/api/serial/status` -> 200
  - `/api/safety/state` -> 200
  - `/api/color/config` -> 200
  - `/api/calibration/status` -> 200

## Commit hashleri

- Housekeeping: `fb8218d` - `docs: add UI safety polish audit report`
- Ara Task 8.2 feature commit: `49502bf` - `feat: fix final UI consistency before replay phase`

## Düzeltilen UI/state tutarsızlıkları

- INVALID veya critical pin profile durumunda Apply/Save artık aktif kalmıyor.
- Sistem DISARMED değilken pin profile update aksiyonu UI seviyesinde de engelleniyor.
- Safety gate ana metinlerinde `snake_case` id'ler operatöre doğrudan basılmıyor.
- `System Disarmed` label anlam karmaşası `System Mode` ve `Armed for Dry-run` ayrımıyla giderildi.
- Fire Request sonucu sadece event listesinde değil, structured response olarak görünür hale geldi.
- Serial sender aynı seq ile sürekli heartbeat gönderme davranışından çıkarıldı.
- Color mask preview ile latest classification mask state'i ayrı gösteriliyor.
- Lens comparison tablosunda kullanılan width değeri capture width olarak açıklandı.

## Kalan bilinen eksikler

- Logs export JSONL aksiyonu bu ara taskta placeholder olarak kaldı.
- Color mask preview gerçek frame yerine mock visualization üretiyor.
- Calibration lens değerleri saha kalibrasyonu ile doğrulanmış final değerler değildir.
- Önceki screenshot çalışmasından kalan `reports/screenshots/` ve `scripts/` untracked durumdadır; bu task commit'ine dahil edilmedi.

## Faz 9'a geçiş önerisi

- Faz 9'a geçmeden önce istenirse untracked screenshot/script artefaktları için ayrı bir karar verilmeli: repo artefaktı olarak commit veya çalışma çıktısı olarak dışarıda bırakma.
- Dataset/replay fazına mevcut safety varsayımları korunarak geçilebilir: sistem halen default `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false`.
