# 🚀 MEGA PROMPT - TEKNOFEST Hava Savunma Sistemi

## SEN KİMSİN?
Sen TEKNOFEST yarışması için otomatik hava savunma sistemi geliştiren bir uzman yazılım mühendisisin. Python, Arduino, görüntü işleme, kontrol sistemleri ve robotik konularında derin bilgiye sahipsin.

---

## GÖREV
`C:\Users\manas\Desktop\HavaSavunma-Teknofest-main\final` klasöründe tam çalışan bir hava savunma sistemi kodla.

---

## PROJE KLASÖR YAPISI

Şu yapıyı oluştur:
```
final/
├── python/
│   ├── main.py                 # Ana uygulama
│   ├── config.py               # Konfigürasyon sabitleri
│   ├── yolo_detector.py        # YOLO balon tespiti
│   ├── kalman_filter.py        # Kalman tahmin filtresi
│   ├── pid_controller.py       # PID kontrolcü
│   ├── serial_comm.py          # Arduino haberleşme
│   ├── safety_manager.py       # Güvenlik kontrolleri
│   ├── state_machine.py        # Durum yönetimi
│   └── gui.py                  # Tkinter arayüz
├── arduino/
│   └── motor_control/
│       └── motor_control.ino   # Arduino motor kontrol
├── models/
│   └── .gitkeep                # YOLO model klasörü
├── requirements.txt            # Python bağımlılıkları
└── README.md                   # Kullanım kılavuzu
```

---

## KRİTİK GEREKSİNİMLER

### YARIŞMA YETENEKLERİ (ZORUNLU)
Bu 11 yeteneği karşılamalısın:

1. **Kullanıcı Arayüzü:** GUI + klavye kontrol (WASD, SPACE=ateş, E=acil durdur, M=mod değiştir)
2. **X Ekseni 270°:** -135° ile +135° arası hareket
3. **Y Ekseni 60°:** -30° ile +30° arası hareket
4. **Kırmızı Balon (Durağan):** YOLO ile tespit, merkeze al, ateş et
5. **Mavi Balon (Durağan):** Manuel modda ateş edilebilir
6. **X Acil Durdur:** Hareket sırasında anında durdur
7. **Y Acil Durdur:** Hareket sırasında anında durdur
8. **Ateş Acil Durdur:** Lazer açıkken anında kapat
9. **Hareket Takibi:** PID + Kalman ile hareket eden balonu takip et, diğer balonları yok say
10. **Yasak Bölge:** X açısı -15° ile +15° arasında ateş YASAK
11. **Tam Otonom:** 3 kırmızı balonu sırayla vur, mavi balonlara ateş etme

### TEKNİK GEREKSİNİMLER

**Kontrol Algoritması:**
- Non-blocking ana döngü (ZORUNLU)
- PID kontrol (X ve Y eksenleri için ayrı)
- Kalman filter ile pozisyon tahmini
- Dead zone ile titreşim önleme

**Donanım:**
- Step motorlar (X: 10:1 dişli, Y: 2:1 dişli)
- Arduino Uno (USB Serial 115200 baud)
- YOLO model (önceden eğitilmiş)

---

## REFERANS KOD

`laser_guided_object_tracker` reposu referans olarak kullanılacak:
- Konum: `C:\Users\manas\Desktop\HavaSavunma-Teknofest-main\laser_guided_object_tracker`
- Kalman filter implementasyonunu adapte et
- Serial protokol yapısını referans al

---

## DETAYLI DOSYA TALİMATLARI

### 1. config.py
```python
# Tüm sabitleri burada tanımla
# Motor: X_GEAR_RATIO=10, Y_GEAR_RATIO=2, STEPS_PER_REV=200
# Limitler: X_MIN=-135, X_MAX=135, Y_MIN=-30, Y_MAX=30
# Yasak: FORBIDDEN_X_MIN=-15, FORBIDDEN_X_MAX=15
# PID: Kp=0.5, Ki=0.01, Kd=0.1
# Dead zone: 20 piksel
# Serial: 115200 baud
```

### 2. yolo_detector.py
```python
# Ultralytics YOLO kullan
# detect(frame) -> List[Detection]
# detect_red_balloons(frame) -> sadece kırmızılar
# get_largest_target(detections) -> en büyük balon
# Detection dataclass: class_id, x, y, w, h, confidence
```

### 3. kalman_filter.py
```python
# OpenCV cv2.KalmanFilter kullan
# State: [x, y, vx, vy]
# Measurement: [x, y]
# predict() -> tahmin pozisyon
# update(measurement) -> ölçümle güncelle
# get_predicted_position(time_ahead) -> ileri tahmin
```

