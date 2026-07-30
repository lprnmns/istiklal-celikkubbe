# Faz 8 - Kamera Kalibrasyon ve Dost/Düşman Renk Ayarları Raporu

## Yapılanlar

- `reports/009_phase7_motion_controls.md` housekeeping commit'i tamamlandı.
- Backend calibration ve color classifier servis katmanları eklendi.
- Calibration/color Pydantic schema setleri oluşturuldu.
- Calibration endpointleri eklendi.
- Color endpointleri eklendi.
- Config içine `calibration:` ve `color:` bölümleri eklendi.
- FOV/pixel estimate hesaplayıcısı eklendi.
- Mock color classifier ile enemy/friend/unknown sample sınıflandırması eklendi.
- Kırmızı balon maskesi davranışı ve `balloon_mask_not_applied` warning'i eklendi.
- Decision engine renk sonucunu advisory metadata olarak okuyabilir hale getirildi.
- WebSocket `calibration.*` ve `color.*` eventleri eklendi.
- Frontend `/calibration` ve `/color` ekranları oluşturuldu.
- Vision body detection tablosuna advisory color decision alanı eklendi.
- `docs/calibration_color_phase8.md` dokümantasyonu oluşturuldu.

## Oluşturulan/değiştirilen dosyalar

- `backend/app/api/calibration.py`
- `backend/app/api/color.py`
- `backend/app/api/routes_ws.py`
- `backend/app/main.py`
- `backend/app/schemas/calibration.py`
- `backend/app/schemas/color.py`
- `backend/app/schemas/config.py`
- `backend/app/schemas/vision.py`
- `backend/app/services/calibration_service.py`
- `backend/app/services/color_classifier_service.py`
- `backend/app/services/decision_engine.py`
- `backend/app/services/runtime_state.py`
- `backend/tests/test_calibration_color.py`
- `backend/tests/test_config.py`
- `config/config.yaml`
- `docs/calibration_color_phase8.md`
- `frontend/src/api/calibration.ts`
- `frontend/src/api/color.ts`
- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/router/index.ts`
- `frontend/src/stores/calibrationStore.ts`
- `frontend/src/stores/colorStore.ts`
- `frontend/src/stores/systemStore.ts`
- `frontend/src/types/calibration.ts`
- `frontend/src/types/color.ts`
- `frontend/src/types/vision.ts`
- `frontend/src/views/CalibrationView.vue`
- `frontend/src/views/ColorView.vue`
- `frontend/src/views/VisionView.vue`

## Çalıştırılan komutlar

- `git status --short`
- `git add reports/009_phase7_motion_controls.md && git commit -m "docs: add phase 7 motion controls report"`
- `uv run pytest`
- `pnpm typecheck`
- `pnpm build`
- `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
- `pnpm dev --host 127.0.0.1 --port 5173`
- `curl -s http://127.0.0.1:8000/api/calibration/status`
- `curl -s -X POST http://127.0.0.1:8000/api/color/classify-sample -H 'Content-Type: application/json' -d '{"frame_id":1,"detection_id":1,"mock_team":"enemy","balloon_bbox_present":true}'`
- `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5173/calibration`
- `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5173/color`
- `git diff --check`
- `git add backend/app backend/tests config/config.yaml docs/calibration_color_phase8.md frontend/src && git commit -m "feat: add calibration and color tuning tools"`

## Test/build sonuçları

- Backend: `101 passed in 10.19s`
- Frontend typecheck: `vue-tsc -b` başarılı.
- Frontend build: `vite build` başarılı.
- Manuel smoke:
  - `GET /api/calibration/status` başarılı; default `field_calibration_required`.
  - `POST /api/color/classify-sample` başarılı; mock enemy sonucu `decision=enemy`, `balloon_mask_applied=true`.
  - `/calibration` route HTTP `200`.
  - `/color` route HTTP `200`.

## Git commit hashleri

- `9b462e8 docs: add phase 7 motion controls report`
- `b46974a feat: add calibration and color tuning tools`

## Calibration mimarisi özeti

- `CalibrationService` runtime memory state üzerinde kamera/lens profilini, kalibrasyon noktalarını, homography placeholder sonucunu ve warning listesini yönetir.
- `POST /api/calibration/fov-estimate` HFOV, mesafe, obje genişliği ve image width ile görünür genişlik/piksel tahmini üretir.
- Kalibrasyon noktası ekleme/silme ve compute aksiyonları JSONL loglanır.
- Homography gerçek çözümü bu fazda yok; en az 4 nokta ve `homography_enabled=true` durumunda testlenebilir placeholder matrix döner.

## Color classifier mimarisi özeti

- `ColorClassifierService` HSV config, balon maskesi ayarı, mock sample sınıflandırması ve mask preview sonucunu yönetir.
- Enemy/friend/unknown sonuçları pixel ratio ve confidence ile döner.
- LAB bu fazda toggle/placeholder olarak tutulur.
- Color config değişimi ve classification sample sonuçları JSONL loglanır.
- Decision engine son color result'ı body detection id ile eşleştirip advisory team metadata olarak okuyabilir.

## Balon maskeleme davranışı

- `balloon_mask_enabled=true` default.
- Balloon bbox varsa mask uygulanmış kabul edilir.
- Balloon bbox yoksa `balloon_mask_not_applied` warning'i üretilir.
- Balon rengi dost/düşman kararına dahil edilmez.

## Frontend Calibration/Color ekranları özeti

- `/calibration`:
  - kamera/lens profile card
  - geometry inputları
  - FOV estimator
  - 5m/10m/15m pixel estimate tablosu
  - calibration point add/delete
  - homography/reprojection status
  - warning paneli
- `/color`:
  - enemy/friend HSV sliderları
  - LAB placeholder toggle
  - balon maskesi toggle
  - min pixel/threshold/consistent frame ayarları
  - mock sample classifier
  - mask preview
  - pixel ratio bars
  - warnings listesi
- Vision sayfası body detection satırlarında advisory color decision gösterir.

## Bilinen eksikler

- Gerçek OpenCV crop/mask pipeline henüz uygulanmadı.
- Gerçek homography çözümü yok; placeholder matrix var.
- Kalibrasyon/color ayarları runtime memory state olarak kalıyor; profile registry veya kalıcı YAML yazımı yok.
- Color store için ayrı unit test altyapısı yok; frontend typecheck/build ve route smoke yapıldı.

## Riskler

- Placeholder HSV aralıkları saha ışığı, kamera beyaz dengesi ve materyal rengine göre güvenilir kabul edilmemeli.
- Kırmızı balon ile kırmızı düşman rengi çakışabileceği için balon maskesi gerçek frame üzerinde doğrulanmadan karar güvenilir değildir.
- Renk sonucu decision engine tarafından okunabilir hale geldi, ancak fiziksel aksiyona bağlanmadı; ileride entegrasyon yapılırsa friend/unknown durumları backend ve Pico local safety tarafında da bloklanmalı.

## Bir sonraki önerilen task

- Faz 9: Dataset/replay/veri toplama hattı. Renk ayarlarının gerçek saha verisiyle tekrar oynatılabilmesi için replay altyapısı öncelikli olmalı.
