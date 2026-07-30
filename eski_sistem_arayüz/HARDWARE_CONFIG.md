# ⚙️ Donanım Konfigürasyonu ve Sabitler

## Pin Bağlantıları (Arduino Uno)

### Step Motor X (Yatay Eksen)
```
STEP_X_PIN = 2      # Step pulse pin
DIR_X_PIN = 3       # Direction pin
ENABLE_X_PIN = 4    # Enable pin (opsiyonel)
```

### Step Motor Y (Dikey Eksen)
```
STEP_Y_PIN = 5      # Step pulse pin
DIR_Y_PIN = 6       # Direction pin
ENABLE_Y_PIN = 7    # Enable pin (opsiyonel)
```

### Lazer Kontrolü
```
LASER_PIN = 8       # Lazer röle/transistör kontrolü
```

### Acil Durdur Butonu
```
EMERGENCY_STOP_PIN = 9  # Pull-up ile bağlı, LOW = basılı
```

### Limit Switch (Opsiyonel)
```
LIMIT_X_MIN_PIN = 10
LIMIT_X_MAX_PIN = 11
LIMIT_Y_MIN_PIN = 12
LIMIT_Y_MAX_PIN = 13
```

---

## Motor Özellikleri

### Step Motor Genel
```python
# config.py içinde tanımlanacak

STEPS_PER_REVOLUTION = 200  # 1.8° step angle (full step)
MICROSTEPPING = 1           # 1 = full step, 2 = half, 4, 8, 16, 32

# Eğer microstepping kullanılıyorsa:
# EFFECTIVE_STEPS = STEPS_PER_REVOLUTION * MICROSTEPPING
```

### X Ekseni (Yatay - Pan)
```python
# Dişli oranı
X_GEAR_RATIO = 10  # 150 diş / 15 diş = 10:1

# Hareket limitleri
X_MIN_ANGLE = -135  # derece
X_MAX_ANGLE = 135   # derece
X_TOTAL_RANGE = 270 # derece

# Adım hesaplama
# 1 derece = (STEPS_PER_REVOLUTION * X_GEAR_RATIO) / 360
# 1 derece = (200 * 10) / 360 = 5.556 adım
X_STEPS_PER_DEGREE = (STEPS_PER_REVOLUTION * X_GEAR_RATIO) / 360

# Toplam adım sayısı
X_TOTAL_STEPS = int(X_TOTAL_RANGE * X_STEPS_PER_DEGREE)  # ~1500 adım

# Hız limitleri (adım/saniye)
X_MAX_SPEED = 1000      # Maksimum hız
X_ACCELERATION = 500    # İvme (adım/saniye²)
```

### Y Ekseni (Dikey - Tilt)
```python
# Dişli oranı
Y_GEAR_RATIO = 2  # 30 diş / 15 diş = 2:1

# Hareket limitleri
Y_MIN_ANGLE = -30   # derece
Y_MAX_ANGLE = 30    # derece
Y_TOTAL_RANGE = 60  # derece

# Adım hesaplama
# 1 derece = (STEPS_PER_REVOLUTION * Y_GEAR_RATIO) / 360
# 1 derece = (200 * 2) / 360 = 1.111 adım
Y_STEPS_PER_DEGREE = (STEPS_PER_REVOLUTION * Y_GEAR_RATIO) / 360

# Toplam adım sayısı
Y_TOTAL_STEPS = int(Y_TOTAL_RANGE * Y_STEPS_PER_DEGREE)  # ~67 adım

# Hız limitleri (adım/saniye)
Y_MAX_SPEED = 500       # Maksimum hız
Y_ACCELERATION = 250    # İvme (adım/saniye²)
```

---

## Kamera Özellikleri

```python
# Kamera ayarları
CAMERA_INDEX = 0            # USB kamera indeksi
FRAME_WIDTH = 640           # Piksel
FRAME_HEIGHT = 480          # Piksel
FPS = 30                    # Hedef FPS

# Frame merkezi (hedef noktası)
FRAME_CENTER_X = FRAME_WIDTH // 2   # 320
FRAME_CENTER_Y = FRAME_HEIGHT // 2  # 240
```

---

## YOLO Model Ayarları

```python
# Model dosyası
YOLO_MODEL_PATH = "models/balon_model.pt"  # Eğitilmiş model

# Tespit parametreleri
YOLO_CONFIDENCE_THRESHOLD = 0.5    # Minimum güven skoru
YOLO_IOU_THRESHOLD = 0.45          # NMS için IoU eşiği

# Sınıf ID'leri (modele göre ayarlanacak)
CLASS_RED_BALLOON = 0      # Kırmızı balon
CLASS_BLUE_BALLOON = 1     # Mavi balon

# Veya tek sınıf varsa renk filtreleme yapılacak
```

---

## PID Parametreleri

```python
# X Ekseni PID
PID_X_KP = 0.5      # Proportional gain
PID_X_KI = 0.01     # Integral gain
PID_X_KD = 0.1      # Derivative gain

# Y Ekseni PID
PID_Y_KP = 0.5      # Proportional gain
PID_Y_KI = 0.01     # Integral gain
PID_Y_KD = 0.1      # Derivative gain

# PID çıktı limitleri
PID_OUTPUT_MIN = -500   # Minimum motor hızı
PID_OUTPUT_MAX = 500    # Maksimum motor hızı

# Dead zone (kilitlenme bölgesi)
DEAD_ZONE_X = 20    # Piksel (bu değerin altında hata varsa "kilitli" say)
DEAD_ZONE_Y = 20    # Piksel
```

