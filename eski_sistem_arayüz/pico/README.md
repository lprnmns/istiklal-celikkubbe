# 🎯 Hava Savunma Sistemi - Raspberry Pi Pico 2 Port

Arduino Uno tabanlı sistemin Raspberry Pi Pico 2 portudur. TMC2209 step motor sürücüleri ile çalışır.

## 📦 İçerik

```
pico/
├── 📄 motor_control_pico.py    # Ana motor kontrol programı
├── 📄 simple_test.py           # Basit donanım test programı
├── 📄 tmc2209_uart.py          # TMC2209 UART kontrol kütüphanesi
├── 📖 QUICKSTART.md            # Hızlı başlangıç kılavuzu
├── 📖 PICO_WIRING.md           # Detaylı bağlantı şeması
└── 📖 README.md                # Bu dosya
```

## 🚀 Hızlı Başlangıç

### 1. MicroPython Yükle
```bash
# BOOTSEL'e basılı tut, USB'ye tak
# .uf2 dosyasını sürücüye kopyala
```

### 2. Kodu Yükle
```bash
mpremote fs cp motor_control_pico.py :main.py
mpremote reset
```

### 3. Test Et
```bash
mpremote run simple_test.py
```

Detaylı kurulum için: [QUICKSTART.md](QUICKSTART.md)

## 🔌 Pin Konfigürasyonu

### Motor Kontrol Pinleri
```
X Motor:  STEP=GPIO2,  DIR=GPIO3,  MS1=GPIO4,  MS2=GPIO5
Y Motor:  STEP=GPIO6,  DIR=GPIO7,  MS1=GPIO8,  MS2=GPIO9
Kontrol:  ENABLE=GPIO10, LASER=GPIO11, E-STOP=GPIO12
UART:     TX=GPIO0,    RX=GPIO1
```

### TMC2209 Mikroadım Ayarı (Manuel)
```
MS1=LOW,  MS2=LOW  → 1/8  mikroadım (önerilen) ✅
MS1=HIGH, MS2=HIGH → 1/16 mikroadım
MS1=HIGH, MS2=LOW  → 1/32 mikroadım
MS1=LOW,  MS2=HIGH → 1/64 mikroadım
```

Detaylı bağlantı şeması: [PICO_WIRING.md](PICO_WIRING.md)

## 📡 Serial Komutlar

### Python'dan Kontrol
```python
import serial

ser = serial.Serial('COM3', 115200)

# Hız kontrolü (-1000 ~ 1000)
ser.write(b"SPD,500,0\n")    # X motoru sağa
ser.write(b"SPD,0,500\n")    # Y motoru yukarı
ser.write(b"SPD,0,0\n")      # Dur

# Lazer kontrolü
ser.write(b"LZR,1\n")        # Aç
ser.write(b"LZR,0\n")        # Kapat

# Mikroadım değiştir
ser.write(b"MICROSTEP,both,1/16\n")
```

### Komut Formatı
```
SPD,x,y              # Hız ayarı
LZR,0/1              # Lazer kontrol
PING                 # Bağlantı testi (PONG döner)
MICROSTEP,motor,mod  # Mikroadım ayarı
```

## 🔬 TMC2209 UART Kontrolü (İleri Seviye)

### Donanım Bağlantısı
```
PDN_UART → 1kΩ → VCC_IO (3.3V)
TMC RX → Pico TX (GPIO4)
TMC TX → Pico RX (GPIO5)
```

### Yazılım Kullanımı
```python
from tmc2209_uart import TMC2209

# TMC2209 başlat
tmc = TMC2209(uart_id=1, tx_pin=4, rx_pin=5, slave_address=0x00)

# Sürücüyü yapılandır
tmc.init_driver(
    run_current=1000,    # 1A akım
    microstep='1/16',    # 1/16 mikroadım
    stealthchop=True     # Sessiz mod
)

# Durum oku
status = tmc.get_status()
print(f"Sıcaklık: {status['otpw']}")
print(f"Akım: {status['cs_actual']}")
```

## 🎛️ Özellikler

### Temel Özellikler
- ✅ Çift motor kontrolü (X/Y ekseni)
- ✅ Hızlanma/yavaşlama (ramping)
- ✅ Acil durdur desteği
- ✅ Lazer kontrol
- ✅ Serial iletişim (115200 baud)

### TMC2209 Özellikleri
- ✅ Manuel mikroadım ayarı (MS1/MS2 pinleri)
- ✅ UART ile gelişmiş kontrol (opsiyonel)
- ✅ StealthChop (sessiz çalışma)
- ✅ SpreadCycle (güç modu)
- ✅ Akım ayarı (0-2A)
- ✅ Sıcaklık koruması

### Performans
- ⚡ Min adım gecikmesi: 50µs (20kHz)
- 🎯 Hassasiyet: 1/8 - 1/256 mikroadım
- 🔋 Güç: 12-24V DC
- 🧵 Multi-threading desteği

