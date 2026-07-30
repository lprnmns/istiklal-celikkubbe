# Faz 5 Kamera, Vision Pipeline ve Overlay UI

## Camera Service Mimarisi

Backend kamera katmani `CameraService` ile soyutlandi.

Desteklenen modlar:

- `mock`: varsayilan ve guvenli mod.
- `image`: ileride placeholder/image source icin ayrilmis mod.
- `webcam`: opsiyonel real webcam modu; OpenCV zorunlu degildir ve yoksa sistem cokmez.

Varsayilan config:

```yaml
camera:
  camera_mode: "mock"
  camera_source: null
  stream_enabled: true
  stream_width: 640
  stream_height: 360
  stream_fps: 15
```

## Mock / Real Camera Ayrimi

Bu fazda mock camera defaulttur. Real webcam support opsiyonel entegrasyon noktasi olarak durur; kamera yoksa backend ayakta kalir.

Mock camera MJPEG stream icin sabit guvenli JPEG frame uretir. Vision metadata mock pipeline tarafindan uretilir.

## MJPEG Stream Yaklasimi

Ham frame WebSocket uzerinden gonderilmez. Video icin:

```http
GET /api/camera/stream.mjpg
```

Metadata ve detection olaylari WebSocket uzerinden akar.

## Detection Schema

BBox format: pixel.

Body detection:

```json
{
  "id": 1,
  "class_name": "helicopter",
  "class_id": 1,
  "confidence": 0.86,
  "bbox": {"x": 120, "y": 80, "w": 140, "h": 90, "format": "pixel"},
  "source": "mock",
  "color_hint": "enemy_candidate",
  "stable_frames": 5
}
```

Balloon detection:

```json
{
  "id": 1,
  "confidence": 0.91,
  "bbox": {"x": 250, "y": 220, "w": 32, "h": 32, "format": "pixel"},
  "center_x": 266,
  "center_y": 236,
  "source": "mock"
}
```

## Body / Balloon Ayrimi

- Body detector hedef govdesini temsil eder.
- Balloon detector nisan/aim point kaynagi olarak ayri tutulur.
- Aim point bu fazda sadece gorsel telemetry alanidir.
- Track ve aim point alanlari placeholder olarak schema'da vardir.

## YOLO Entegrasyon Noktasi

Config alanlari:

```yaml
vision:
  vision_mode: "mock"
  model_loading_required: false
  body_model_path: null
  balloon_model_path: null
  body_conf_threshold: 0.35
  balloon_conf_threshold: 0.35
```

Model path verilip dosya bulunamazsa controlled warning uretilir. Backend cokmez. Gercek Ultralytics YOLO inference bu fazda zorunlu degildir.

## WebSocket Eventleri

- `vision.status`
- `vision.frame`
- `vision.detections`
- `vision.warning`
- `camera.status`

Ham frame WebSocket'e konmaz.

## Overlay UI Kullanimi

Frontend Vision sayfasi:

- Camera status card.
- Vision pipeline status card.
- MJPEG stream panel.
- SVG overlay.
- Body detection table.
- Balloon detection table.
- FPS/latency panel.
- Latest vision events.
- Start/stop vision butonlari.
- Snapshot butonu.

Overlay layer toggles:

- body boxes
- balloon boxes
- aim points
- labels
- latency

## Safety Notlari

- Vision output advisory only.
- Bu fazda vision eventleri motor/fire komutu uretmez.
- Aim point sadece gorsel/telemetry amaclidir.
- Default sistem davranisi korunur:
  - `DISARMED`
  - `NO_FIRE`
  - `dry_run=true`

## Bilincli Olarak Yapilmayanlar

- Decision engine yok; Faz 6.
- Motor/taret kontrol paneli yok; Faz 7.
- Dataset/replay yok; Faz 9.
- Model egitme yok.
- Gercek hardware komutu yok.
- Vision output motor/fire akisi ile baglanmadi.
