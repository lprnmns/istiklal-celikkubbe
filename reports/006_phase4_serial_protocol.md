# Task Raporu: Faz 4 - Serial Protocol ve Serial Monitor

## Yapilanlar

- Housekeeping olarak Faz 3 raporu commit'e alindi.
- Backend serial protocol/transport katmani olusturuldu:
  - `protocols/serial_json.py`
  - `protocols/serial_binary.py`
  - `protocols/crc16.py`
  - `services/serial_service.py`
  - `mocks/mock_serial_transport.py`
- JSON-line dev protocol encode/decode eklendi.
- Binary packet encode/decode katmani eklendi.
- CRC16/XMODEM implementasyonu ve test vektoru eklendi.
- SerialService icinde seq counter, pending ACK map, ACK/NACK handling, ACK timeout, heartbeat timeout ve status/log state eklendi.
- Riskli mesajlar `/api/serial/send-json` tarafinda reddedildi.
- Serial Monitor backend API'leri eklendi:
  - `GET /api/serial/status`
  - `GET /api/serial/logs`
  - `POST /api/serial/send-json`
  - `POST /api/serial/clear-logs`
  - `POST /api/serial/simulate-rx`
- WebSocket eventleri genisletildi:
  - `serial.tx`
  - `serial.rx`
  - `serial.ack`
  - `serial.nack`
  - `serial.timeout`
  - `serial.error`
  - `serial.status`
- Config'e serial ayarlari eklendi.
- Frontend Serial Monitor ekrani eklendi.
- Serial store ve API client eklendi.
- Faz 4 serial protocol dokumantasyonu eklendi.
- Gercek hardware komutu, motor/taret kontrol paneli veya vision overlay eklenmedi.

## Olusturulan / Degistirilen Dosyalar

| Dosya | Degisiklik |
|---|---|
| `backend/app/protocols/crc16.py` | CRC16/XMODEM implementasyonu eklendi. |
| `backend/app/protocols/serial_json.py` | JSON-line TX/RX schema, encode/decode eklendi. |
| `backend/app/protocols/serial_binary.py` | Binary packet encode/decode ve controlled errors eklendi. |
| `backend/app/mocks/mock_serial_transport.py` | Mock serial transport eklendi. |
| `backend/app/schemas/serial.py` | Serial status/log/request/result schemalari eklendi. |
| `backend/app/services/serial_service.py` | ACK/NACK, timeout, safe send, simulate-rx ve log mantigi eklendi. |
| `backend/app/api/routes_serial.py` | Serial REST endpointleri eklendi. |
| `backend/app/api/routes_ws.py` | Serial WebSocket eventleri eklendi. |
| `backend/app/schemas/config.py` | Serial config validation eklendi. |
| `config/config.yaml` | Serial config defaultlari eklendi. |
| `backend/tests/test_serial_protocols.py` | Protocol/CRC/binary/json tests eklendi. |
| `backend/tests/test_serial_service.py` | Serial API, ACK/NACK, timeout tests eklendi. |
| `frontend/src/types/serial.ts` | Serial frontend tipleri eklendi. |
| `frontend/src/api/serial.ts` | Serial REST client eklendi. |
| `frontend/src/stores/serialStore.ts` | Serial state/log store eklendi. |
| `frontend/src/views/SerialView.vue` | Serial Monitor UI eklendi. |
| `frontend/src/router/index.ts` | Serial route eklendi. |
| `frontend/src/components/layout/AppShell.vue` | Sidebar'a Serial linki eklendi. |
| `docs/serial_protocol_phase4.md` | Faz 4 serial protocol dokumantasyonu eklendi. |
| `reports/006_phase4_serial_protocol.md` | Bu rapor eklendi. |

## Calistirilan Komutlar

```bash
git status --short
git add reports/005_phase3_pico_interface.md
git commit -m "docs: add phase 3 pico interface report"
PATH="$HOME/.local/bin:$PATH" uv run pytest
pnpm typecheck
pnpm build
curl -sS http://127.0.0.1:8000/api/serial/status
curl -sS -X POST http://127.0.0.1:8000/api/serial/send-json -H 'Content-Type: application/json' -d '{"message":{"type":"disarm","seq":31,"reason":"smoke"}}'
curl -sS -I http://127.0.0.1:5173/serial
git add backend config docs/serial_protocol_phase4.md frontend/src
git commit -m "feat: add serial protocol and monitor"
```

