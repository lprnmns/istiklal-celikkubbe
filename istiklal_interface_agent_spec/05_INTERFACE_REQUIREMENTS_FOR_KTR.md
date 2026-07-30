# 5. KTR 4.3 Arayüzler Bölümü İçin İçerik

## Arayüz Tanımı

Sistem arayüzleri yalnızca kullanıcı arayüzü ile sınırlı değildir. Sistem; kamera, görüntü işleme yazılımı, karar motoru, Pico 2, motor sürücüleri, servo tetik mekanizması, acil stop hattı, güç dağıtımı ve web komuta ekranı arasında tanımlı elektronik ve yazılımsal arayüzlere sahiptir.

## Kullanıcı Arayüzü

FastAPI backend ve Vue/TypeScript frontend tabanlı web komuta kontrol merkezi.

Arayüz üzerinden:

- Görev modu seçilir.
- Kamera görüntüsü canlı izlenir.
- Hedef tespit/takip çıktıları görüntülenir.
- Dost/düşman kararı izlenir.
- Atış güvenlik kapıları kontrol edilir.
- Pico 2 pin ve telemetry durumu doğrulanır.
- Motor/servo testleri güvenli modda yapılır.
- Loglar dışa aktarılır.

## Yazılımsal Arayüzler

| Arayüz | Taraflar | Protokol | Veri | Amaç |
|---|---|---|---|---|
| UI REST | Vue ↔ FastAPI | HTTP/JSON | config, commands | Ayar/komut |
| UI Realtime | Vue ↔ FastAPI | WebSocket/JSON | telemetry, detection | Canlı veri |
| Vision Event | Vision ↔ Decision | Python event/queue | detection object | Hedef kararı |
| Tracker Event | Tracker ↔ Decision | Python object | track state | Hedef sürekliliği |
| Config | Backend ↔ YAML | file I/O + schema | config.yaml | Ayar yönetimi |
| Logging | Backend ↔ files | JSONL/CSV | event records | İzlenebilirlik |
| Replay | Video ↔ Vision | OpenCV frame stream | frame/timestamp | Test/analiz |

## Elektronik Arayüzler

| Arayüz | Taraflar | Sinyal/Gerilim | Açıklama |
|---|---|---|---|
| Güç 12 VDC | AC/DC ↔ sistem | 12 VDC | Ana besleme |
| Güç 24 VDC | Güç ↔ motor sürücü | 24 VDC | Step motor |
| Güç 5 VDC | Buck ↔ servo/Pico | 5 VDC | Yardımcı güç |
| USB kamera | Kamera ↔ laptop | USB/UVC | Video |
| USB serial | Laptop ↔ Pico 2 | USB CDC/UART | Komut/telemetry |
| STEP/DIR | Pico ↔ TMC2209 | GPIO | Motor kontrol |
| UART sürücü | Pico ↔ TMC2209 | UART | Sürücü config |
| PWM servo | Pico ↔ MG995 | PWM | Tetik servo |
| E-stop | Buton ↔ güç/Pico | NC/NO + dijital | Güvenlik |
| Limit input | Switch ↔ Pico | dijital | Eksen sınırı |

## Pico 2 Mesaj Arayüzü

Final için önerilen paket:

```text
START | TYPE | SEQ | LEN | PAYLOAD | CRC16 | END
0xAA  | 1B   | 1B  | 1B  | N byte  | 2B    | 0x55
```

Mesaj türleri:

- HEARTBEAT
- SET_MODE
- SET_MOTOR_TARGET
- SET_SERVO_POSITION
- FIRE_REQUEST
- DISARM
- CONFIG_UPDATE
- SELF_TEST
- TELEMETRY
- ERROR

## Güvenlik Arayüzü

Ateşleme varsayılan olarak kapalıdır. Fire request yalnızca şu koşullarda geçer:

- E-stop serbest
- Sistem armed
- Pico heartbeat aktif
- Track stabil
- Hedef düşman
- Mesafe uygun
- Balon/nişan noktası algılandı
- Yasak alan ihlali yok
- Pico ack alınabilir

## Arayüz Doğrulama

- Pico 2 pin çakışması
- PWM/UART/GPIO uygunluğu
- Kamera bağlantısı
- Model dosyası
- Serial heartbeat
- Motor küçük hareket testi
- Servo dry-run
- E-stop
- Log sistemi
- Görev modu simülasyonu
