# 17. Backlog ve Fazlar

Agent nihai planı kendisi çıkaracak; bu belge referans backlogtur.

## Faz 0 — Repo Analizi

Kod yazılmaz.

Çıktılar:

- Repo analiz raporu
- Mimari öneri
- Faz planı
- Risk listesi
- İlk task önerisi

## Faz 1 — Backend Skeleton

- FastAPI app
- Health endpoint
- WebSocket endpoint
- Event bus
- Config loader
- JSONL logger
- Mock Pico
- Mock camera
- Unit test altyapısı

## Faz 2 — Frontend Skeleton

- Vue 3 + TypeScript + Pinia
- Layout/sidebar
- Dashboard
- WebSocket client
- System state store
- Basic telemetry cards

## Faz 3 — Pico 2 Arayüzü

- Pico port listesi
- Connect/disconnect
- Telemetry
- Interaktif Pico pinout
- Pin assignment
- Pin validation

## Faz 4 — Serial Protocol

- JSON-line dev protocol
- Binary protocol temel sınıfları
- Packet encode/decode
- CRC16
- ACK/NACK
- Timeout
- Serial monitor

## Faz 5 — Kamera ve Vision UI

- Kamera başlat/durdur
- Frame stream
- YOLO overlay mock
- Real model integration
- Body/balloon target cards
- FPS/latency

## Faz 6 — Decision Engine ve Safety

- Safety gates
- NO_FIRE default
- Arm/disarm
- Fire request validation
- Decision reason
- UI gate panel

## Faz 7 — Motor/Taret Kontrol Paneli

- Jog command
- Home command
- Stop motion
- Motor settings
- Dry-run mode

## Faz 8 — Kamera Kalibrasyon ve Renk Ayarları

- Lens profile
- Exposure/white balance settings
- Homography points
- HSV/LAB sliders
- Mask preview

## Faz 9 — Dataset ve Replay

- Video recording
- Frame capture
- Scenario metadata
- Replay video
- Error tagging
- Dataset export

## Faz 10 — Self-Test Wizard

- Kamera testi
- Model testi
- Pico testi
- E-stop testi
- Motor dry-run
- Servo dry-run
- Log testi

## Faz 11 — Polish ve KTR Export

- Screenshot/report export
- Latency dashboard
- Demo mode
- Role-based settings
