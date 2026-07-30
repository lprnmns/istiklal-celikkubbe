# Faz 10 Raporu - Self-Test Wizard ve Kabul Testleri

## Yapılanlar

- Backend Self-Test run/step şemaları eklendi.
- Self-Test servis ve API endpointleri eklendi.
- Self-Test WebSocket eventleri eklendi.
- Self-Test rapor üretimi eklendi: JSON ve Markdown.
- Frontend `/self-test` ekranı eklendi.
- Sidebar'a Self-Test route'u eklendi.
- Dashboard'a Self-Test / Readiness kartı eklendi.
- Logs ekranı mevcut event altyapısıyla `self_test.*` eventlerini gösterebilir hale geldi.
- Backend test fixture'ı self-test raporlarını test ortamında `tmp_path` altına yazar hale getirildi.
- Faz 10 dokümantasyonu yazıldı.

## Oluşturulan/değiştirilen dosyalar

- `backend/app/schemas/self_test.py`
- `backend/app/services/self_test_service.py`
- `backend/app/api/self_test.py`
- `backend/app/api/routes_ws.py`
- `backend/app/main.py`
- `backend/app/services/runtime_state.py`
- `backend/tests/test_self_test_phase10.py`
- `backend/tests/conftest.py`
- `frontend/src/types/selfTest.ts`
- `frontend/src/api/selfTest.ts`
- `frontend/src/stores/selfTestStore.ts`
- `frontend/src/views/SelfTestView.vue`
- `frontend/src/router/index.ts`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/views/DashboardView.vue`
- `docs/self_test_phase10.md`
- `reports/self_tests/self_test_20260509_095736_selftest-b7ecada361.json`
- `reports/self_tests/self_test_20260509_095736_selftest-b7ecada361.md`

## Test/build sonuçları

- `cd backend && uv run pytest -q`: 129 passed.
- `cd frontend && pnpm typecheck`: başarılı.
- `cd frontend && pnpm build`: başarılı.
- Manual smoke:
  - `/self-test`: 200
  - `/`: 200
  - `/logs`: 200
  - `POST /api/self-test/run`: 200

## Git commit hashleri

- `23ddbf3` - `docs: add phase 9 e2e acceptance report`
- `3634328` - `feat: add self-test wizard and readiness checks`

## Self-Test Wizard özeti

- `/api/self-test/run` tek çağrıda tüm kabul kontrol listesini çalıştırıyor.
- Kontroller kategorilere ayrıldı: backend/config/safety/pico/serial/vision/model/motion/dataset/replay/logging.
- UI'da overall readiness, progress, category summary, warning/failure listesi, step timeline ve rapor bağlantısı gösteriliyor.
- Ekranda açık uyarı var: `Self-test readiness does not enable physical fire.`

## Readiness hesaplama özeti

- Critical failed step varsa `overall_ready=false`, `readiness_level=not_ready`.
- Critical failure yok ve warning varsa `status=warning`, `readiness_level=demo_ready`.
- `hardware_enabled=false` olduğu için self-test başarılı olsa bile fiziksel field readiness verilmez.
- Gerçek donanım kontrolleri bu fazda mock/disabled durumun doğru temsil edilmesi olarak değerlendirilir.

## Safety invariant kanıtı

- Oluşturulan self-test sonucu:
  - status: `warning`
  - readiness_level: `demo_ready`
  - critical_failures: `0`
  - no_physical_command_generated: `true`
  - dry_run: `true`
  - hardware_enabled: `false`
- Riskli serial TX step'i reddedildi.
- Fire request default olarak reddedildi.
- Motion jog sadece dry-run accepted oldu.
- Model inference sonucu `no_physical_command_generated=true` döndü.

## Frontend Self-Test ekranı özeti

- Route: `/self-test`
- Run self-test ve cancel butonları var.
- Overall readiness card, progress bar, category summary, suggested actions ve full step timeline gösteriliyor.
- Latest report bağlantısı backend markdown rapor endpointine gidiyor.
- Dashboard'da latest self-test status, readiness, critical failures, warnings ve no physical command özeti görünüyor.

## Üretilen self-test raporu yolu

- Markdown: `reports/self_tests/self_test_20260509_095736_selftest-b7ecada361.md`
- JSON: `reports/self_tests/self_test_20260509_095736_selftest-b7ecada361.json`

## Bilinen eksikler

- Self-test şu anda senkron çalışıyor; uzun saha kontrolleri eklendiğinde async/background run yapısına taşınabilir.
- Frontend cancel butonu mevcut, ancak self-test çok hızlı tamamlandığı için pratikte çoğu run tamamlandıktan sonra etkisiz kalır.
- Gerçek hardware kontrolleri deliberately mock/disabled state doğrulaması olarak bırakıldı.

## Riskler

- `demo_ready` fiziksel sistem yetkisi olarak yorumlanmamalı.
- Self-test raporu runtime durumuna bağlıdır; yarışma günü raporu her demo öncesi yeniden üretilmelidir.
- İleride `hardware_enabled=true` akışı eklendiğinde readiness hesaplama ve safety gates yeniden sıkı review gerektirir.

## Bir sonraki önerilen task

Faz 11: KTR export/polish ve teslim paketleme akışı. Faz 11'e geçmeden önce bu raporun housekeeping commit'i alınmalı.
