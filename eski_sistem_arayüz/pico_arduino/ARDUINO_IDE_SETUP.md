# 🔧 Arduino IDE ile Raspberry Pi Pico 2 Kurulumu

## 📋 İçindekiler
1. [Arduino IDE Kurulumu](#arduino-ide-kurulumu)
2. [Pico Board Support Ekleme](#pico-board-support-ekleme)
3. [Kod Yükleme](#kod-yükleme)
4. [Kütüphane Gereksinimleri](#kütüphane-gereksinimleri)
5. [Test ve Sorun Giderme](#test-ve-sorun-giderme)

---

## 🖥️ Arduino IDE Kurulumu

### Adım 1: Arduino IDE İndirme

**Arduino IDE 2.x (Önerilen)**
- İndirme: https://www.arduino.cc/en/software
- Windows için: `arduino-ide_2.x.x_Windows_64bit.exe`
- Sürüm: 2.0.0 veya üzeri

**Alternatif: Arduino IDE 1.8.x**
- Eski sürüm ama daha stabil
- İndirme: https://www.arduino.cc/en/software/OldSoftwareReleases
- Sürüm: 1.8.19 önerilir

### Adım 2: Arduino IDE Kurulumu

1. İndirilen `.exe` dosyasını çalıştır
2. "I accept the agreement" seç
3. Varsayılan klasöre kur: `C:\Program Files\Arduino IDE`
4. Tüm ek bileşenleri seç (USB driver dahil)
5. "Install" butonuna tıkla
6. Kurulum tamamlandığında Arduino IDE'yi aç

---

## 🎛️ Pico Board Support Ekleme

### Yöntem 1: Arduino-Pico Core (Önerilen ✅)

Arduino IDE için Raspberry Pi Pico desteği ekler.

#### Adım 1: Board Manager URL Ekleme

1. Arduino IDE'yi aç
2. **File** → **Preferences** (veya `Ctrl+,`)
3. **Additional Boards Manager URLs** alanına şunu ekle:
   ```
   https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
   ```
4. Birden fazla URL varsa virgül ile ayır
5. **OK** butonuna tıkla

#### Adım 2: Pico Board Paketini Yükleme

1. **Tools** → **Board** → **Boards Manager...**
2. Arama kutusuna **"pico"** yaz
3. **"Raspberry Pi Pico/RP2040"** paketini bul (Earle F. Philhower, III)
4. **Install** butonuna tıkla (en son sürümü yükle)
5. Yükleme tamamlanana kadar bekle (2-3 dakika)
6. **Close** butonuna tıkla

#### Adım 3: Board Seçimi

1. **Tools** → **Board** → **Raspberry Pi RP2040 Boards**
2. **Raspberry Pi Pico 2** seç (veya **Raspberry Pi Pico W** eğer WiFi kullanacaksan)

#### Adım 4: Port Seçimi

1. Pico'yu USB ile bilgisayara bağla
2. **Tools** → **Port** → **COMx (Raspberry Pi Pico)** seç
   - Windows: `COM3`, `COM4`, vb.
   - Eğer port görünmüyorsa, Pico'yu yeniden tak

---

### Yöntem 2: Mbed OS RP2040 Core (Alternatif)

Arduino'nun resmi Pico desteği (daha az özellik).

#### Kurulum:
1. **Tools** → **Board** → **Boards Manager...**
2. **"mbed"** ara
3. **Arduino Mbed OS RP2040 Boards** yükle
4. Board olarak **Raspberry Pi Pico** seç

**Not:** arduino-pico core daha fazla özellik sunduğu için önerilir.

---

## 📤 Kod Yükleme

### Adım 1: Sketch'i Aç

1. Arduino IDE'de: **File** → **Open**
2. `motor_control_pico.ino` dosyasını seç ve aç

### Adım 2: Board ve Port Ayarları

```
Tools → Board → Raspberry Pi RP2040 Boards → Raspberry Pi Pico 2
Tools → Port → COMx (Raspberry Pi Pico)
```

### Adım 3: Derleme (Compile)

1. **Sketch** → **Verify/Compile** (veya `Ctrl+R`)
2. Alt panelde "Done compiling" mesajını bekle
3. Hata yoksa devam et

### Adım 4: Yükleme (Upload)

**Normal Yükleme (Pico bootloader hazırsa):**
1. **Sketch** → **Upload** (veya `Ctrl+U`)
2. Alt panelde yükleme işlemini izle
3. "Done uploading" mesajını bekle

**İlk Yükleme veya BOOTSEL Modu:**
1. Pico'daki **BOOTSEL** butonuna basılı tut
2. USB kablosunu tak (veya Pico'yu resetle)
3. **RPI-RP2** adında bir sürücü görünecek
4. **Sketch** → **Upload** butonuna tıkla
5. Arduino IDE otomatik olarak kodu yükleyecek

### Adım 5: Serial Monitor

1. **Tools** → **Serial Monitor** (veya `Ctrl+Shift+M`)
2. Sağ altta baud rate'i **115200** yap
3. "Both NL & CR" seç (satır sonu karakteri)
4. Pico'nun başlangıç mesajlarını görmelisin:
   ```
   ============================================
   Hava Savunma - Pico 2 Motor Kontrol
   ============================================
   OK,PICO_READY
   ============================================
   ```

---

## 📚 Kütüphane Gereksinimleri

### Temel Kurulum (Kütüphane Gerekmez ✅)

`motor_control_pico.ino` **hiçbir harici kütüphane gerektirmez**. Sadece Arduino Core fonksiyonları kullanır:
- `pinMode()`, `digitalWrite()`, `digitalRead()`
- `Serial.begin()`, `Serial.print()`, vb.
- `millis()`, `micros()`, `delay()`

### İleri Seviye: TMC2209 UART Kontrolü (Opsiyonel)

Eğer TMC2209'u UART ile kontrol etmek istersen:

#### Önerilen Kütüphane: TMCStepper

1. **Sketch** → **Include Library** → **Manage Libraries...**
2. Arama kutusuna **"TMCStepper"** yaz
3. **TMCStepper by teemuatlut** bulun
4. **Install** butonuna tıkla

**Kullanım Örneği:**
```cpp
#include <TMCStepper.h>

#define R_SENSE 0.11f  // TMC2209 sense resistor

// X Motor TMC2209 (UART)
TMC2209Stepper tmc_x(&Serial1, R_SENSE, 0x00);  // Address: 0x00

void setup() {
  Serial1.begin(115200);  // TMC UART
  
  tmc_x.begin();
  tmc_x.toff(5);
  tmc_x.rms_current(1000);    // 1A motor akımı
  tmc_x.microsteps(16);       // 1/16 mikroadım
  tmc_x.en_spreadCycle(false); // StealthChop aktif
  tmc_x.pwm_autoscale(true);
}
```

**Bağlantı:**
```
Pico TX1 (GPIO4) → TMC2209 PDN_UART
Pico RX1 (GPIO5) → TMC2209 PDN_UART (1kΩ ile birlikte)
```

---

## 🧪 Test ve Sorun Giderme

### İlk Test: Serial Monitor

**Beklenen Çıktı:**
```
============================================
Hava Savunma - Pico 2 Motor Kontrol
============================================
Pin Konfigürasyonu:
  X Motor: STEP=2, DIR=3, MS1=4, MS2=5
  Y Motor: STEP=6, DIR=7, MS1=8, MS2=9
  Kontrol: ENABLE=10, LASER=11, E-STOP=12
--------------------------------------------
Mikroadım ayarı [B]: 1/8
OK,PICO_READY
============================================
STS,READY
```

### Manuel Komut Testi

Serial Monitor'e bu komutları yaz:

```
PING
```
**Beklenen:** `OK,PONG`

```
SPD,500,0
```
**Beklenen:** X motoru hareket etmeli

```
SPD,0,0
```
**Beklenen:** Motor durmalı

```
LZR,1
```
**Beklenen:** `OK,LASER_1` + Lazer yanmalı

```
LZR,0
```
**Beklenen:** `OK,LASER_0` + Lazer sönmeli

```
MICROSTEP,B,16
```
**Beklenen:** `Mikroadım ayarı [B]: 1/16` + `OK,MICROSTEP_B_1/16`

---

### Yaygın Sorunlar

#### Problem: Port Görünmüyor

**Çözüm:**
1. USB kablosunu kontrol et (veri transferi desteklemeli)
2. Pico'yu farklı bir USB portuna tak
3. Windows Cihaz Yöneticisi'nde kontrol et:
   - **Ports (COM & LPT)** altında "USB Serial Device (COMx)" görmeli
4. Sürücü eksikse, Arduino IDE'yi yeniden kur (USB driver seç)

#### Problem: "Compilation Error"

**Çözüm:**
1. Board seçimini kontrol et: **Raspberry Pi Pico 2**
2. Arduino-Pico core yüklü mü kontrol et
3. Sketch dosya adı `.ino` ile bitmeli
4. Kodu yeniden kopyala (karakter hatası olabilir)

#### Problem: "Upload Failed"

**Çözüm:**
1. BOOTSEL moduna geç:
   - BOOTSEL butonuna bas
   - USB'yi tak veya Pico'yu resetle
   - RPI-RP2 sürücüsü görünmeli
2. Port'u değiştir
3. "Upload Using Programmer" dene

#### Problem: Serial Monitor Boş

**Çözüm:**
1. Baud rate 115200 olmalı
2. Pico'yu resetle (USB'yi çıkar-tak)
3. Serial Monitor'ü kapat/aç
4. Farklı port dene

#### Problem: Motor Hareket Etmiyor

**Çözüm:**
1. Donanım bağlantılarını kontrol et
2. Serial Monitor'de `STS,MOVING` mesajını ara
3. ENABLE pini LOW olmalı (kod içinde ayarlı)
4. TMC2209 VM pinine güç geliyor mu kontrol et (12-24V)
5. GND ortak mı kontrol et

---

## ⚙️ Arduino IDE Ayarları (Performans)

### Optimize Edilmiş Derleyici Seçenekleri

```
Tools → CPU Speed → 150 MHz (Overclock - Standart)
Tools → Optimize → Optimize More (-O3)  (Hız için)
Tools → USB Stack → Pico SDK
Tools → Debug Port → Disabled (Performans için)
Tools → Debug Level → None
```

**Açıklamalar:**
- **CPU Speed:** 150 MHz Pico 2'nin varsayılan hızı
- **Optimize More:** Daha hızlı kod üretir
- **USB Stack:** Pico SDK daha stabil
- **Debug:** Devre dışı bırakarak RAM tasarrufu

---

## 📊 Performans Karşılaştırması

| Özellik | MicroPython | Arduino C++ |
|---------|-------------|-------------|
| Geliştirme Hızı | ⚡⚡⚡⚡⚡ | ⚡⚡⚡ |
| Çalışma Hızı | ⚡⚡⚡ | ⚡⚡⚡⚡⚡ |
| RAM Kullanımı | Yüksek | Düşük ✅ |
| Adım Frekansı | ~10 kHz | ~20 kHz ✅ |
| Kütüphane Desteği | Orta | Yüksek ✅ |
| Tanıdıklık | Orta | Yüksek ✅ |

**Sonuç:** Arduino C++ daha hızlı ve verimli, özellikle motor kontrolü için.

---

## 🔄 MicroPython'dan Geçiş

### Kod Karşılaştırması

**MicroPython:**
```python
step_x = Pin(2, Pin.OUT)
step_x.value(1)
time.sleep_us(2)
step_x.value(0)
```

**Arduino C++:**
```cpp
pinMode(STEP_X_PIN, OUTPUT);
digitalWrite(STEP_X_PIN, HIGH);
delayMicroseconds(2);
digitalWrite(STEP_X_PIN, LOW);
```

### Avantajlar

- ✅ Daha hızlı yürütme (5-10x)
- ✅ Daha az RAM kullanımı
- ✅ Daha fazla kütüphane desteği
- ✅ Arduino ekosistemiyle uyumlu
- ✅ Tanıdık syntax (Arduino Uno ile aynı)

---

## 📝 Checklist

### Kurulum
- [ ] Arduino IDE 2.x yüklendi
- [ ] arduino-pico core eklendi
- [ ] Board olarak "Raspberry Pi Pico 2" seçildi
- [ ] Port seçildi (COMx)

### Test
- [ ] Kod derlendi (No errors)
- [ ] Kod yüklendi (Upload successful)
- [ ] Serial Monitor açıldı (115200 baud)
- [ ] "OK,PICO_READY" mesajı görüldü
- [ ] PING komutu test edildi

### Donanım
- [ ] TMC2209 bağlantıları yapıldı
- [ ] Güç kaynağı bağlandı (12-24V)
- [ ] GND ortak yapıldı
- [ ] Motorlar test edildi

---

## 🎯 Sonraki Adımlar

1. ✅ Donanım bağlantılarını yap → [../PICO_WIRING.md](../pico/PICO_WIRING.md)
2. ✅ İlk testi yap → Serial Monitor ile PING
3. ✅ Motor testi yap → `SPD,500,0`
4. ✅ Python entegrasyonu → Mevcut `serial_comm.py` uyumlu
5. 🚀 UART ile TMC2209 kontrolü → TMCStepper kütüphanesi ekle

**Başarılar! 🎉**
