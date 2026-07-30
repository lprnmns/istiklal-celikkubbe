# Ara Task 8.1 - UI/UX Safety Polish ve State Consistency Audit Raporu

## Yapılanlar

- `reports/010_phase8_calibration_color.md` housekeeping commit'i tamamlandı.
- Global status ayrımı topbar/sidebar ve dashboard üzerinde netleştirildi.
- Backend, Pico, mock Pico, camera stream, vision inference, serial transport, hardware enabled, dry-run ve fire policy ayrı badge/metrikler olarak gösterildi.
- Tüm kritik ekranlarda `MOCK DATA`, `REAL HARDWARE DISABLED`, `ADVISORY ONLY`, `NO PHYSICAL COMMAND` görünürlüğü artırıldı.
- Vision stopped iken body/balloon count değerleri `0` olacak şekilde backend status tutarlılığı düzeltildi.
- Pico disconnected iken heartbeat `0ms` yerine `null/not available` olarak raporlanıyor.
- Pico API hata modeli endpoint/method/status/suggestion alanlarıyla kullanıcıya okunur hale getirildi.
- Pico connect butonu port seçimi yokken disabled hale getirildi.
- Safety gate ve blocking reason id'leri human-readable label ile gösteriliyor; teknik id küçük alt metin olarak kalıyor.
- Blocking reason listeleri dedupe edildi.
- Safety ekranı `System Gates`, `Target Gates`, `Motion Gates`, `Advisory/Mock Gates` olarak gruplandı.
- Dashboard'a Mission Readiness, System Health ve Live Target Summary kartları eklendi.
- Logs ekranına type filter, severity filter, search, pause live, clear view, event detail ve export placeholder eklendi.
- Color ekranında latest decision mask state ile preview mask state ayrıldı; body-only/baloon-excluded uyarısı güçlendirildi.
- Calibration ekranına 3.6mm/8mm/12mm lens comparison table, threshold açıklaması ve FOV diagram placeholder eklendi.
- Motion ekranında dry-run preview buton etiketleri, sticky stop ve no-command-generated uyarısı güçlendirildi.
- Vision ekranında camera stream state, vision inference state, overlay source ve detection source ayrıldı; mock frame etiketi eklendi.
- Topbar `ISTIKLAL C2 Console · Build: Phase 8` olarak güncellendi.

## Oluşturulan/değiştirilen dosyalar

- `backend/app/schemas/pico.py`
- `backend/app/services/pico_service.py`
- `backend/app/services/vision_service.py`
- `frontend/src/api/pico.ts`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/components/safety/SafetyGatesPanel.vue`
- `frontend/src/stores/colorStore.ts`
- `frontend/src/stores/decisionStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/pico.ts`
- `frontend/src/utils/safetyLabels.ts`
- `frontend/src/views/CalibrationView.vue`
- `frontend/src/views/ColorView.vue`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/LogsView.vue`
- `frontend/src/views/MotionView.vue`
- `frontend/src/views/PicoView.vue`
- `frontend/src/views/SafetyView.vue`
- `frontend/src/views/VisionView.vue`

## Çalıştırılan komutlar

- `git status --short`
- `git add reports/010_phase8_calibration_color.md && git commit -m "docs: add phase 8 calibration color report"`
- `uv run pytest`
- `pnpm typecheck`
- `pnpm build`
- `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
- `pnpm dev --host 127.0.0.1 --port 5173`
- `/usr/bin/curl` route smoke:
  - `/`
  - `/safety`
  - `/pico`
  - `/serial`
  - `/vision`
  - `/motion`
  - `/calibration`
  - `/color`
  - `/logs`
- `/usr/bin/curl http://127.0.0.1:8000/api/pico/status`
- `/usr/bin/curl http://127.0.0.1:8000/api/vision/status`
- `git diff --check`
- `git add backend/app frontend/src && git commit -m "feat: polish UI state consistency and safety visibility"`

## Test/build sonuçları

- Backend: `101 passed in 9.87s`
- Frontend typecheck: `vue-tsc -b` başarılı.
- Frontend build: `vite build` başarılı.
- Manuel route smoke:
  - `/` -> `200`
  - `/safety` -> `200`
  - `/pico` -> `200`
  - `/serial` -> `200`
  - `/vision` -> `200`
  - `/motion` -> `200`
  - `/calibration` -> `200`
  - `/color` -> `200`
  - `/logs` -> `200`
- API smoke:
  - `/api/pico/status`: disconnected durumda `heartbeat_age_ms=null`.
  - `/api/vision/status`: stopped durumda `body_count=0`, `balloon_count=0`.

## Git commit hashleri

- `2667114 docs: add phase 8 calibration color report`
- `444a3b5 feat: polish UI state consistency and safety visibility`

## State consistency özeti

- Backend connection, physical Pico connection, mock Pico active, camera stream, vision inference, serial transport ve motion dry-run UI’da ayrı etiketleniyor.
- Mock telemetry fiziksel bağlantı gibi gösterilmiyor.
- Vision stopped durumunda eski latest detection count değerleri dashboard ve status üzerinde gösterilmiyor.
- Pico heartbeat disconnected durumda yanıltıcı `0ms` göstermiyor.

## Safety görünürlüğü özeti

- Safety gate id’leri operatör dostu label’larla gösteriliyor.
- Blocking reasons dedupe edildi ve human-readable hale getirildi.
- Dashboard mission readiness ana blocker’ı gösteriyor.
- Motion/Color/Vision ekranlarında advisory/dry-run/no-physical-command sınırları daha belirgin.

## Bilinen eksikler

- Logs export JSON sadece placeholder; dosya indirme veya backend export yok.
- Event detail drawer/modal yerine mevcut kart içinde detail panel kullanıldı.
- Route smoke HTTP düzeyinde yapıldı; Playwright görsel regression eklenmedi.
- Pico NetworkError bug’ı için hata modeli düzeltildi; gerçek tarayıcı ortamında backend kapalı senaryo manuel olarak ayrıca gözlenmedi.

## Riskler

- UI safety polish gerçek hardware safety yerine geçmez; backend/Pico local safety kapıları zorunlu kalır.
- Mock/real ayrımı artık daha görünür, ancak ileride gerçek hardware enable edildiğinde tüm badge ve command path’ler yeniden audit edilmeli.
- Logs ekranı client-side event buffer kullanıyor; uzun süreli forensic log için backend JSONL esas kaynak olmaya devam ediyor.

## Bir sonraki önerilen task

- Faz 9’a geçmeden önce `reports/011_ui_safety_polish_audit.md` dosyası housekeeping commit’i olarak alınmalı. Sonraki ana task için Dataset/Replay hattı önerilir.
