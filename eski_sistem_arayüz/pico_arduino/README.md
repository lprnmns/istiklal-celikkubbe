# 🚀 Arduino IDE ile Raspberry Pi Pico 2 - Hızlı Başlangıç

## 📁 Dosya Yapısı

```
pico_arduino/
├── motor_control_pico/
│   └── motor_control_pico.ino    # Ana motor kontrol (UART'sız)
├── tmc2209_uart_test/
│   └── tmc2209_uart_test.ino     # TMC2209 UART test (TMCStepper ile)
├── ARDUINO_IDE_SETUP.md          # Detaylı Arduino IDE kurulum
└── README.md                     # Bu dosya
```

## ⚡ Hızlı Kurulum (5 Dakika)

### 1️⃣ Arduino IDE Yükle
```
https://www.arduino.cc/en/software
→ Arduino IDE 2.x indir ve kur
```

### 2️⃣ Pico Board Desteği Ekle

**File → Preferences → Additional Boards Manager URLs:**
```
https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
```

**Tools → Board → Boards Manager:**
```
"Raspberry Pi Pico/RP2040" ara ve yükle
```

### 3️⃣ Board Seç

```
Tools → Board → Raspberry Pi RP2040 Boards → Raspberry Pi Pico 2
Tools → Port → COMx (Raspberry Pi Pico)
```

### 4️⃣ Kodu Yükle

```
File → Open → motor_control_pico.ino
Sketch → Upload (Ctrl+U)
```

### 5️⃣ Test Et

```
Tools → Serial Monitor (Ctrl+Shift+M)
Baud Rate: 115200
```

**Serial'e yaz:**
```
PING          → OK,PONG
SPD,500,0     → X motoru hareket eder
SPD,0,0       → Motor durur
LZR,1         → Lazer açılır
```

## 📋 İki Sketch Karşılaştırması

### 🔹 motor_control_pico.ino (Temel)

**Özellikler:**
- ✅ Hiçbir kütüphane gerektirmez
- ✅ Manuel mikroadım ayarı (MS1/MS2 pinleri)
- ✅ Hızlı başlangıç
- ✅ Python ile serial iletişim
- ✅ Lazer ve acil durdur kontrolü

**Kullanım:**
- İlk testler için ideal
- UART gerektirmez
- Plug & play

**Pin Kullanımı:**
```
GPIO2,3   → X Motor (STEP, DIR)
GPIO4,5   → X Motor (MS1, MS2)
GPIO6,7   → Y Motor (STEP, DIR)
GPIO8,9   → Y Motor (MS1, MS2)
GPIO10    → ENABLE
GPIO11    → LASER
GPIO12    → E-STOP
```

---

### 🔹 tmc2209_uart_test.ino (İleri Seviye)

**Özellikler:**
- ✅ TMCStepper kütüphanesi ile UART kontrolü
- ✅ Dinamik akım ayarı (0-2A)
- ✅ Dinamik mikroadım ayarı (1/1 - 1/256)
- ✅ StealthChop/SpreadCycle geçişi
- ✅ Durum okuma (sıcaklık, hata vb.)

**Kullanım:**
- Gelişmiş kontrol için
- TMCStepper kütüphanesi gerekli
- UART bağlantısı gerekli

**Ek Pin Kullanımı:**
```
GPIO4    → TMC2209 PDN_UART (TX)
GPIO5    → TMC2209 PDN_UART (RX)
```

**Kütüphane Kurulumu:**
```
Sketch → Include Library → Manage Libraries
→ "TMCStepper" ara ve yükle
```

---

## 🔌 Donanım Bağlantıları

### Temel Mod (motor_control_pico.ino)

```
RASPBERRY PI PICO 2          TMC2209
───────────────────          ────────────
GPIO2 ──────────────────────► STEP
GPIO3 ──────────────────────► DIR
GPIO4 ──────────────────────► MS1 (CFG1)
GPIO5 ──────────────────────► MS2 (CFG2)
GPIO10 ─────────────────────► EN
3.3V ───────────────────────► VCC_IO
GND ────────────────────────► GND

                             MS3 (CFG3) → GND
                             PDN_UART → VCC_IO (3.3V)
                             VM → 12-24V Güç Kaynağı
```

### UART Mod (tmc2209_uart_test.ino)

```
RASPBERRY PI PICO 2          TMC2209
───────────────────          ────────────
GPIO2 ──────────────────────► STEP
GPIO3 ──────────────────────► DIR
GPIO10 ─────────────────────► EN
GPIO4 ──────────────────────► PDN_UART (1kΩ ile birlikte)
GPIO5 ──────────────────────► PDN_UART (aynı pin)
3.3V ───────────────────────► VCC_IO
GND ────────────────────────► GND

                             1kΩ direnci PDN_UART ile VCC_IO arası
                             VM → 12-24V Güç Kaynağı
```

---

## 📡 Komut Formatları

### motor_control_pico.ino Komutları

| Komut | Format | Açıklama |
|-------|--------|----------|
| Hız ayarla | `SPD,x,y` | x,y: -1000~1000 |
| Lazer aç | `LZR,1` | 1 = açık |
| Lazer kapat | `LZR,0` | 0 = kapalı |
| Ping testi | `PING` | PONG döner |
| Mikroadım | `MICROSTEP,B,16` | B=both, 8/16/32/64 |

