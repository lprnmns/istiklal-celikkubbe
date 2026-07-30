# 🎯 TEKNOFEST Hava Savunma Sistemi - Proje Genel Bakış

## Proje Amacı
Lazer ile kırmızı balonları tespit edip patlatan, mavi balonlara (dost) ateş etmeyen otomatik hava savunma sistemi.

## Sistem Bileşenleri

### Donanım
- **Kamera:** USB webcam (görüntü işleme için)
- **Lazer:** Kırmızı balonları patlatmak için (kameraya paralel monte)
- **Step Motorlar:** 2 adet (X ekseni: yatay, Y ekseni: dikey)
- **Dişli Oranları:**
  - X ekseni: 150:15 (10:1 redüksiyon)
  - Y ekseni: 30:15 (2:1 redüksiyon)
- **Mikrodenetleyici:** Arduino Uno
- **Haberleşme:** USB Serial

### Yazılım
- **Görüntü İşleme:** Python + YOLO (önceden eğitilmiş model mevcut)
- **Motor Kontrol:** Arduino + AccelStepper
- **Kontrol Algoritması:** PID + Kalman Filter (Prediction)

## Hareket Limitleri
- **X Ekseni (Yatay):** 270 derece toplam (-135° ile +135°)
- **Y Ekseni (Dikey):** 60 derece toplam (-30° ile +30°)
- **Yasak Bölge:** X ekseni -15° ile +15° arası (ateş yasak)

## Çalışma Modları

### 1. Manuel Mod
- Joystick veya klavye ile kontrol
- Kullanıcı motorları hareket ettirir
- Kullanıcı ateş butonuna basar

### 2. Yarı-Otomatik Mod
- Sistem balonu tespit eder ve takip eder
- Kullanıcı ateş butonuna basar

### 3. Tam Otomatik Mod (Otonom)
- Sistem kırmızı balonları otomatik tespit eder
- Sırayla hedef alır ve ateş eder
- Mavi balonlara ateş ETMEZ
- Acil durdur butonu ile durdurulabilir

## Güvenlik Özellikleri
- **Acil Durdur Butonu:** Tüm hareketleri ve ateşi anında durdurur
- **Yasak Bölge:** -15° ile +15° arasında ateş engellenir
- **Limit Switchler:** Mekanik hareket sınırları (opsiyonel)

## Dosya Yapısı
```
final/
├── python/
│   ├── main.py                 # Ana uygulama (GUI + kontrol döngüsü)
│   ├── config.py               # Konfigürasyon sabitleri
│   ├── yolo_detector.py        # YOLO balon tespiti
│   ├── kalman_filter.py        # Kalman tahmin filtresi
│   ├── pid_controller.py       # PID kontrolcü
│   ├── serial_comm.py          # Arduino haberleşme
│   ├── motor_controller.py     # Motor yönetimi (Python tarafı)
│   ├── safety_manager.py       # Güvenlik kontrolleri
│   └── gui.py                  # Kullanıcı arayüzü
├── arduino/
│   └── motor_control/
│       └── motor_control.ino   # Arduino motor kontrol kodu
├── models/
│   └── (YOLO model dosyası buraya konacak)
├── tests/
│   └── test_system.py          # Test kodları
└── README.md                   # Kullanım kılavuzu
```

## Referans Repo
`laser_guided_object_tracker` reposu referans olarak kullanılacak:
- Kalman Filter implementasyonu
- Serial protokol yapısı
- Step motor kontrol mantığı