## 📊 Performans Karşılaştırması

| Özellik | Arduino Uno | Pico 2 |
|---------|-------------|--------|
| İşlemci | 16 MHz | 150 MHz ⚡ |
| RAM | 2 KB | 520 KB 🚀 |
| GPIO | 14 | 26 |
| UART | 1 | 2 |
| Min adım gecikmesi | 80µs | 50µs |
| Multi-threading | ❌ | ✅ |

## 🛠️ Gereksinimler

### Donanım
- Raspberry Pi Pico 2
- 2x TMC2209 step motor sürücü
- 2x NEMA 17 step motor
- 12-24V DC güç kaynağı (min 2A)
- USB kablo

### Yazılım
- MicroPython firmware (Pico 2)
- Thonny IDE veya mpremote
- Python 3.x (PC tarafı için)
- pyserial (`pip install pyserial`)

## 📝 Test Prosedürü

### 1. Basit Donanım Testi
```bash
mpremote run simple_test.py
```
**Menü seçenekleri:**
- X/Y motor testi
- Lazer testi
- Mikroadım değiştirme
- Hız testi

### 2. Ana Program Testi
```bash
mpremote fs cp motor_control_pico.py :main.py
mpremote reset
```

### 3. Python İletişim Testi
```python
import serial
ser = serial.Serial('COM3', 115200)
ser.write(b"PING\n")
print(ser.readline())  # b"OK,PONG\n"
```

## 🐛 Sorun Giderme

### Motor Hareket Etmiyor
1. ENABLE pini kontrol et (LOW olmalı)
2. VM güç girişini ölç (12-24V)
3. GND ortak bağlantısını kontrol et
4. Motor kablo bağlantılarını kontrol et

### Titreşim/Gürültü
1. Mikroadımı azalt (1/16 → 1/8)
2. Hızı düşür
3. UART ile akımı artır

### UART Çalışmıyor
1. TX/RX pinlerini kontrol et
2. PDN_UART 1kΩ ile VCC_IO'ya bağlı mı?
3. Baudrate doğru mu? (115200)
4. Slave address doğru mu?

## 📚 Dokümantasyon

- **[QUICKSTART.md](QUICKSTART.md)** - Adım adım kurulum kılavuzu
- **[PICO_WIRING.md](PICO_WIRING.md)** - Detaylı pin bağlantıları ve şemalar
- **[motor_control_pico.py](motor_control_pico.py)** - Ana kod (yorumlu)
- **[tmc2209_uart.py](tmc2209_uart.py)** - UART kütüphanesi (yorumlu)

## 🔄 Arduino'dan Geçiş Farkları

### Pin Numaraları
```
Arduino → Pico
-------------------
D2  → GPIO2  (X STEP)
D3  → GPIO3  (X DIR)
D5  → GPIO6  (Y STEP)
D6  → GPIO7  (Y DIR)
D8  → GPIO10 (ENABLE)
D12 → GPIO11 (LASER)
D9  → GPIO12 (E-STOP)
```

### Kod Farkları
```python
# Arduino
digitalWrite(pin, HIGH)

# Pico MicroPython
pin.value(1)
```

```python
# Arduino
delayMicroseconds(100)

# Pico MicroPython
time.sleep_us(100)
```

### Avantajlar
- ✅ Daha güçlü işlemci (150 MHz vs 16 MHz)
- ✅ Daha fazla RAM (520 KB vs 2 KB)
- ✅ Multi-threading desteği
- ✅ 2 UART portu (Python + TMC2209)
- ✅ Daha fazla GPIO (26 vs 14)

## 🎯 Geliştirme Yol Haritası

### Tamamlanan
- [x] Temel motor kontrolü
- [x] Serial iletişim
- [x] Manuel mikroadım ayarı
- [x] Lazer kontrolü
- [x] Acil durdur

### Planlanıyor
- [ ] UART ile TMC2209 kontrolü
- [ ] StallGuard (takılma algılama)
- [ ] Pozisyon kaydetme (encoder)
- [ ] WiFi entegrasyonu (Pico W)
- [ ] Web arayüzü

## 📞 Destek

Sorun yaşarsanız:
1. [QUICKSTART.md](QUICKSTART.md) dosyasını kontrol edin
2. [PICO_WIRING.md](PICO_WIRING.md) bağlantıları doğrulayın
3. `simple_test.py` ile donanımı test edin
4. Serial çıktıyı kontrol edin (`mpremote`)

## 📄 Lisans

Bu proje Teknofest Hava Savunma Sistemi yarışması için geliştirilmiştir.

---

**Geliştirici Notları:**
- Kod MicroPython (v1.22+) ile test edilmiştir
- TMC2209 sürücüler v1.3 donanım revizyonudur
- Güç kaynağı olarak 24V/2A adaptör önerilir
- İlk testlerde 1/8 mikroadım kullanın

**Son Güncelleme:** 16 Ocak 2026
