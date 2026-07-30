# 🚀 TMC2209 UART Hızlı Başlangıç Rehberi

## 📋 İHTİYAÇLAR

1. ✅ Raspberry Pi Pico 2
2. ✅ TMC2209 sürücüler (UART destekli)
3. ✅ Bağlantı kabloları
4. ✅ Güncellenmiş kod dosyaları

---

## 🔌 DONANIM BAĞLANTILARI

### TMC2209 UART Bağlantısı

```
┌─────────────────────────────────────────┐
│  Raspberry Pi Pico 2  →  TMC2209       │
├─────────────────────────────────────────┤
│  GPIO4 (TX - UART1)   →  PDN_UART (RX) │
│  GPIO5 (RX - UART1)   →  PDN_UART (TX) │  ← DİKKAT: Tek pin!
│  GND                  →  GND            │
└─────────────────────────────────────────┘
```

**ÖNEMLİ**: TMC2209'da PDN_UART pini hem RX hem TX işlevi görür!

### Adres Ayarları (İki Ayrı Sürücü Varsa)

```
X Motor TMC2209:  MS1_AD0 = LOW,  MS2_AD1 = LOW  → Adres 0x00
Y Motor TMC2209:  MS1_AD0 = HIGH, MS2_AD1 = LOW  → Adres 0x01
```

---

## 📁 DOSYA YAPISI

```
pico/
├── tmc2209_advanced.py              ← YENİ! Gelişmiş TMC kontrol
├── motor_control_pico_v2_tmc_uart.py ← YENİ! UART destekli motor kontrol
├── motor_control_pico.py            ← ESKİ (yedek)
└── tmc2209_uart.py                  ← ESKİ (temel, yedek)
```

---

## ⚙️ KURULUM ADIMLARI

### Adım 1: Dosyaları Pico'ya Yükle

```bash
# Thonny IDE veya rshell kullanarak:
1. tmc2209_advanced.py → Pico'ya yükle
2. motor_control_pico_v2_tmc_uart.py → Pico'ya yükle
3. main.py olarak yeniden adlandır (opsiyonel)
```

### Adım 2: Konfigürasyonu Ayarla

`motor_control_pico_v2_tmc_uart.py` dosyasını aç:

```python
# 🔧 BURADAN AYARLA:

# X Ekseni için mod seç
TMC_MODE_X = 'speed'       # Seçenekler: 'speed', 'precision', 'balanced'

# Y Ekseni için mod seç
TMC_MODE_Y = 'precision'   # Seçenekler: 'speed', 'precision', 'balanced'

# İki ayrı sürücü varsa:
TMC_ADDR_X = 0x00   # X motor adresi
TMC_ADDR_Y = 0x01   # Y motor adresi (farklı olmalı!)

# Tek sürücü varsa (her iki motor aynı TMC2209'a bağlı):
TMC_ADDR_X = 0x00
TMC_ADDR_Y = 0x00   # Aynı adres
```

### Adım 3: Test Et

```python
# Pico üzerinde çalıştır:
python motor_control_pico_v2_tmc_uart.py
```

**Beklenen Çıktı**:
```
============================================================
 TMC2209 UART BAŞLATILIYOR
============================================================

🔧 X Motoru yapılandırılıyor...

🚀 X Ekseni: HIZ MOD

⚡ Akım: RUN=1400mA, HOLD=400mA, DELAY=1
🎯 Mikroadım: 1/8 → 256 interp
🔄 Hybrid mod: 0 RPM'de SpreadCycle'a geçiş
❄️ CoolStep aktif: MIN=2, MAX=0
⚙️ Chopper: speed (TOFF=3, HSTRT=7, HEND=0)
⏱️ Standstill delay: 1
✅ HIZ modu aktif!

📊 X Motoru:
  Mode: SpreadCycle
  Standstill: False
  Actual Current: 28/31
  Overtemp: False (Warning: False)

============================================================
✅ TMC2209 başlatma tamamlandı!
============================================================

📌 PIN KONFIGÜRASYONU:
  X Motor: STEP=2, DIR=3
  Y Motor: STEP=6, DIR=7
  Kontrol: ENABLE=10, LASER=11, E-STOP=12
  UART0: TX=0, RX=1, Baudrate=115200
  UART1 (TMC): TX=4, RX=5, Baudrate=115200
  TMC Mode: X=speed, Y=precision

✅ Sistem hazır!
```

---

## 🧪 TEST KOMUTLARI

### Python tarafından gönderilecek komutlar:

```python
# Motor hız kontrolü (aynı)
"SPD,500,300\n"     # X: 500, Y: 300

# Lazer kontrolü (aynı)
"LZR,1\n"           # Lazer aç
"LZR,0\n"           # Lazer kapat

# Ping test (aynı)
"PING\n"            # → "OK,PONG\n"

# YENİ: TMC2209 durum kontrolü
"TMC_STATUS\n"      # → "TMC_X,SpreadCycle,28\n"

# YENİ: Akım değiştir
"TMC_CURRENT,1000\n"  # → 1000mA'ya düşür
"TMC_CURRENT,1600\n"  # → 1600mA'ya çıkar
```

---

## 📊 MOD KARŞILAŞTIRMASI

### Speed Mod (X Ekseni Önerilen)
```
✅ 1/8 mikroadım → 256 interpolasyon
✅ Her zaman SpreadCycle (maksimum güç)
✅ 1400mA akım (güçlü)
✅ Agresif CoolStep
✅ Speed-optimized chopper
```

**SONUÇ**: En hızlı, en atik, yüksek güç

