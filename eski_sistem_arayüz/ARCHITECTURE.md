# 🏗️ Sistem Mimarisi

## Genel Mimari

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PYTHON (PC)                                  │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐             │
│  │  GUI    │   │  YOLO   │   │ KALMAN  │   │   PID   │             │
│  │(Tkinter)│   │Detector │   │ Filter  │   │Controller│            │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘             │
│       │             │             │             │                   │
│       └─────────────┴──────┬──────┴─────────────┘                   │
│                            │                                        │
│                    ┌───────┴───────┐                                │
│                    │  MAIN LOOP    │                                │
│                    │ (Non-blocking)│                                │
│                    └───────┬───────┘                                │
│                            │                                        │
│                    ┌───────┴───────┐                                │
│                    │ Serial Comm   │                                │
│                    │  (PySerial)   │                                │
│                    └───────┬───────┘                                │
└────────────────────────────┼────────────────────────────────────────┘
                             │ USB Serial (115200 baud)
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                    ┌───────┴───────┐                                │
│                    │  Arduino Uno  │            ARDUINO             │
│                    │    Parser     │                                │
│                    └───────┬───────┘                                │
│           ┌────────────────┼────────────────┐                       │
│    ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐               │
│    │ AccelStepper│  │ AccelStepper│  │   Laser     │               │
│    │  Motor X    │  │  Motor Y    │  │  Control    │               │
│    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
└───────────┼────────────────┼────────────────┼───────────────────────┘
            │                │                │
      ┌─────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
      │ Step Motor│    │ Step Motor│    │   Lazer   │
      │  X Ekseni │    │  Y Ekseni │    │  Modülü   │
      └───────────┘    └───────────┘    └───────────┘
```

---

## Veri Akış Diyagramı

```
┌──────────────┐
│   KAMERA     │
│  (Webcam)    │
└──────┬───────┘
       │ Frame (640x480)
       ▼
┌──────────────┐
│    YOLO      │
│  Detector    │
└──────┬───────┘
       │ [(class_id, x, y, w, h, confidence), ...]
       ▼
┌──────────────┐
│   TARGET     │
│  SELECTOR    │  → Sadece kırmızı balonları filtrele
└──────┬───────┘    En büyük/yakın olanı seç
       │ (target_x, target_y)
       ▼
┌──────────────┐
│   KALMAN     │
│   FILTER     │  → Gelecek pozisyonu tahmin et
└──────┬───────┘
       │ (predicted_x, predicted_y)
       ▼
┌──────────────┐
│     PID      │
│ CONTROLLER   │  → Hata hesapla, motor hızı belirle
└──────┬───────┘
       │ (speed_x, speed_y)
       ▼
┌──────────────┐
│   SERIAL     │
│    COMM      │  → Arduino'ya gönder
└──────┬───────┘
       │ "SPD,{speed_x},{speed_y}\n"
       ▼
┌──────────────┐
│   ARDUINO    │
│   MOTORS     │  → Step motorları çalıştır
└──────────────┘
```

---

## Kontrol Döngüsü (Main Loop)

```python
# PSEUDO CODE - Ana döngü yapısı

while running:
    # 1. FRAME AL (non-blocking)
    frame = camera.read()
    
    # 2. YOLO TESPİT
    detections = yolo.detect(frame)
    
    # 3. HEDEF SEÇ (sadece kırmızı)
    red_balloons = filter_red_balloons(detections)
    target = select_target(red_balloons)  # En büyük veya en yakın
    
    # 4. KALMAN TAHMİN
    if target:
        predicted_pos = kalman.predict(target.center)
    else:
        predicted_pos = None
    
    # 5. PID HESAPLA
    if predicted_pos:
        error_x = FRAME_CENTER_X - predicted_pos.x
        error_y = FRAME_CENTER_Y - predicted_pos.y
        speed_x = pid_x.compute(error_x)
        speed_y = pid_y.compute(error_y)
    else:
        speed_x, speed_y = 0, 0
    
    # 6. GÜVENLİK KONTROL
    if emergency_stop_pressed:
        speed_x, speed_y = 0, 0
        laser_off()
        continue
    
    # 7. ARDUINO'YA GÖNDER
    serial.send(f"SPD,{speed_x},{speed_y}")
    
    # 8. ATEŞ KONTROLÜ
    if target and is_locked(error_x, error_y) and can_fire():
        laser_on()
    else:
        laser_off()
    
    # 9. GUI GÜNCELLE
    gui.update(frame, target, current_angle, mode)
