# 2. Özellik Kataloğu

## Öncelik seviyeleri

- **P0:** İlk çalışan sürümde zorunlu.
- **P1:** Profesyonel seviye için gerekli.
- **P2:** Zaman kalırsa eklenecek ileri özellik.

---

# P0 Özellikler

## Dashboard

- Canlı kamera görüntüsü
- YOLO body bbox overlay
- Balon bbox overlay
- Track ID
- Hedef sınıfı
- Dost/düşman kararı
- Tahmini menzil
- Karar durumu
- Pico 2 bağlantı durumu
- Acil stop durumu
- Arm/disarm durumu
- FPS/gecikme
- Son hata

## Görev Modları

- `DISARMED`
- `MANUAL_STAGE_1`
- `AUTONOMOUS_STAGE_2`
- `FRIEND_ENEMY_STAGE_3`
- `CALIBRATION`
- `SELF_TEST`
- `REPLAY`

## Görüntü Overlay Katmanları

- Raw camera
- Body bbox
- Balloon bbox
- Aim point
- Track trail
- HSV mask
- ROI
- Safe/no-fire zone
- Crosshair
- FPS/latency

## Pico 2 Bağlantı

- Port listesi
- Baudrate seçimi
- Connect/disconnect
- Heartbeat
- Telemetry
- CRC/hata sayacı
- Son paket zamanı

## Pico 2 Pinout

- İnteraktif kart görseli
- Pine tıklayıp görev atama
- Pin conflict kontrolü
- PWM/UART/GPIO uygunluk kontrolü
- Canlı pin state
- Config kaydet/yükle

## Motor/Taret Paneli

- Pan +1° / -1°
- Tilt +1° / -1°
- Go Home
- Stop Motion
- Driver enable/disable
- Max speed
- Acceleration
- Step/degree
- Deadband
- Backlash compensation

## Güvenlik Paneli

- `NO_FIRE` default
- Arm/disarm
- Fire gates
- Emergency stop
- Yasak alan
- Track stable
- Enemy confirmed
- Balloon detected
- Range valid
- Pico acknowledged

## Serial Monitor

- Giden paketler
- Gelen paketler
- Decode edilmiş mesajlar
- CRC hata sayısı
- ACK/NACK
- Timeout
- Raw hex view

## Log Sistemi

- Vision log
- Decision log
- Pico serial log
- Operator action log
- Safety log
- Export JSONL/CSV

---

# P1 Özellikler

## Kamera/Lens Kalibrasyonu

- Kamera seçimi
- Çözünürlük/FPS
- Exposure lock
- White balance lock
- Lens profili: 3.6 / 8 / 12 mm
- Kamera yüksekliği
- Hedef yüksekliği
- Homography kalibrasyonu
- 5/10/15 m referans çizgileri

## HSV/LAB Dost-Düşman Ayarı

- Enemy renk eşiği
- Friend renk eşiği
- Balon maskesi
- Gövde crop alanı
- Mask preview
- Renk oranı
- Unknown threshold
- Temporal smoothing

## Veri Toplama

- Video kaydı
- Frame capture
- Scenario metadata
- Hard negative capture
- YOLO dataset export
- CVAT/LabelImg uyumlu klasör

## Replay

- Video yükle
- Model seç
- Frame frame inference
- Hatalı frame işaretleme
- False positive/false negative tagging
- Yeni dataset'e ekleme

## Model Registry

- Aktif body model
- Aktif balloon model
- Model metrikleri
- Known failures
- Rollback
- Model compare

## Self-Test Wizard

- Kamera testi
- Model testi
- Pico bağlantı testi
- E-stop testi
- Pan/tilt dry-run
- Servo dry-run
- Log sistemi testi
- Sistem hazır raporu

---

# P2 Özellikler

## Çoklu Kamera

- 3.6 mm geniş görüş
- 8/12 mm kilit kamerası
- Kamera transform kalibrasyonu
- Geniş kameradan dar kameraya hedef aktarımı

## Parkur Dijital İkiz

- 10 m × 16 m parkur
- Sistem POV konisi
- 5/10/15 m çizgileri
- Hedef track pozisyonları
- Yasak alanlar

## Zone Editor

- No-fire zone
- No-motion zone
- ROI zone
- Bariyer bölgeleri
- Export/import

## Latency Profiler

- Capture latency
- Inference latency
- Tracking latency
- Decision latency
- Serial latency
- Pico ack latency
- End-to-end loop

## Role-Based UI

- Operator mode
- Engineer mode
- Admin mode
- Demo mode

## Read-only LLM Assistant

Opsiyonel. Karar döngüsüne girmemeli.

- Log açıklama
- “Neden ateş izni yok?” özetleme
- Demo sırasında durum anlatımı
