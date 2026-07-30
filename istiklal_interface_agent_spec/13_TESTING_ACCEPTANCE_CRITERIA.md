# 13. Test ve Kabul Kriterleri

## Test Seviyeleri

- Unit tests
- Integration tests
- Hardware-in-the-loop tests
- UI tests
- Replay tests
- Field tests
- Safety tests

## P0 Kabul Kriterleri

### Backend

- FastAPI server çalışır.
- WebSocket telemetry yayınlar.
- Kamera mock/gerçek modda çalışır.
- Model yüklenir veya mock detection çalışır.
- Pico serial mock çalışır.
- Config validation çalışır.
- Loglar JSONL olarak yazılır.

### Frontend

- Dashboard açılır.
- WebSocket state canlı güncellenir.
- Kamera overlay görünür.
- Pico pinout görünür.
- Pin ataması yapılır.
- Hatalı pin ataması kırmızı görünür.
- Safety gates paneli çalışır.

### Pico/Serial

- Mock Pico telemetry alınıp UI'da gösterilir.
- Heartbeat timeout fault üretir.
- CRC error loglanır.
- DISARM komutu gönderilebilir.
- E-stop aktifken fire request reddedilir.

### Vision

- Body detection UI'da gösterilir.
- Balloon detection UI'da gösterilir.
- Track ID gösterilir.
- Decision reason gösterilir.
- Replay video üzerinde inference çalışır.

## Safety Acceptance

Fire request reddedilmeli:

```text
system disarmed
e-stop active
target friend
balloon missing
range invalid
track unstable
forbidden zone violation
Pico timeout
```

## Performance Acceptance

Başlangıç hedefleri:

```text
Camera capture: < 20 ms
YOLO inference RTX 4060: < 25 ms
Decision engine: < 5 ms
WebSocket publish: < 10 ms
Serial command: < 20 ms
End-to-end UI telemetry: < 100 ms
```

## Replay Acceptance

- Video yüklenir.
- Timeline çalışır.
- Model inference overlay üretir.
- Hatalı frame işaretlenir.
- Error tags JSONL'e yazılır.
- Dataset export çalışır.

## Config Acceptance

- Geçerli config kaydedilir.
- Geçersiz config reddedilir.
- Pin çakışması yakalanır.
- Model dosyası yoksa hata verir.
- Config değişiklikleri loglanır.

## Definition of Done

Her ana task için:

- Kod çalışıyor.
- Test eklendi.
- UI ekranı veya açıklama var.
- Config/schema güncellendi.
- Dokümantasyon güncellendi.
- Agent raporu yazıldı.
- Kullanıcı onayı bekleniyor.
