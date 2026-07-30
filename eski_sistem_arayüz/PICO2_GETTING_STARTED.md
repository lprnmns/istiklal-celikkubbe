# 🚀 Raspberry Pi Pico 2 ile Başlangıç Rehberi

## 📋 Sistem Kurulumu Adımları

### Adım 1: Arduino IDE'de Pico 2 Kodunu Yükle

```bash
1. Arduino IDE aç
2. File → Open → pico_arduino/motor_control_pico/motor_control_pico.ino
3. Tools → Board → Raspberry Pi Pico 2 seç
4. Tools → Port → COMx (Pico 2) seç
5. Sketch → Upload (Ctrl+U)
6. Serial Monitor aç (115200 baud)
7. "OK,PICO_READY" mesajını gör
```

### Adım 2: Python Ortamını Hazırla

```bash
cd c:\Users\mehme\Desktop\pico\ denem1\HavaSavunma-Teknofest-Final-main
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Adım 3: Donanım Testi

```bash
# Test programını çalıştır
python python/donanim_test.py

# Menü:
# 1 - X Motorunu Test Et
# 2 - Y Motorunu Test Et
# 3 - Her İki Motoru Test Et
# 4 - Lazer Testi
# 5 - Acil Durdur Testi
```

### Adım 4: Ana Programı Çalıştır

```bash
python python/main.py

# GUI açılacak
# Kontroller:
# - WASD: Motor hareket
# - SPACE: Lazer
# - E: Acil Durdur
# - M: Mod değiştir (Manuel/Otomatik)
```

## 🔧 Pin Bağlantıları

```
RASPBERRY PI PICO 2 ────────── CNC SHIELD
─────────────────────────────────────────
GPIO2    → X-STEP
GPIO3    → X-DIR
GPIO6    → Y-STEP (Z-STEP)
GPIO7    → Y-DIR (Z-DIR)
GPIO10   → ENABLE
GPIO11   → Lazer
GPIO12   → E-STOP
GND      → GND (ortak)
3.3V     → VCC_IO

CNC SHIELD ────────── MOTOR SÜRÜCÜ (A4988/DRV8825/TMC2209)
──────────────────────────────────────
X-STEP → STEP (X)
X-DIR  → DIR (X)
Y-STEP → STEP (Y)
Y-DIR  → DIR (Y)
ENABLE → EN (ortak)
VM     → 12-24V Güç
GND    → GND (ortak)
```

## 📡 Python Komutları

```python
# Bağlantı (Otomatik Pico 2 bulur)
from serial_comm import SerialComm
from config import SerialConfig

config = SerialConfig()
comm = SerialComm(config)
comm.connect()

# Motor Kontrol
comm.set_speed(500, 0)     # X: 500, Y: 0
comm.set_speed(-300, 200)  # X: -300, Y: 200
comm.set_speed(0, 0)       # DUR

# Lazer
comm.laser_on()
comm.laser_off()

# Durum
comm.get_status()

# Bağlantı Testi
comm.send_command("PING")  # OK,PONG döner
```

## ✅ Kontrol Listesi

### Arduino IDE Kurulumu
- [ ] Arduino IDE 2.x yüklü
- [ ] Board support yüklü (earlephilhower/arduino-pico)
- [ ] Pico 2 board seçili
- [ ] COM port seçili
- [ ] motor_control_pico.ino yüklü
- [ ] Serial Monitor'de "OK,PICO_READY" görüldü

### Python Kurulumu
- [ ] Python 3.8+ yüklü
- [ ] Virtual environment oluşturuldu
- [ ] requirements.txt yüklendi (pip install -r)
- [ ] config.py Pico 2 pinlerine göre ayarlandı
- [ ] donanim_test.py başarıyla çalıştı

### Donanım Testi
- [ ] X motoru hareket etti
- [ ] Y motoru hareket etti
- [ ] Lazer yanıp söndü
- [ ] Acil durdur butonu çalıştı
- [ ] GND ortak bağlantısı yapıldı

### Entegrasyon
- [ ] main.py çalıştırıldı
- [ ] GUI açıldı
- [ ] Klavye kontrolü çalıştı
- [ ] Motor hareket etti
- [ ] Lazer kontrol çalıştı

## 🐛 Sorun Giderme

### Python Bağlantı Hatası

```
"Pico 2 bağlantı hatası"
→ COM portunu manuel belirle: config.py'de PORT değiştir
→ USB kablosu veri transferi desteklemeli
→ Arduino IDE'de "OK,PICO_READY" kontrol et
```

### Motor Hareket Etmiyor

```
→ GND ortak bağlantısı yapıldı mı?
→ CNC Shield'de jumper'lar doğru mı?
→ VM güç geldi mi? (12-24V)
→ ENABLE pini LOW mu?
```

### Lazer Çalışmıyor

```
→ GPIO11 fiziksel olarak bağlı mı?
→ Lazer modülü güç alıyor mu?
→ Transistör veya FET doğru mı bağlı?
```

## 📚 Dosyalar

```
Mikrodenetleyici Kodu:
├── pico_arduino/
│   ├── motor_control_pico/motor_control_pico.ino    ← Arduino IDE ile yükle
│   ├── tmc2209_uart_test/tmc2209_uart_test.ino      (opsiyonel)
│   └── ARDUINO_IDE_SETUP.md

Python Kodları (Pico 2 Uyarlaması Yapıldı):
├── python/
│   ├── config.py                  ← Pico 2 pinleri
│   ├── serial_comm.py             ← Pico 2 iletişimi
│   ├── donanim_test.py            ← Donanım testi
│   ├── main.py                    ← Ana program (değişiklik yok)
│   ├── gui.py                     (değişiklik yok)
│   └── ...
└── PICO2_PYTHON_UPDATE.md         ← Değişiklik özeti
```

## 🎯 Tipik Kullanım Akışı

```
1. Arduino IDE'de motor_control_pico.ino yükle
2. Serial Monitor'de test et (PING, SPD komutu)
3. python donanim_test.py çalıştır (Motor, Lazer, Buton test)
4. python main.py çalıştır (Ana sistem, GUI)
5. WASD ile motorları kontrol et
6. SPACE ile lazer aç/kapat
7. Sistem stabil ise kamera ve YOLO entegrasyonu ekle
```

## 💡 İpuçları

- ✅ Pico 2 otomatik olarak port algılanır
- ✅ Aynı Python kodları Arduino ve Pico 2 ile çalışır
- ✅ Baud rate değişmeyin (115200)
- ✅ CNC Shield jumper'ları doğru ayarlayın
- ✅ Motorları devre dışı konumda test edin

## 📞 Hızlı Referans

| İşlem | Komut |
|-------|-------|
| Pico 2 Bağla | `comm.connect()` |
| X Motor Sağa | `comm.set_speed(500, 0)` |
| Y Motor Yukarı | `comm.set_speed(0, 500)` |
| Motor Dur | `comm.set_speed(0, 0)` |
| Lazer Aç | `comm.laser_on()` |
| Lazer Kapat | `comm.laser_off()` |
| Bağlantı Test | `comm.send_command("PING")` |

---

**Başarılar! 🚀**

Herhangi bir sorun olursa:
1. [PICO2_PYTHON_UPDATE.md](PICO2_PYTHON_UPDATE.md) kontrol et
2. [pico_arduino/README.md](pico_arduino/README.md) kontrol et
3. [pico/PICO_WIRING.md](pico/PICO_WIRING.md) pin bağlantılarını kontrol et
