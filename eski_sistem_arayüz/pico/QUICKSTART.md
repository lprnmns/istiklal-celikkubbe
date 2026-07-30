# 🚀 Raspberry Pi Pico 2 - Hızlı Başlangıç Kılavuzu

## 📋 Hazırlık

### Gerekli Malzemeler

- ✅ Raspberry Pi Pico 2
- ✅ 2x TMC2209 Step Motor Sürücü
- ✅ 2x NEMA 17 Step Motor
- ✅ 12-24V DC Güç Kaynağı (min 2A)
- ✅ USB Kablo (Pico programlama için)
- ✅ Bağlantı kabloları
- ✅ Breadboard veya PCB

### Gerekli Yazılımlar

1. **Thonny IDE** (önerilen) veya **mpremote**
   ```bash
   # mpremote kurulumu (Windows):
   pip install mpremote
   ```

2. **MicroPython Firmware** (Pico 2 için)
   - İndirme: https://micropython.org/download/RPI_PICO2/
   - En son `.uf2` dosyasını indir

---

## 🔧 1. Pico'ya MicroPython Yükleme

### Adımlar:

1. **BOOTSEL** butonuna basılı tutarak Pico'yu USB'ye tak
2. **RPI-RP2** adında bir sürücü görünecek
3. İndirdiğin `.uf2` dosyasını bu sürücüye kopyala
4. Pico otomatik olarak yeniden başlayacak
5. Artık MicroPython hazır! ✅

### Test:

```python
# Thonny'de Shell'e yaz:
>>> print("Hello Pico!")
Hello Pico!
```

---

## 🔌 2. Donanım Bağlantısı

### Temel Bağlantı Şeması

```
RASPBERRY PI PICO 2          TMC2209 (X)         TMC2209 (Y)
───────────────────          ──────────          ──────────
GPIO2 ──────────────────────► STEP
GPIO3 ──────────────────────► DIR
GPIO4 ──────────────────────► MS1
GPIO5 ──────────────────────► MS2
GPIO6 ────────────────────────────────────────► STEP
GPIO7 ────────────────────────────────────────► DIR
GPIO8 ────────────────────────────────────────► MS1
GPIO9 ────────────────────────────────────────► MS2
GPIO10 ─────────────────────► EN ──────────────► EN (ortak)
GPIO11 ─────────────────────► Lazer Modülü
GPIO12 ─────────────────────► Acil Durdur Butonu

3.3V ───────────────────────► VCC_IO ──────────► VCC_IO
GND ────────────────────────► GND ─────────────► GND (ortak!)

                     ┌───► VM (TMC X)
Güç Kaynağı (12-24V) ├───► VM (TMC Y)
                     └───► GND (ortak!)
```

### ⚠️ Kritik Kontroller

- [ ] **GND ortak mı?** (Pico + TMC + Güç Kaynağı)
- [ ] **VCC_IO = 3.3V** (5V değil!)
- [ ] **VM = 12-24V** (motor güç kaynağı)
- [ ] **Polarite doğru mu?** (multimetre ile kontrol)

---

## 📤 3. Kod Yükleme

### Yöntem 1: Thonny ile (Kolay)

1. Thonny'yi aç
2. Sağ alt köşeden **MicroPython (Raspberry Pi Pico)** seç
3. `motor_control_pico.py` dosyasını aç
4. **File → Save as...** → **Raspberry Pi Pico** → `main.py` olarak kaydet
5. Pico otomatik çalıştıracak

### Yöntem 2: mpremote ile (Hızlı)

```bash
# Ana dizine git
cd "c:\Users\mehme\Desktop\pico denem1\HavaSavunma-Teknofest-Final-main\pico"

# Kodu Pico'ya yükle
mpremote fs cp motor_control_pico.py :main.py

# Pico'yu resetle
mpremote reset

# Serial çıktıyı izle
mpremote
```

---

## 🧪 4. İlk Test

### Basit Test (simple_test.py)

```bash
# Test kodunu yükle
mpremote fs cp simple_test.py :

# Çalıştır
mpremote run simple_test.py
```

**Menü seçenekleri:**
1. X Motorunu test et
2. Y Motorunu test et
3. Her iki motoru test et
4. Lazer testi
5. Mikroadım değiştir

