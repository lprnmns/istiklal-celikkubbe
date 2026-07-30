# 4. UI/UX Spesifikasyonu

## Tasarım İlkeleri

- Koyu tema, yüksek kontrast.
- Kritik durumlar: yeşil/hazır, sarı/bekle, kırmızı/hata.
- Operatör ekranı sade, engineer ekranı detaylı olmalı.
- Her kritik kararın nedeni görünmeli.
- Riskli butonlar güvenlik koşulu ve onay gerektirmeli.

## Sidebar Sayfaları

1. Dashboard
2. Görev Modları
3. Görüntü İşleme
4. Hedef Takip & Karar
5. Pico 2 Pinout
6. Motor & Taret
7. Atış Güvenliği
8. Kamera Kalibrasyon
9. Renk/Dost-Düşman
10. Veri Toplama
11. Replay
12. Model Registry
13. Loglar
14. Konfigürasyon
15. Self-Test

## Dashboard Layout

```text
┌───────────────────────────────────────────────┬────────────────────┐
│ Canlı Kamera + Overlay                         │ Sistem Durumu       │
│                                                │ mode/arm/estop      │
├───────────────────────────────────────────────┼────────────────────┤
│ Hedef Tablosu                                  │ Karar Kapıları      │
└───────────────────────────────────────────────┴────────────────────┘
```

## Ana Widgetlar

- SystemStateCard
- CameraFeedPanel
- TargetListTable
- DecisionGatePanel
- PicoStatusCard
- SafetyStatusCard
- LatencyMiniChart
- MissionModeControl

## Pico 2 Pinout Ekranı

Her pin gösterir:

- GP adı
- fiziksel pin
- görev
- canlı değer
- hata/uyarı
- son update zamanı

Renkler:

- gri: unused
- yeşil: input
- mavi: output
- turuncu: PWM
- mor: UART/SPI/I2C
- kırmızı: conflict/error
- sarı: warning

## Görüntü İşleme Ekranı

Layer toggles:

- Raw camera
- Body bbox
- Balloon bbox
- Aim point
- Track trail
- HSV mask
- ROI
- Safe zone
- Latency

## Atış Güvenliği Ekranı

Fire gates checklist:

- Emergency stop released
- System armed
- Pico heartbeat
- Track stable
- Target enemy
- Balloon detected
- Range valid
- Aim point valid
- No forbidden zone
- Pico ack

## Veri Toplama Ekranı

Metadata alanları:

- scenario
- target type
- team
- distance
- angle
- lighting
- camera/lens
- operator
- notes

Butonlar:

- Start recording
- Capture frame
- Capture hard negative
- Export YOLO dataset
- Open dataset folder

## Replay Ekranı

- Video yükle
- Model seç
- Inference çalıştır
- Timeline
- Hata etiketle
- Dataset'e ekle

## Log Ekranı

Filtreler:

- time range
- level
- subsystem
- track_id
- decision
- error code

Örnek:

```text
14:32:10.221 [DECISION] track=8 NO_FIRE reason="target_friend"
```

## Self-Test Wizard

Adımlar:

1. Kamera
2. Model
3. Pico
4. E-stop
5. Pan motor
6. Tilt motor
7. Servo dry-run
8. Log
9. Ready report
