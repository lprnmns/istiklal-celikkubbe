# 📚 Referans Repo: laser_guided_object_tracker

## Repo Konumu
```
C:\Users\manas\Desktop\HavaSavunma-Teknofest-main\laser_guided_object_tracker
```

## Ne İçin Kullanılacak?

Bu repo aşağıdaki konularda referans olarak kullanılacak:

### 1. Kalman Filter Implementasyonu ✅ KULLAN
Repo'daki Kalman filter kodu adapte edilecek.

**Dosya:** `laser_guidance_ot.py` içindeki Kalman kısmı

**Önemli Noktalar:**
- 2 boyutlu (x, y) Kalman filter
- Constant velocity model kullanıyor
- Predict ve correct fonksiyonları var

**Adapte Edilecek:**
```python
# Repo'dan alınacak Kalman yapısı:
# - State vector: [x, y, vx, vy]
# - Measurement: [x, y]
# - Prediction için dt parametresi
```

### 2. Serial Protokol ✅ REFERANS AL
Repo'nun Arduino ile haberleşme protokolü referans alınacak.

**Repo'daki Komutlar:**
```
m0mtp,val - stepper 0 move to position plus
m0mtm,val - stepper 0 move to position minus
m1mtp,val - stepper 1 move plus
m1mtn,val - stepper 1 move minus
m0p,val   - stepper 0, current position plus n steps
m0m,val   - stepper 0, current position minus n steps
m1p,val   - stepper 1, current position plus n steps
m1m,val   - stepper 1, current position minus n steps
ls,val    - list commands
sh,[0,1]  - set home position
gh,[0,1]  - go home
```

**Bizim Protokol (Daha Basit):**
```
SPD,x,y   - Hız ayarla
POS,x,y   - Pozisyona git
LZR,0/1   - Lazer
STP       - Durdur
HOM       - Home
STS       - Durum
```

### 3. Step Motor Kontrol Mantığı ✅ REFERANS AL
Repo 28BYJ-48 step motor kullanıyor, mantık benzer.

**Repo'dan Alınacak:**
- CheapStepper kütüphanesi kullanımı
- Serial üzerinden step komutu gönderme
- Non-blocking hareket

**Bizim Değişiklik:**
- AccelStepper kütüphanesi kullanacağız (daha gelişmiş)
- Hız tabanlı kontrol (pozisyon değil)

### 4. HSV Renk Tespiti ❌ KULLANMA
Repo HSV renk tespiti kullanıyor, biz YOLO kullanacağız.

**Repo'daki Yaklaşım:**
```python
#Ball color code
OBJ_2_COLOR_CODE=[10,108,136,62,142,255]
# HSV -> mask -> contour detection
```

**Bizim Yaklaşım:**
```python
# YOLO model ile tespit
model = YOLO("balon_model.pt")
results = model(frame)
```

---

## Repo Dosya Yapısı

```
laser_guided_object_tracker/
├── laser_guidance_ot.py      # Ana Python kodu
├── arduino/
│   └── stepper_ctrl.ino      # Arduino kodu
├── images/
│   └── (dokümantasyon görselleri)
└── README.md
```

---

## Kalman Filter Kodu Analizi

Repo'daki Kalman filter OpenCV'nin `cv2.KalmanFilter` sınıfını kullanıyor.

**Örnek Kullanım:**
```python
import cv2
import numpy as np

# Kalman Filter oluştur
kalman = cv2.KalmanFilter(4, 2)  # 4 state, 2 measurement

# State transition matrix (A)
kalman.transitionMatrix = np.array([
    [1, 0, 1, 0],  # x = x + vx*dt
    [0, 1, 0, 1],  # y = y + vy*dt
    [0, 0, 1, 0],  # vx = vx
    [0, 0, 0, 1]   # vy = vy
], dtype=np.float32)

# Measurement matrix (H)
kalman.measurementMatrix = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0]
], dtype=np.float32)

# Process noise
kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.01

# Measurement noise
kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1

# Predict
predicted = kalman.predict()
pred_x, pred_y = predicted[0], predicted[1]

# Update with measurement
measured = np.array([[measured_x], [measured_y]], dtype=np.float32)
kalman.correct(measured)
```

---

## Arduino Kodu Analizi

Repo CheapStepper kütüphanesi kullanıyor:

```cpp
#include <CheapStepper.h>

CheapStepper stepper0(8,9,10,11);  // 4 pin
CheapStepper stepper1(4,5,6,7);

void setup() {
    Serial.begin(9600);
    stepper0.setRpm(12);
    stepper1.setRpm(12);
}

void loop() {
    // Serial komut oku
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        // Parse et ve çalıştır
    }
    
    // Non-blocking step
    stepper0.run();
    stepper1.run();
}
```

**Bizim AccelStepper ile:**
```cpp
#include <AccelStepper.h>

AccelStepper motorX(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);
AccelStepper motorY(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

void setup() {
    Serial.begin(115200);  // Daha hızlı
    motorX.setMaxSpeed(1000);
    motorX.setAcceleration(500);
}

void loop() {
    // Serial komut oku
    // Parse et
    
    // Non-blocking - HIZ tabanlı
    motorX.runSpeed();
    motorY.runSpeed();
}
```

---

## Adapte Edilecek Kod Parçaları

### 1. Serial Haberleşme Yapısı
```python
# Repo'dan ilham alınacak
import serial

class SerialComm:
    def __init__(self, port, baud=115200):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        
    def send(self, cmd):
        self.ser.write(f"{cmd}\n".encode())
        
    def read(self):
        if self.ser.in_waiting:
            return self.ser.readline().decode().strip()
        return None
```

### 2. Ana Döngü Yapısı
```python
# Repo'nun non-blocking yapısı
while True:
    ret, frame = cap.read()
    
    # Tespit
    target = detect_target(frame)
    
    # Kalman tahmin
    if target:
        kalman.correct(target)
    predicted = kalman.predict()
    
    # Kontrol hesapla
    if predicted:
        error_x = center_x - predicted[0]
        error_y = center_y - predicted[1]
        # Motor komutu gönder
        
    # GUI güncelle
```

---

## ÖNEMLİ NOTLAR

1. **Kalman Filter'ı kopyala, HSV tespiti KULLANMA**
   - Kalman kodu iyi çalışıyor
   - HSV yerine YOLO kullanacağız

2. **Serial protokolü basitleştir**
   - Repo'nun protokolü karmaşık
   - Bizimki daha basit ve okunabilir

3. **Step motor kontrolü güncelle**
   - CheapStepper → AccelStepper
   - Pozisyon → Hız tabanlı kontrol

4. **PID EKLE**
   - Repo'da PID yok
   - Biz simple-pid kütüphanesi ekleyeceğiz

5. **GUI EKLE**
   - Repo'da GUI yok
   - Tkinter ile arayüz yapacağız

6. **Güvenlik EKLE**
   - Repo'da yasak bölge yok
   - Repo'da acil durdur basit
   - Biz detaylı güvenlik ekleyeceğiz