```

---

## Serial Protokol

### Python → Arduino Komutları

| Komut | Format | Açıklama |
|-------|--------|----------|
| Hız Ayarla | `SPD,{x},{y}\n` | X ve Y motor hızları (-1000 ile +1000) |
| Pozisyona Git | `POS,{x},{y}\n` | X ve Y hedef pozisyonlar (adım) |
| Lazer Aç | `LZR,1\n` | Lazeri aç |
| Lazer Kapat | `LZR,0\n` | Lazeri kapat |
| Acil Durdur | `STP\n` | Tüm motorları durdur |
| Home Git | `HOM\n` | Başlangıç pozisyonuna git |
| Durum Sor | `STS\n` | Mevcut durumu sor |

### Arduino → Python Yanıtları

| Yanıt | Format | Açıklama |
|-------|--------|----------|
| Pozisyon | `POS,{x},{y}\n` | Mevcut pozisyon (adım) |
| Durum | `STS,{state}\n` | READY, MOVING, STOPPED, ERROR |
| OK | `OK\n` | Komut alındı |
| Error | `ERR,{code}\n` | Hata kodu |

---

## Durum Makinesi (State Machine)

```
                    ┌─────────────┐
                    │    INIT     │
                    └──────┬──────┘
                           │ Başlatma tamamlandı
                           ▼
                    ┌─────────────┐
        ┌──────────►│    IDLE     │◄──────────┐
        │           └──────┬──────┘           │
        │                  │                  │
        │    ┌─────────────┼─────────────┐    │
        │    │             │             │    │
        │    ▼             ▼             ▼    │
   ┌────┴────┐      ┌─────────┐     ┌────────┐
   │ MANUAL  │      │  AUTO   │     │AUTONOMS│
   │  MODE   │      │  MODE   │     │  MODE  │
   └────┬────┘      └────┬────┘     └────┬───┘
        │                │               │
        │    ┌───────────┴───────────┐   │
        │    ▼                       │   │
        │ ┌─────────┐               │   │
        │ │SEARCHING│               │   │
        │ └────┬────┘               │   │
        │      │ Hedef bulundu      │   │
        │      ▼                    │   │
        │ ┌─────────┐               │   │
        │ │TRACKING │               │   │
        │ └────┬────┘               │   │
        │      │ Kilitlendi         │   │
        │      ▼                    │   │
        │ ┌─────────┐               │   │
        │ │ FIRING  │───────────────┘   │
        │ └────┬────┘                   │
        │      │ Patladı               │
        │      └───────────────────────┘
        │
        │     EMERGENCY STOP (Her durumdan)
        │              │
        │              ▼
        │      ┌─────────────┐
        └──────│ EMERGENCY   │
               │   STOP      │
               └─────────────┘
```

---

## Sınıf Diyagramı

```
┌─────────────────────────────────────────────────────────────────┐
│                        MainApplication                           │
├─────────────────────────────────────────────────────────────────┤
│ - camera: cv2.VideoCapture                                       │
│ - detector: YOLODetector                                         │
│ - kalman: KalmanFilter                                           │
│ - pid_x: PIDController                                           │
│ - pid_y: PIDController                                           │
│ - serial: SerialComm                                             │
│ - safety: SafetyManager                                          │
│ - gui: GUI                                                       │
│ - state: SystemState                                             │
├─────────────────────────────────────────────────────────────────┤
│ + run()                                                          │
│ + process_frame()                                                │
│ + update_motors()                                                │
│ + handle_input()                                                 │
│ + emergency_stop()                                               │
└─────────────────────────────────────────────────────────────────┘
         │
         │ uses
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  YOLODetector   │  │  KalmanFilter   │  │ PIDController   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ - model: YOLO   │  │ - state         │  │ - Kp, Ki, Kd    │
│ - conf_thresh   │  │ - covariance    │  │ - integral      │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + detect()      │  │ + predict()     │  │ + compute()     │
│ + filter_red()  │  │ + update()      │  │ + reset()       │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   SerialComm    │  │  SafetyManager  │  │      GUI        │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ - port          │  │ - forbidden_zone│  │ - root (Tk)     │
│ - baudrate      │  │ - limits        │  │ - canvas        │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + send()        │  │ + can_fire()    │  │ + update()      │
│ + receive()     │  │ + check_limits()│  │ + draw_target() │
│ + connect()     │  │ + e_stop()      │  │ + show_status() │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Zamanlama Gereksinimleri

| İşlem | Hedef Süre | Kritiklik |
|-------|------------|-----------|
| Frame alma | < 33ms (30 FPS) | Yüksek |
| YOLO tespit | < 100ms | Yüksek |
| Kalman hesaplama | < 1ms | Düşük |
| PID hesaplama | < 1ms | Düşük |
| Serial gönderim | < 5ms | Orta |
| GUI güncelleme | < 16ms | Orta |
| **Toplam döngü** | **< 150ms (~7 FPS)** | Kritik |

---

## Hata Yönetimi

```python
class SystemError(Enum):
    CAMERA_NOT_FOUND = 1
    SERIAL_CONNECTION_FAILED = 2
    MOTOR_NOT_RESPONDING = 3
    YOLO_MODEL_NOT_FOUND = 4
    EMERGENCY_STOP_ACTIVATED = 5
    LIMIT_REACHED = 6
    FORBIDDEN_ZONE = 7
```

Her hata için:
1. Log'a yaz
2. GUI'de göster
3. Güvenli duruma geç (motorları durdur)
4. Gerekirse acil durdur aktif et