### Precision Mod (Y Ekseni Önerilen)
```
✅ 1/32 mikroadım → 256 interpolasyon
✅ Hybrid mod (80 RPM'de geçiş)
✅ 1000mA akım (dengeli)
✅ Normal CoolStep
✅ Balanced chopper
```

**SONUÇ**: Hassas, hala hızlı, dengeli

### Balanced Mod (Her İkisi)
```
✅ 1/16 mikroadım → 256 interpolasyon
✅ Hybrid mod (100 RPM'de geçiş)
✅ 1200mA akım
✅ Normal CoolStep
✅ Balanced chopper
```

**SONUÇ**: Her şey dengeli

---

## 🔍 SORUN GİDERME

### Problem 1: "TMC2209 Advanced modülü bulunamadı"

**Çözüm**: `tmc2209_advanced.py` dosyasını Pico'ya yüklediniz mi?

```bash
# Thonny'de:
File → Save to Micropython device → tmc2209_advanced.py
```

### Problem 2: "TMC2209 başlatma hatası"

**Kontrol listesi**:
1. UART bağlantıları doğru mu? (GPIO4↔PDN_UART, GPIO5↔PDN_UART)
2. PDN_UART pini pull-up direnci ile VCC'ye bağlı mı? (10kΩ)
3. TMC2209'a güç geliyor mu?
4. Baudrate doğru mu? (115200)

### Problem 3: Motorlar hareket etmiyor

**Kontrol listesi**:
1. ENABLE pini LOW mu? (Motorlar aktif)
2. STEP/DIR bağlantıları doğru mu?
3. Motor güç kaynağı bağlı mı?
4. `SPD,500,0\n` komutu gönderildi mi?

### Problem 4: TMC_STATUS yanıt vermiyor

**Neden**: UART iletişimi yok  
**Çözüm**:
```python
# tmc2209_advanced.py içinde test et:
tmc_x = TMC2209Advanced(1, 4, 5, 0x00)
status = tmc_x.get_status()
print(status)
# None geliyorsa → UART bağlantısı hatalı
```

### Problem 5: Interpolasyon çalışmıyor mu?

**Kontrol**:
```python
chopconf = tmc_x.read_register(tmc_x.REG_CHOPCONF)
print(f"CHOPCONF: 0x{chopconf:08X}")
# Bit 28 kontrol et:
if chopconf & (1 << 28):
    print("✅ Interpolasyon aktif")
else:
    print("❌ Interpolasyon kapalı")
```

---

## 📈 PERFORMANS İYİLEŞTİRME İPUÇLARI

### 1. X Ekseni Çok Yavaş mı?

```python
# motor_control_pico_v2_tmc_uart.py içinde:
MIN_STEP_DELAY_US = 40  # 50'den 40'a düşür (daha hızlı)

# VEYA TMC2209 akımını artır:
# Python serial'den:
"TMC_CURRENT,1600\n"  # 1400'den 1600'e çıkar
```

### 2. Y Ekseni Daha Hassas Olmalı mı?

```python
# Y için precision yerine 1/64 kullan:
# tmc2209_advanced.py içinde:
tmc_y.set_microstepping_with_interpolation(tmc_y.MRES_64, True)
```

### 3. Motorlar Çok Isınıyor mu?

```python
# CoolStep'i daha agresif yap:
tmc_x.enable_coolstep(min_current=3, max_current=0, step_down=1, step_up=2)

# VEYA akımı düşür:
"TMC_CURRENT,1000\n"
```

### 4. Daha Yumuşak Hareket İstiyor musun?

```python
# Chopper'ı balanced'a çek:
# motor_control_pico_v2_tmc_uart.py içinde:
TMC_MODE_X = 'balanced'  # speed yerine
```

---

## ✅ BAŞARILI KURULUM KONTROLÜ

Aşağıdaki testleri sırayla yapın:

1. ✅ Pico boot'lanınca "TMC2209 başlatma tamamlandı!" görüyorum
2. ✅ `TMC_STATUS` komutu yanıt veriyor
3. ✅ `SPD,500,0` komutu X motorunu hareket ettiriyor
4. ✅ Motor hareketi eskisinden belirgin şekilde daha hızlı
5. ✅ Motorlar eskisinden daha yumuşak hareket ediyor
6. ✅ `tmc_x.print_status()` ile "SpreadCycle" görüyorum

**HEPSI ✅ İSE**: Tebrikler! TMC2209 UART optimizasyonu aktif! 🎉

---

## 🎯 SONRAKI ADIMLAR

1. **Python tarafını güncelle**: `config.py` değişiklik GEREKMEZ! (Interpolasyon TMC'de)

2. **Serial komutları test et**:
   ```python
   # Python'da:
   ser.write(b"TMC_STATUS\n")
   print(ser.readline())  # → TMC_X,SpreadCycle,28
   ```

3. **Performansı ölç**:
   - Hedef takip hızı
   - Kaçırılan hedefler
   - Motor sıcaklığı

4. **İnce ayar yap**:
   - Akım ayarla
   - Mod değiştir (speed ↔ balanced)
   - CoolStep hassasiyeti

---

## 📞 DESTEK

Sorun yaşıyorsanız:

1. `TMC_STATUS` komutunu deneyin → TMC UART çalışıyor mu?
2. `tmc_x.print_status()` çıktısını paylaşın
3. CHOPCONF kaydını okuyun: `tmc_x.read_register(0x6C)`
4. Serial monitörde hata mesajı var mı?

---

**Hazırlayan**: GitHub Copilot  
**Sürüm**: 2.0 (TMC2209 UART)  
**Tarih**: 18 Ocak 2026