## Test / Build Sonuclari

```text
Backend pytest: 38 passed in 1.55s
Frontend pnpm typecheck: passed
Frontend pnpm build: passed
Manual /api/serial/status: passed
Manual /api/serial/send-json safe disarm: passed
Manual /serial frontend route: HTTP 200
```

Build ciktisi:

```text
dist/index.html                  0.45 kB
dist/assets/index-*.css         20.68 kB
dist/assets/index-*.js         133.11 kB
```

## Git Commit Hashleri

```text
d1a31f9 docs: add phase 3 pico interface report
93582a4 feat: add serial protocol and monitor
```

## JSON-line Protokol Ozeti

JSON-line dev protocol newline ile biten JSON mesajlari kullanir.

Safe PC -> Pico mesajlari:

- `heartbeat`
- `disarm`
- `self_test`
- `set_mode`

Pico -> PC mesajlari:

- `ack`
- `nack`
- `telemetry`
- `error`
- `heartbeat`

Riskli TX mesajlari bu fazda reddedilir:

- `fire_request`
- `jog_motor`
- `set_motor_target`
- `set_servo_position`
- `set_servo`

## Binary Protokol Ozeti

Binary packet formati:

```text
START | TYPE | SEQ | LEN | PAYLOAD | CRC16 | END
0xAA  | 1B   | 1B  | 1B  | N byte  | 2B    | 0x55
```

Bu fazda binary protokol yalnizca encode/decode ve test katmanidir; gercek cihaza uygulanmadi.

## CRC / ACK / NACK / Timeout Davranisi

- CRC secimi: CRC16/XMODEM.
- Test vektoru: `"123456789" -> 0x31C3`.
- CRC hesap alani: `TYPE + SEQ + LEN + PAYLOAD`.
- ACK gelirse pending command temizlenir.
- NACK gelirse pending command temizlenir ve `last_error` guncellenir.
- ACK timeout olursa connection state `FAULT` olur, `ACK_TIMEOUT:<seq>` yazilir ve safety fault loglanir.
- Heartbeat timeout olursa connection state `FAULT` olur ve `HEARTBEAT_TIMEOUT` yazilir.

## Serial Monitor Ekraninin Kisa Aciklamasi

- Serial Status: connection state, transport mode, protocol mode, real serial flag ve last error.
- ACK / Heartbeat: pending ack count, ack timeout, heartbeat timeout ve heartbeat age.
- Safety Boundary: riskli mesajlarin disabled oldugunu gosterir.
- Safe Message Sender: allowlisted JSON-line mesajlari mock transport'a yollar.
- Simulate RX: ack/nack/telemetry/heartbeat/error mesajlarini mock olarak sisteme enjekte eder.
- Serial Log: tx/rx/ack/nack/error/timeout/status kayitlarini renkli tabloda gosterir.

## Bilinen Eksikler

- Gercek PySerial transport yok; real serial intentionally disabled.
- Binary protocol gercek cihaza baglanmiyor; sadece testlenebilir codec katmani.
- Frontend icin unit test eklenmedi; typecheck/build ve manuel smoke yapildi.
- Serial log kalici storage'a yazilmiyor; runtime memory + JSONL service loglari var.
- `reports/006_phase4_serial_protocol.md` commit sonrasinda olusturuldu; bu rapor henuz commitlenmedi.

## Riskler

- SerialService mock transport uzerinde olsa da riskli mesaj isimleri schema seviyesinde taniniyor; gercek transport eklenirken allowlist/safety gate korunmali.
- Timeout faultlari simule ediliyor; Pico local watchdog davranisi firmware fazinda ayrica dogrulanmali.
- `DISARM` safe command olarak kabul ediliyor ama bu fazda yalnizca mock transport'a yaziliyor.
- `hardware_enabled=false` ve `real_serial_enabled=false` validation ile korunuyor; ileride gevsetilirse ayrica onay ve test gerekir.

## Bir Sonraki Onerilen Task

Faz 5 - Kamera ve Vision UI:

- CameraService mock/gercek kaynak soyutlamasi.
- Mock frame pipeline.
- YOLO model entegrasyon noktasi.
- Body/balloon target cards.
- Canvas/SVG overlay ilk surumu.
- FPS/latency telemetry.

Kullanici `devam` demeden Faz 5'e gecilmeyecek.