**Beklenen sonuç:**
- Motorlar yumuşak hareket etmeli
- Garip ses veya titreşim olmamalı
- Lazer açılıp kapanmalı

---

## 🖥️ 5. Python ile İletişim

### Serial Bağlantı (Windows)

```python
import serial
import time

# COM portunu bul (Cihaz Yöneticisi'nden kontrol et)
# Örnek: COM3, COM4, vb.

ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)  # Bağlantı için bekle

# Motor hareketini test et
# Format: SPD,hız_x,hız_y (-1000 ile 1000 arası)

# X motorunu sağa hareket ettir (orta hız)
ser.write(b"SPD,500,0\n")
time.sleep(2)

# Dur
ser.write(b"SPD,0,0\n")
time.sleep(1)

# Y motorunu yukarı hareket ettir
ser.write(b"SPD,0,500\n")
time.sleep(2)

# Dur
ser.write(b"SPD,0,0\n")

# Lazer aç
ser.write(b"LZR,1\n")
time.sleep(1)

# Lazer kapat
ser.write(b"LZR,0\n")

# Bağlantıyı kapat
ser.close()
```

### Komut Formatları

```
┌─────────────────────────────────────────────────┐
│ KOMUT          │ FORMAT           │ AÇIKLAMA     │
├────────────────┼──────────────────┼──────────────┤
│ Hız ayarla     │ SPD,x,y          │ -1000 ~ 1000 │
│ Lazer aç       │ LZR,1            │ 1 = açık     │
│ Lazer kapat    │ LZR,0            │ 0 = kapalı   │
│ Ping testi     │ PING             │ PONG döner   │
│ Mikroadım      │ MICROSTEP,x,1/16 │ x,y veya both│
└─────────────────────────────────────────────────┘
```

---

## 🔬 6. TMC2209 Mikroadım Ayarı (Manuel)

### Başlangıç Ayarı (Kod içinde)

```python
# motor_control_pico.py - main() içinde
set_microstepping('both', '1/8')  # ✅ Önerilen
```

### Çalışma Sırasında Değiştirme

```python
# Serial üzerinden:
ser.write(b"MICROSTEP,both,1/16\n")  # 1/16 mikroadım
```

### Mikroadım Tablosu

```
┌──────────┬──────────────┬───────────────────┐
│ Mod      │ Hassasiyet   │ Kullanım Alanı    │
├──────────┼──────────────┼───────────────────┤
│ 1/8      │ ⭐⭐⭐       │ Genel Kullanım ✅ │
│ 1/16     │ ⭐⭐⭐⭐     │ Hassas Pozisyon   │
│ 1/32     │ ⭐⭐⭐⭐⭐   │ Ultra Hassas      │
│ 1/64     │ ⭐⭐⭐⭐⭐⭐ │ Maksimum Hassas   │
└──────────┴──────────────┴───────────────────┘

NOT: Yüksek mikroadım = Daha hassas ama daha yavaş
```

---

## ⚡ 7. Performans Optimizasyonu

### Hız Ayarları

```python
# motor_control_pico.py içinde değiştir:

MIN_STEP_DELAY_US = 50    # Minimum gecikme (maks hız)
MAX_STEP_DELAY_US = 2000  # Maksimum gecikme (başlangıç)
ACCEL_RATE = 0.05         # Hızlanma/yavaşlama (düşük = yumuşak)
```

**Daha hızlı hareket için:**
```python
MIN_STEP_DELAY_US = 30   # ⚠️ Dikkat: Motor atlama yapabilir
```

**Daha yumuşak hareket için:**
```python
ACCEL_RATE = 0.02  # Daha yavaş hızlanır
```

---

## 🛠️ 8. İleri Seviye: UART ile TMC2209 Kontrolü

### Donanım Eklentisi

```
1. PDN_UART pinini 1kΩ ile VCC_IO'ya bağla
2. TMC RX ──► Pico GPIO4 (TX)
3. TMC TX ──► Pico GPIO5 (RX)
```

### Yazılım Kullanımı

```python
from tmc2209_uart import TMC2209

# X motoru için TMC2209 başlat
tmc_x = TMC2209(uart_id=1, tx_pin=4, rx_pin=5, slave_address=0x00)

# Ayarları yap
tmc_x.init_driver(
    run_current=1000,    # 1A motor akımı
    microstep='1/16',    # 1/16 mikroadım
    stealthchop=True     # Sessiz mod aktif
)

# Durum kontrolü
status = tmc_x.get_status()
print(f"Sıcaklık uyarısı: {status['otpw']}")
print(f"Anlık akım: {status['cs_actual']}")
```