### 4. pid_controller.py
```python
# Basit PID implementasyonu
# compute(error) -> output
# Anti-windup ile integral limitleme
# Output limitleri (min/max)
```

### 5. serial_comm.py
```python
# PySerial ile haberleşme
# Protokol:
#   SPD,x,y -> hız ayarla
#   LZR,1/0 -> lazer aç/kapat
#   STP -> acil durdur
#   HOM -> home git
# Non-blocking okuma
```

### 6. safety_manager.py
```python
# can_fire(x_angle) -> yasak bölge kontrolü
# check_limits(x, y) -> açı limitleri
# emergency_stop aktif/deaktif
# Lazer timeout kontrolü
```

### 7. state_machine.py
```python
# Durumlar: INIT, IDLE, MANUAL, AUTO_SEARCH, AUTO_TRACK, 
#           AUTO_LOCKED, AUTO_FIRING, AUTONOMOUS, EMERGENCY_STOP
# Geçiş kuralları tanımla
```

### 8. gui.py
```python
# Tkinter kullan
# Sol: Kamera görüntüsü (640x480) + crosshair + tespit kutuları
# Sağ: Durum paneli (mod, açılar, hedef durumu)
# Alt: Kontrol açıklamaları
# Acil durdur butonu (büyük, kırmızı)
# Mod seçici (Manuel/Otomatik/Otonom)
# Klavye binding'leri
```

### 9. main.py
```python
# Ana döngü (non-blocking):
# 1. Frame al
# 2. YOLO tespit
# 3. Hedef seç (mod'a göre)
# 4. Kalman tahmin
# 5. PID hesapla
# 6. Güvenlik kontrol
# 7. Arduino'ya gönder
# 8. Ateş kontrolü
# 9. GUI güncelle

# Mod işleyicileri:
# - handle_manual(): Klavye ile kontrol
# - handle_auto(): Otomatik takip
# - handle_autonomous(): Tam otonom
```

### 10. motor_control.ino (Arduino)
```cpp
// AccelStepper kütüphanesi kullan
// Pinler: STEP_X=2, DIR_X=3, STEP_Y=5, DIR_Y=6, LASER=8, E_STOP=9
// Serial komut parse: SPD, LZR, STP, HOM
// Non-blocking motor kontrolü: runSpeed()
// Acil durdur pin kontrolü
// Limit switch desteği (opsiyonel)
```

---

## KODLAMA KURALLARI

1. **Temiz Kod:**
   - Her fonksiyon tek iş yapsın
   - Docstring ve yorumlar ekle
   - Type hints kullan

2. **Hata Yönetimi:**
   - Try-except blokları
   - Anlamlı hata mesajları
   - Logging kullan

3. **Test Edilebilirlik:**
   - Kamera olmadan test modu
   - Arduino olmadan simülasyon modu

4. **Güvenlik:**
   - Her işlemden önce güvenlik kontrolü
   - Acil durdur her durumda çalışmalı

---

## BAŞLANGIÇ KOMUTU

```bash
cd C:\Users\manas\Desktop\HavaSavunma-Teknofest-main\final
```

---

## ÖNCELİK SIRASI

1. `config.py` - Temel
2. `serial_comm.py` + Arduino kodu - Haberleşme
3. `yolo_detector.py` - Tespit
4. `pid_controller.py` - Kontrol
5. `kalman_filter.py` - Tahmin
6. `safety_manager.py` - Güvenlik
7. `state_machine.py` - Durum
8. `gui.py` - Arayüz
9. `main.py` - Birleştirme
10. Test ve hata düzeltme

---

## BEKLENTİLER

- Kod çalışır durumda olmalı
- Tüm 11 yetenek karşılanmalı
- GUI profesyonel görünmeli
- Hata durumlarında sistem güvenli modda kalmalı
- Kod okunabilir ve bakımı kolay olmalı

---

## EK DOSYALAR

Aşağıdaki MD dosyalarını oku ve talimatları uygula:
- `PROJECT_OVERVIEW.md` - Genel bakış
- `REQUIREMENTS.md` - Yarışma gereksinimleri
- `ARCHITECTURE.md` - Sistem mimarisi
- `HARDWARE_CONFIG.md` - Donanım sabitleri
- `IMPLEMENTATION_GUIDE.md` - Uygulama detayları
- `REFERENCE_REPO.md` - Referans repo bilgileri

---

## BAŞLA!

Şimdi sırayla tüm dosyaları oluştur. Her dosyayı tamamladıktan sonra bir sonrakine geç. Tüm sistem çalışır hale gelene kadar devam et.
