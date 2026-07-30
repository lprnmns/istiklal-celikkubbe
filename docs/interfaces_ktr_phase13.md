# Interfaces KTR Phase 13

## KTR 4.3 Arayüzler Yaklaşımı

Phase 13 ile arayüz envanteri backend tarafından üretilen, UI’da incelenebilen ve KTR export paketine eklenen tek kaynak haline getirildi. `/interfaces` ekranı ve `/api/interfaces/*` endpointleri KTR 4.3 metnini otomatik üretir.

## UI Arayüzleri

- Dashboard
- Safety
- Self-Test
- First Run
- Devices
- Pico
- Serial
- Vision
- Data Lab
- Reports
- Interfaces
- Logs

UI, fiziksel komut yetkisi vermez. Operatör aksiyonları backend safety gate ve config validation katmanından geçer.

## Yazılım Arayüzleri

- Frontend ↔ Backend REST: `/api/*`, JSON, Pydantic schema validation
- Backend → Frontend WebSocket: `/ws`, event envelope
- Camera stream: `/api/camera/stream.mjpg`
- Model registry/runtime: `/api/models/*`, `/api/vision/runtime/*`
- Dataset/replay: `/api/sessions`, `/api/datasets`, `/api/replay`
- Report export: `/api/reports/*`
- First-run: `/api/first-run/*`
- Interface inventory: `/api/interfaces/*`

## Donanım Arayüzleri

- Pico 2 read-only telemetry over USB serial
- Serial JSON-line telemetry parser
- Binary protocol codec as tested foundation
- Future electronic power/signal interface placeholder for STEP/DIR/UART/PWM/E-stop/limits

Bu fazda GPIO, STEP/DIR, PWM, servo, trigger veya fire output yoktur.

## Mesaj Protokolleri

- REST JSON: operator action and service state
- WebSocket JSON envelope: `type`, `ts`, `seq`, `payload`
- MJPEG: browser stream display
- JSON-line serial telemetry: Pico read-only state
- Binary packet codec: future protocol foundation, not active on physical hardware
- JSONL files: logs, detections, annotations and client event exports

## Güvenlik Sınırları

- Backend is the safety authority.
- UI does not authorize physical action.
- Reports, first-run and self-test do not enable fire/motion.
- Hardware discovery is read-only.
- Config validation rejects physical command flags.
- Default startup is DISARMED and NO_FIRE.

## Kullanılan Teknolojiler

- Python 3.12+
- FastAPI
- Pydantic
- WebSocket
- Vue 3
- Vite
- TypeScript
- Pinia
- TailwindCSS
- OpenCV integration points
- PySerial read-only discovery
- YAML config
- JSONL logging

## Jüriye Anlatım Metni

İSTİKLAL C2 Console, kullanıcı arayüzü, REST/WebSocket yazılım arayüzleri, kamera/MJPEG görüntü aktarımı, vision model adapter sözleşmesi, Pico read-only telemetry, serial protocol codec, safety gate modeli, dataset/replay dosya arayüzleri ve KTR/report export akışlarını tek bir doğrulanabilir interface inventory içinde toplar. Tüm bu arayüzler safety boundary ve failure behavior alanlarıyla belgelenir. Bu fazda hiçbir fiziksel motor, servo, tetik veya atış çıkışı üretilmez.
