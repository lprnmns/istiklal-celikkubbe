# Faz 7 - Motion/Turret Dry-Run Kontrol Raporu

## Yapılanlar

- `reports/008_phase6_decision_safety.md` housekeeping commit'i tamamlandı.
- Backend motion/turret dry-run katmanı eklendi.
- Motion state, settings, komut request/response Pydantic şemaları oluşturuldu.
- `/api/motion/*` endpointleri eklendi.
- Motion settings `config/config.yaml` ve config validation şemasına eklendi.
- Jog, go-to, home, stop, scan ve tracking dry-run komut yolları eklendi.
- Tüm motion komutları `no_physical_command_generated=true` kalacak şekilde sınırlandı.
- Motion komutları JSONL loglara yazıldı.
- Decision/safety gate listesine motion gate'leri eklendi.
- WebSocket motion eventleri eklendi.
- Frontend `/motion` route'u, motion store, API client ve taret dry-run ekranı eklendi.
- Dashboard'a Motion Status kartı eklendi.
- Safety gate özetine motion gate durumları eklendi.
- `docs/motion_phase7.md` dokümantasyonu oluşturuldu.

## Oluşturulan/değiştirilen dosyalar

- `backend/app/api/motion.py`
- `backend/app/api/routes_ws.py`
- `backend/app/main.py`
- `backend/app/schemas/config.py`
- `backend/app/schemas/motion.py`
- `backend/app/schemas/safety.py`
- `backend/app/services/decision_engine.py`
- `backend/app/services/motion_service.py`
- `backend/app/services/runtime_state.py`
- `backend/app/services/safety_service.py`
- `backend/app/services/turret_service.py`
- `backend/tests/test_config.py`
- `backend/tests/test_motion.py`
- `config/config.yaml`
- `docs/motion_phase7.md`
- `frontend/src/api/motion.ts`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/components/safety/SafetyGatesPanel.vue`
- `frontend/src/router/index.ts`
- `frontend/src/stores/motionStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/motion.ts`
- `frontend/src/types/system.ts`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/MotionView.vue`

## Çalıştırılan komutlar

- `git status --short`
- `git add reports/008_phase6_decision_safety.md && git commit -m "docs: add phase 6 decision safety report"`
- `uv run pytest`
- `pnpm typecheck`
- `pnpm build`
- `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
- `pnpm dev --host 127.0.0.1 --port 5173`
- `curl -s http://127.0.0.1:8000/api/motion/status`
- `curl -s -X POST http://127.0.0.1:8000/api/motion/jog -H 'Content-Type: application/json' -d '{"axis":"pan","direction":"positive","step_deg":1}'`
- `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5173/motion`
- `git diff --check`
- `git add backend/app frontend/src backend/tests config/config.yaml docs/motion_phase7.md && git commit -m "feat: add dry-run turret motion controls"`

## Test/build sonuçları

- Backend: `83 passed in 6.69s`
- Frontend typecheck: `vue-tsc -b` başarılı.
- Frontend build: `vite build` başarılı.
- Manuel HTTP smoke:
  - `GET /api/motion/status` başarılı, default `IDLE`, `dry_run=true`.
  - `POST /api/motion/jog` başarılı, response `accepted=true`, `no_physical_command_generated=true`.
  - `/motion` route HTTP `200` döndü.

## Git commit hashleri

- `e0d0a63 docs: add phase 6 decision safety report`
- `4d11fd3 feat: add dry-run turret motion controls`

## Motion/turret mimarisi özeti

- `MotionService` motion komutlarını validate eder, simüle state üretir ve JSONL loglar.
- `TurretService` ileride taret davranışlarını ayırmak için servis sarmalayıcı olarak eklendi.
- `MotionSettings` runtime memory state olarak güncellenir; bu fazda config dosyasına kalıcı yazım yapılmaz.
- Frontend motion store, HTTP endpointleri ve WebSocket `motion.*` eventleri ile güncellenir.

## Dry-run safety davranışı

- Gerçek motor/Pico/serial motion komutu üretilmez.
- Response'larda `no_physical_command_generated=true`.
- `hardware_enabled=false`, `motion.dry_run=true`, `motion.real_motion_enabled=false` varsayılanları korunur.
- Sistem ARMED ise motion settings ve unsafe motion komutları reddedilir.
- E-stop, limit switch, soft limit ve FAULT durumları komut reddi üretir.

## Frontend Motion ekranı özeti

- Motion state, pan/tilt pozisyon, target ve limit durum kartları eklendi.
- Jog, go-to, home, stop, scan dry-run ve tracking preview kontrolleri eklendi.
- 2D taret görselleştirmesi current/target pan-tilt değerlerini gösterir.
- Editable settings paneli backend validation'a bağlıdır.
- Komut log tablosu accepted/rejected dry-run response'larını gösterir.

## Motion validation kuralları

- Soft limit dışında hedef reddedilir.
- Pan/tilt min-max ayarları ters veya eşit olamaz.
- Speed/acceleration negatif olamaz.
- Steps per degree `> 0` olmalıdır.
- E-stop aktifse motion komutu reddedilir.
- Limit switch aktif yönde hareket reddedilir.
- FAULT state içinde stop dışındaki unsafe komut reddedilir.
- Scan disabled ise scan start reddedilir.

## Bilinen eksikler

- Motion settings kalıcı config dosyasına yazılmıyor; runtime memory state olarak kalıyor.
- Gerçek encoder/limit/driver telemetrisi yok; mock/simulated state kullanılıyor.
- Store unit test altyapısı yok; frontend için typecheck/build ve manuel smoke yapıldı.
- Tracking dry-run sadece pixel error ve gain çarpımı ile preview hesaplıyor; closed-loop kontrol yok.

## Riskler

- Placeholder motion limitleri ve steps/degree değerleri kalibrasyon yapılmadan fiziksel sistem için kullanılamaz.
- İleride gerçek motion aktif edilecekse backend safety gate yanında Pico local safety, limit switch debounce ve serial ACK/fault modeli birlikte zorunlu olmalı.
- Motion gate warning'leri UI'da görünür, ancak Phase 7 fiziksel yetki vermediği için driver disabled beklenen durumdur.

## Bir sonraki önerilen task

- Faz 8: Calibration ve self-check ön hazırlığı ya da proje planındaki sıraya göre sonraki ana task. Gerçek motion veya fire entegrasyonuna geçilmeden önce Pico local safety ve kalibrasyon verisi netleştirilmeli.
