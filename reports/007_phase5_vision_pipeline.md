# Task Raporu: Faz 5 - Kamera, Vision Pipeline ve Overlay UI

## Yapilanlar

- Housekeeping olarak Faz 4 raporu commit'e alindi.
- Backend `CameraService`, `VisionService` ve `VisionPipeline` katmanlari eklendi.
- Mock camera default olarak kuruldu.
- MJPEG stream endpointi eklendi: `GET /api/camera/stream.mjpg`.
- Vision endpointleri eklendi:
  - `GET /api/vision/status`
  - `GET /api/vision/config`
  - `PUT /api/vision/config`
  - `POST /api/vision/start`
  - `POST /api/vision/stop`
  - `POST /api/vision/snapshot`
  - `GET /api/vision/latest`
  - `GET /api/camera/status`
  - `GET /api/camera/sources`
  - `POST /api/camera/select`
- Vision event, body detection, balloon detection, track placeholder ve aim point schemalari eklendi.
- YOLO entegrasyon noktalari config ve service arayuzunde hazirlandi.
- Model path yoksa controlled warning uretiliyor; backend cokmuyor.
- Mock vision sahte ama tutarli body/balloon detection, aim point, FPS ve latency uretiyor.
- WebSocket eventleri eklendi:
  - `vision.status`
  - `vision.frame`
  - `vision.detections`
  - `vision.warning`
  - `camera.status`
- Frontend Vision sayfasi gelistirildi:
  - camera status card
  - vision pipeline status card
  - stream panel
  - SVG overlay
  - body detections table
  - balloon detections table
  - FPS/latency panel
  - latest vision events
  - start/stop/snapshot butonlari
- Dashboard Vision karti gercek vision store'dan beslenecek sekilde guncellendi.
- Vision output'un advisory only oldugu UI'da belirtildi.
- Vision output motor/fire komutuna baglanmadi.

## Olusturulan / Degistirilen Dosyalar

| Dosya | Degisiklik |
|---|---|
| `backend/app/schemas/vision.py` | Camera, vision event ve detection schemalari eklendi. |
| `backend/app/services/camera_service.py` | Camera service ve MJPEG frame kaynagi eklendi. |
| `backend/app/services/vision_service.py` | Mock vision ve YOLO entegrasyon arayuzu eklendi. |
| `backend/app/services/vision_pipeline.py` | Camera + vision pipeline state akisi eklendi. |
| `backend/app/mocks/mock_camera.py` | Mock JPEG camera kaynagi eklendi. |
| `backend/app/mocks/mock_vision.py` | Mock body/balloon detection generator eklendi. |
| `backend/app/api/vision.py` | Vision ve camera REST endpointleri eklendi. |
| `backend/app/api/routes_ws.py` | Vision/camera WebSocket eventleri eklendi. |
| `backend/app/schemas/config.py` | Camera/vision Faz 5 config validation eklendi. |
| `config/config.yaml` | Camera/vision Faz 5 default ayarlari eklendi. |
| `backend/tests/test_vision.py` | Vision/camera endpoint ve safety invariant testleri eklendi. |
| `frontend/src/types/vision.ts` | Vision frontend tipleri eklendi. |
| `frontend/src/api/vision.ts` | Vision REST/stream client eklendi. |
| `frontend/src/stores/visionStore.ts` | Vision/camera frontend store eklendi. |
| `frontend/src/views/VisionView.vue` | Stream + overlay + detection UI eklendi. |
| `frontend/src/views/DashboardView.vue` | Dashboard Vision karti vision store'a baglandi. |
| `docs/vision_phase5.md` | Faz 5 kamera/vision dokumantasyonu eklendi. |
| `reports/007_phase5_vision_pipeline.md` | Bu rapor eklendi. |

## Calistirilan Komutlar