**Örnek:**
```
SPD,500,0      # X motoru sağa, orta hız
SPD,-300,200   # X sola yavaş, Y yukarı yavaş
SPD,0,0        # Dur
MICROSTEP,X,32 # X motoru 1/32 mikroadım
```

### tmc2209_uart_test.ino Komutları

Serial Monitor'den tek tuş ile:

| Tuş | Fonksiyon |
|-----|-----------|
| 1 | Motor testi (200 adım) |
| 2 | Akım değiştir |
| 3 | Mikroadım değiştir |
| 4 | StealthChop/SpreadCycle geçiş |
| 5 | Durum oku |

---

## 🧪 Test Prosedürü

### Adım 1: Temel Test (motor_control_pico.ino)

```bash
1. Kodu yükle
2. Serial Monitor aç (115200)
3. "OK,PICO_READY" mesajını gör
4. "PING" yaz → "OK,PONG" dönmeli
5. "SPD,200,0" yaz → X motoru hareket etmeli
6. "SPD,0,0" yaz → Motor durmalı
```

### Adım 2: UART Test (tmc2209_uart_test.ino)

```bash
1. TMCStepper kütüphanesini yükle
2. UART bağlantısını yap (GPIO4,5)
3. Kodu yükle
4. Serial Monitor aç
5. "TMC2209 algılandı!" mesajını gör
6. "1" bas → Motor testi
7. "5" bas → Durum kontrolü
```

---

## 🐛 Sorun Giderme

### Port Görünmüyor

1. USB kablosu veri transferi desteklemeli
2. BOOTSEL'e basarak yükle:
   - BOOTSEL bas
   - USB tak
   - Upload butonuna tıkla

### Compilation Error

1. Board: "Raspberry Pi Pico 2" seçili mi?
2. arduino-pico core yüklü mü?
3. TMCStepper kütüphanesi yüklü mü? (UART için)

### Motor Hareket Etmiyor

1. VM güç geliyor mu? (12-24V)
2. GND ortak mı?
3. ENABLE pini LOW mu? (kod içinde ayarlı)
4. Serial'de "STS,MOVING" var mı?

### TMC2209 Algılanmıyor (UART)

1. PDN_UART 1kΩ ile VCC_IO'ya bağlı mı?
2. TX/RX pinleri doğru mu?
3. Baud rate 115200 mi?
4. Serial Monitor'de "TMC Sürüm: 0x21" görünüyor mu?

---

## 🎯 Hangi Sketch'i Kullanmalıyım?

### motor_control_pico.ino Kullan Eğer:
- ✅ Hızlı başlangıç istiyorsan
- ✅ Basit motor kontrolü yeterli
- ✅ Ekstra kablolama istemiyorsan
- ✅ Manuel mikroadım ayarı yeterli (1/8, 1/16, vb.)

### tmc2209_uart_test.ino Kullan Eğer:
- ✅ Dinamik akım kontrolü istiyorsan
- ✅ StealthChop (sessiz mod) istiyorsan
- ✅ Gerçek zamanlı durum okuma gerekiyorsa
- ✅ Gelişmiş TMC2209 özelliklerini kullanmak istiyorsan

---

## 📚 Ek Kaynaklar

- **[ARDUINO_IDE_SETUP.md](ARDUINO_IDE_SETUP.md)** - Detaylı Arduino IDE kurulum
- **[../pico/PICO_WIRING.md](../pico/PICO_WIRING.md)** - Detaylı bağlantı şeması
- **[motor_control_pico.ino](motor_control_pico/motor_control_pico.ino)** - Temel kod
- **[tmc2209_uart_test.ino](tmc2209_uart_test/tmc2209_uart_test.ino)** - UART kodu

---

## ✅ Önerilen Geliştirme Yolu

```
1. ✅ motor_control_pico.ino ile başla
   └─► Donanım testlerini tamamla
   └─► Python entegrasyonunu yap
   └─► Manuel mikroadım ile optimize et

2. 🚀 tmc2209_uart_test.ino'ya geç
   └─► UART bağlantısını yap
   └─► Akım optimizasyonu yap
   └─► StealthChop test et
   └─► Durum izleme ekle

3. 🎯 İkisini birleştir
   └─► motor_control_pico.ino + TMCStepper
   └─► Python ile UART kontrolü
   └─► Tam özellikli sistem
```

---

## 🔄 Python Entegrasyonu

Mevcut `serial_comm.py` doğrudan çalışır:

```python
import serial

ser = serial.Serial('COM3', 115200)

# Motor kontrolü (motor_control_pico.ino ile)
ser.write(b"SPD,500,0\n")   # X motoru sağa
ser.write(b"SPD,0,500\n")   # Y motoru yukarı
ser.write(b"SPD,0,0\n")     # Dur

# Lazer
ser.write(b"LZR,1\n")       # Aç
ser.write(b"LZR,0\n")       # Kapat
```

---

**Son Güncelleme:** 16 Ocak 2026

**Başarılar! 🎉**
