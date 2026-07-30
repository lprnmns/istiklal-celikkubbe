# 3. Sistem Mimarisi

## Genel Mimari

```text
[USB Camera(s)]
      ↓
[Vision Service - Python/OpenCV/YOLO]
      ↓
[Tracking Service - ByteTrack/BoT-SORT]
      ↓
[Decision Engine]
      ↓
[Serial Service - PySerial]
      ↓
[Raspberry Pi Pico 2]
      ↓
[TMC2209 + Step Motors + Servo + E-stop IO]

[Vue Frontend]
      ↕ REST/WebSocket
[FastAPI Backend]
```

## Frontend

Önerilen teknoloji:

- Vue 3
- TypeScript
- Pinia
- TailwindCSS
- SVG/Canvas overlay
- WebSocket client

Görevleri:

- Kullanıcı komutları
- Canlı görüntü overlay
- Telemetry
- Ayar yönetimi
- Pico 2 pinout
- Safety gates
- Replay/dataset yönetimi

## Backend

Önerilen teknoloji:

- Python 3.12+
- FastAPI
- WebSocket
- Pydantic
- OpenCV
- Ultralytics YOLO
- PySerial
- SQLite/JSONL
- YAML config

Görevleri:

- Kamera capture
- Model inference
- Tracking
- Karar motoru
- Pico serial protokolü
- Config validation
- Loglama
- Replay

## Pico 2 Firmware

Görevleri:

- STEP/DIR üretimi
- Servo PWM
- Emergency stop input
- Limit switch input
- Driver enable
- Watchdog
- Serial packet parse
- Local safe-state

## Backend Servisleri

### CameraService

- Kamera aç/kapat
- Çözünürlük/FPS
- Exposure/white balance
- Frame timestamp

### VisionService

- Body YOLO
- Balloon YOLO/HSV
- HSV/LAB color classifier
- ROI
- SAHI/15 m mode
- Frame metrics

### TrackingService

- Track ID
- Stable frames
- Lost/reacquire
- ID switch

### DecisionEngine

- Safety gates
- Range rules
- Class/team/balloon validation
- Decision reason

### SerialService

- Pico connect/disconnect
- Packet encode/decode
- CRC16
- Heartbeat
- Telemetry

### ConfigService

- YAML read/write
- Schema validation
- Versioning
- Risky change guard

### LogService

- JSONL logs
- Timeline events
- Export

### ReplayService

- Video replay
- Frame stepping
- Error tagging
- Model compare

## Veri Akışı

### Canlı mod

```text
Camera frame
  → VisionService
  → TrackingService
  → DecisionEngine
  → WebSocket telemetry
  → SerialService command
  → Pico ack
  → UI state update
```

### Replay mod

```text
Recorded video
  → VisionService
  → TrackingService
  → DecisionEngine dry-run
  → UI overlay
  → error tagging
  → dataset export
```

## Güvenlik İlkeleri

- Backend `NO_FIRE` default ile başlar.
- Pico kendi local safe-state mantığını korur.
- UI tek başına ateş/motor güvenliğini sağlayamaz.
- Heartbeat kaybolursa Pico driver disable yapar.
- Emergency stop donanım önceliklidir.