```bash
git status --short
git add reports/006_phase4_serial_protocol.md
git commit -m "docs: add phase 4 serial protocol report"
PATH="$HOME/.local/bin:$PATH" uv run pytest
pnpm typecheck
pnpm build
curl -sS http://127.0.0.1:8000/api/vision/status
curl -sS http://127.0.0.1:8000/api/vision/latest
curl -sS -I http://127.0.0.1:5173/vision
curl -m 1 -sS -D - http://127.0.0.1:8000/api/camera/stream.mjpg -o /dev/null
git add backend config docs/vision_phase5.md frontend/src
git commit -m "feat: add camera vision pipeline and overlay"
```

## Test / Build Sonuclari

```text
Backend pytest: 48 passed in 2.27s
Frontend pnpm typecheck: passed
Frontend pnpm build: passed
Manual /api/vision/status: passed
Manual /api/vision/latest: passed
Manual /api/camera/stream.mjpg: HTTP 200 multipart stream
Manual /vision frontend route: HTTP 200
```

Build ciktisi:

```text
dist/index.html                  0.45 kB
dist/assets/index-*.css         21.11 kB
dist/assets/index-*.js         143.29 kB
```

## Git Commit Hashleri

```text
2f79a14 docs: add phase 4 serial protocol report
86b242e feat: add camera vision pipeline and overlay
```

## Camera / Vision Mimarisi Ozeti

- `CameraService`: camera mode, source, status, sources, select, snapshot ve MJPEG stream sorumlulugu.
- `MockCamera`: default guvenli JPEG frame uretir.
- `VisionService`: mock detection generator ve YOLO model path validation arayuzu.
- `VisionPipeline`: start/stop/latest/configure akisini birlestirir.
- Ham frame WebSocket uzerinden gonderilmez; stream MJPEG endpointinden gelir.
- Detection metadata REST ve WebSocket uzerinden akar.

## Frontend Vision Ekrani Ozeti

- Camera status card.
- Vision pipeline status card.
- Start/stop/snapshot butonlari.
- MJPEG stream paneli.
- SVG overlay:
  - body bbox
  - balloon bbox
  - aim point marker
  - labels
  - latency label
- Body detections table.
- Balloon detections table.
- Latest event/warning badges.
- Overlay layer toggle'lari.

## WebSocket Eventleri

- `vision.status`
- `vision.frame`
- `vision.detections`
- `vision.warning`
- `camera.status`

Mevcut sistem eventleri korunur; vision eventleri motor/fire komutu uretmez.

## Bilinen Eksikler

- Gercek OpenCV webcam capture opsiyonel entegrasyon noktasi olarak duruyor; aktif real webcam pipeline yok.
- Ultralytics YOLO inference arayuzu hazir, fakat model yukleme/inference bu fazda opsiyonel ve uygulanmadi.
- Mock MJPEG frame sade placeholder JPEG'dir; asil deger overlay ve metadata pipeline dogrulamasidir.
- Frontend unit test eklenmedi; typecheck/build ve manuel smoke yapildi.
- `reports/007_phase5_vision_pipeline.md` commit sonrasinda olusturuldu; bu rapor henuz commitlenmedi.

## Riskler

- Vision output advisory only kalmalidir; Faz 6 decision engine gelene kadar motor/fire baglantisi kurulmamalidir.
- Model path warning'leri sistem hazirlik kararinda ileride safety gate'e baglanmalidir.
- Real webcam eklenirken OpenCV hatalari kontrollu ele alinmali ve backend cokmemelidir.
- MJPEG stream WebSocket'ten ayridir; deployment sirasinda CORS/proxy ayarlari buna gore yapilmalidir.

## Bir Sonraki Onerilen Task

Faz 6 - Decision Engine ve Safety:

- Safety gates karar modeli.
- Range/team/balloon/stability/zone gate'leri.
- Arm/disarm endpoint mantiginin genisletilmesi.
- Fire request validation reject-by-default.
- Decision reason ve blocking reasons'in UI paneline baglanmasi.

Kullanici `devam` demeden Faz 6'ya gecilmeyecek.