**Avantajları:**
- ✅ Yazılımdan akım ayarı
- ✅ StealthChop (sessiz çalışma)
- ✅ Stallguard (takılma algılama)
- ✅ Sıcaklık ve durum izleme

---

## 🐛 Sorun Giderme

### Problem: Motor hareket etmiyor

**Kontrol listesi:**
1. ENABLE pini LOW mu? (Aktif seviye)
   ```python
   enable.value()  # 0 olmalı
   ```
2. Güç geliyor mu?
   ```bash
   # Multimetre ile VM pinini ölç: 12-24V
   ```
3. STEP sinyali gidiyor mu?
   ```python
   # Serial'de "STS,MOVING" görünmeli
   ```

### Problem: Motor titriyor

**Çözümler:**
1. Mikroadımı düşür:
   ```python
   set_microstepping('both', '1/8')  # 1/16 yerine
   ```
2. Hızı azalt:
   ```python
   ser.write(b"SPD,200,0\n")  # 500 yerine
   ```
3. Akımı artır (UART ile):
   ```python
   tmc_x.set_current(1200)  # 800 yerine
   ```

### Problem: Python ile bağlanamıyorum

**Çözümler:**
1. COM portunu kontrol et:
   ```python
   import serial.tools.list_ports
   ports = serial.tools.list_ports.comports()
   for p in ports:
       print(p.device, p.description)
   ```
2. Pico'yu resetle:
   ```bash
   mpremote reset
   ```
3. Baudrate doğru mu:
   ```python
   ser = serial.Serial('COM3', 115200)  # 9600 değil!
   ```

---

## 📚 Ek Kaynaklar

### Dosya Yapısı

```
pico/
├── motor_control_pico.py   # Ana motor kontrol
├── simple_test.py          # Basit test programı
├── tmc2209_uart.py         # TMC2209 UART kütüphanesi
├── PICO_WIRING.md          # Detaylı bağlantı şeması
└── QUICKSTART.md           # Bu dosya
```

### Yararlı Linkler

- [Raspberry Pi Pico Datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)
- [TMC2209 Datasheet](https://www.trinamic.com/products/integrated-circuits/details/tmc2209-la/)
- [MicroPython Dokümantasyonu](https://docs.micropython.org/en/latest/)

---

## ✅ Test Checklist

### İlk Kurulum
- [ ] MicroPython firmware yüklendi
- [ ] Pinler doğru bağlandı
- [ ] GND ortak yapıldı
- [ ] Güç kaynağı bağlandı (12-24V)
- [ ] Kod Pico'ya yüklendi

### İlk Test
- [ ] `simple_test.py` çalıştı
- [ ] X motoru hareket etti
- [ ] Y motoru hareket etti
- [ ] Lazer açıldı/kapandı
- [ ] Acil durdur çalıştı

### Python İletişimi
- [ ] Serial bağlantı kuruldu
- [ ] SPD komutu çalıştı
- [ ] LZR komutu çalıştı
- [ ] PING testi başarılı

### İleri Seviye (Opsiyonel)
- [ ] UART bağlantısı yapıldı
- [ ] TMC2209 başlatıldı
- [ ] Akım ayarı yapıldı
- [ ] Durum okuma çalıştı

---

## 🎯 Sonraki Adımlar

1. **Manuel test başarılı ise** → Python entegrasyonuna geç
2. **Python entegrasyonu tamam ise** → UART'ı etkinleştir
3. **UART çalışıyor ise** → Ana sisteme entegre et
4. **Sistem stabil ise** → PID ayarlarını yap

**Başarılar! 🚀**

---

## 💡 İpuçları

- 🔋 **Güç:** İlk test sırasında 12V kullan, sonra 24V'ye geç
- 🎚️ **Mikroadım:** 1/8 ile başla, gerekirse artır
- ⚡ **Hız:** Yavaş başla, sistemi stabil tut
- 🧪 **Test:** Her değişiklikten sonra basit test yap
- 📝 **Log:** Serial çıktıyı kaydet (debug için)

---

**Son Güncelleme:** 16 Ocak 2026