---

## Kalman Filter Parametreleri

```python
# Durum vektörü: [x, y, vx, vy] (pozisyon ve hız)
KALMAN_STATE_DIM = 4
KALMAN_MEASURE_DIM = 2

# Süreç gürültüsü (Q matrix)
KALMAN_PROCESS_NOISE = 0.01

# Ölçüm gürültüsü (R matrix)
KALMAN_MEASUREMENT_NOISE = 1.0

# Tahmin süresi
PREDICTION_TIME = 0.1  # 100ms sonrasını tahmin et
```

---

## Güvenlik Parametreleri

```python
# Yasak bölge (ateş edilemez)
FORBIDDEN_ZONE_X_MIN = -15  # derece
FORBIDDEN_ZONE_X_MAX = 15   # derece

# Acil durdur
EMERGENCY_STOP_ENABLED = True

# Lazer güvenlik
LASER_MAX_ON_TIME = 10.0    # Maksimum sürekli açık kalma süresi (saniye)
LASER_COOLDOWN_TIME = 1.0   # İki ateş arası minimum bekleme (saniye)

# Motor koruma
MOTOR_STALL_TIMEOUT = 5.0   # Motor takılma zaman aşımı (saniye)
```

---

## Serial Haberleşme

```python
# Port ayarları
SERIAL_PORT = "COM3"        # Windows için (veya /dev/ttyUSB0 Linux için)
SERIAL_BAUDRATE = 115200    # Baud rate
SERIAL_TIMEOUT = 0.1        # Okuma zaman aşımı (saniye)

# Protokol
SERIAL_TERMINATOR = "\n"    # Satır sonu karakteri
```

---

## GUI Ayarları

```python
# Pencere boyutu
GUI_WIDTH = 1200
GUI_HEIGHT = 700

# Güncelleme hızı
GUI_UPDATE_INTERVAL = 50    # ms (20 FPS)

# Renkler
COLOR_RED_BALLOON = (0, 0, 255)     # BGR - Kırmızı
COLOR_BLUE_BALLOON = (255, 0, 0)    # BGR - Mavi
COLOR_TARGET_LOCKED = (0, 255, 0)   # BGR - Yeşil (kilitli)
COLOR_CROSSHAIR = (255, 255, 255)   # BGR - Beyaz
COLOR_FORBIDDEN = (0, 0, 128)       # BGR - Koyu kırmızı
```

---

## Tam config.py Şablonu

```python
"""
TEKNOFEST Hava Savunma Sistemi - Konfigürasyon Dosyası
Bu dosyayı kendi donanımınıza göre düzenleyin.
"""

# ============== MOTOR AYARLARI ==============
STEPS_PER_REVOLUTION = 200
MICROSTEPPING = 1

# X Ekseni
X_GEAR_RATIO = 10
X_MIN_ANGLE = -135
X_MAX_ANGLE = 135
X_STEPS_PER_DEGREE = (STEPS_PER_REVOLUTION * MICROSTEPPING * X_GEAR_RATIO) / 360
X_MAX_SPEED = 1000
X_ACCELERATION = 500

# Y Ekseni
Y_GEAR_RATIO = 2
Y_MIN_ANGLE = -30
Y_MAX_ANGLE = 30
Y_STEPS_PER_DEGREE = (STEPS_PER_REVOLUTION * MICROSTEPPING * Y_GEAR_RATIO) / 360
Y_MAX_SPEED = 500
Y_ACCELERATION = 250

# ============== KAMERA ==============
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_CENTER_X = FRAME_WIDTH // 2
FRAME_CENTER_Y = FRAME_HEIGHT // 2

# ============== YOLO ==============
YOLO_MODEL_PATH = "models/balon_model.pt"
YOLO_CONFIDENCE = 0.5
CLASS_RED_BALLOON = 0
CLASS_BLUE_BALLOON = 1

# ============== PID ==============
PID_X_KP, PID_X_KI, PID_X_KD = 0.5, 0.01, 0.1
PID_Y_KP, PID_Y_KI, PID_Y_KD = 0.5, 0.01, 0.1
PID_OUTPUT_MIN, PID_OUTPUT_MAX = -500, 500
DEAD_ZONE_X, DEAD_ZONE_Y = 20, 20

# ============== KALMAN ==============
PREDICTION_TIME = 0.1

# ============== GÜVENLİK ==============
FORBIDDEN_ZONE_X_MIN = -15
FORBIDDEN_ZONE_X_MAX = 15
LASER_MAX_ON_TIME = 10.0

# ============== SERIAL ==============
SERIAL_PORT = "COM3"  # Bunu kendi portuna göre değiştir
SERIAL_BAUDRATE = 115200

# ============== ARDUINO PINLERİ ==============
# (Arduino kodunda kullanılacak, referans için)
STEP_X_PIN = 2
DIR_X_PIN = 3
STEP_Y_PIN = 5
DIR_Y_PIN = 6
LASER_PIN = 8
EMERGENCY_STOP_PIN = 9
```
