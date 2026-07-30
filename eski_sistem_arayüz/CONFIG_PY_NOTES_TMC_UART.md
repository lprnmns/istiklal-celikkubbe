# 📝 config.py İçin Notlar - TMC2209 UART

## ⚠️ ÖNEMLİ: Config.py DEĞİŞTİRMEYİN!

TMC2209 UART ile **interpolasyon** kullanıldığında, mikroadım ayarı **TMC2209 içinde** yapılır.  
Python tarafındaki `config.py` **fiziksel mikroadım değerlerini** saklar.

---

## 🔍 Mevcut Durum (config.py)

```python
MICROSTEPPING_MODE_X: int = 8   # X: 1/8 mikroadım
MICROSTEPPING_MODE_Y: int = 32  # Y: 1/32 mikroadım
```

---

## ✅ TMC2209 UART Optimizasyonu Sonrası

### X Ekseni (Speed Mod)
```
Fiziksel: 1/8 (config.py'de 8)
TMC2209 interpolasyon: 256
Sonuç: 1/8 hızında 256 hassasiyet!
```

**config.py değişiklik**: ❌ GEREKMEZ!

### Y Ekseni (Precision Mod)
```
ÖNCESİ:
  Fiziksel: 1/32 (config.py'de 32)
  Interpolasyon: YOK
  Sonuç: Çok yavaş!

SONRASI (Önerilen):
  Fiziksel: 1/16 (config.py'de 16) ← DEĞİŞ!
  TMC2209 interpolasyon: 256
  Sonuç: 2x daha hızlı, aynı hassasiyet!
```

**config.py değişiklik**: ✅ Y eksenini 32'den 16'ya düşür!

---

## 🛠️ Önerilen config.py Değişikliği

### Seçenek 1: Sadece Y Eksenini Hızlandır (Önerilen)

```python
# config.py

@dataclass
class HardwareConfig:
    MICROSTEPPING_MODE_X: int = 8   # ✅ AYNEN KALSIN (1/8 + interp)
    MICROSTEPPING_MODE_Y: int = 16  # ⚡ DEĞİŞTİR (32 → 16)
    
    # Geri kalan hesaplamalar otomatik:
    ACTUAL_STEPS_PER_REV_X: float = 200 * 8   # = 1600
    ACTUAL_STEPS_PER_REV_Y: float = 200 * 16  # = 3200 (önceden 6400)
    
    X_STEPS_PER_DEG: float = (1600 * 10.0) / 360  # = 44.44
    Y_STEPS_PER_DEG: float = (3200 * 2.0) / 360   # = 17.78 (önceden 35.56)
```

**KAZANIM**:
- Y ekseni **2x daha hızlı**
- Hassasiyet **aynı** (256 interpolasyon sayesinde)
- X ekseni **değişmedi**

---

### Seçenek 2: Her İkisini de Optimize Et (Maksimum Hız)

```python
# config.py

@dataclass
class HardwareConfig:
    MICROSTEPPING_MODE_X: int = 4   # ⚡ 1/4 + interp (ultra hızlı!)
    MICROSTEPPING_MODE_Y: int = 8   # ⚡ 1/8 + interp (çok hızlı!)
    
    # Hesaplamalar:
    ACTUAL_STEPS_PER_REV_X: float = 200 * 4   # = 800
    ACTUAL_STEPS_PER_REV_Y: float = 200 * 8   # = 1600
    
    X_STEPS_PER_DEG: float = (800 * 10.0) / 360   # = 22.22
    Y_STEPS_PER_DEG: float = (1600 * 2.0) / 360   # = 8.89
```

**KAZANIM**:
- X ekseni **2x daha hızlı**
- Y ekseni **4x daha hızlı**
- Hassasiyet **aynı** (256 interpolasyon)

**RİSK**: Çok hızlı olabilir, kontrol kaybı riski var!

---

## 🎯 HANGİSİNİ SEÇMELİYİM?

### Eğer şu anda sistem YAVAŞ ise:
👉 **Seçenek 1** (sadece Y'yi 32→16)

### Eğer sistem ÇOK YAVAŞ ve atik olmalı ise:
👉 **Seçenek 2** (X: 4, Y: 8)

### Eğer sistem YETERINCE HIZLI ise:
👉 **Hiçbir değişiklik yapma!** Sadece TMC2209 interpolasyon + optimizasyon yeterli.

---

## 🔄 Değişiklikleri Uygulama

### Adım 1: config.py'yi güncelle

```python
# python/config.py

MICROSTEPPING_MODE_X: int = 8   # veya 4
MICROSTEPPING_MODE_Y: int = 16  # veya 8 (önceden 32)
```

### Adım 2: Pico kodunu güncelle

```python
# pico/motor_control_pico_v2_tmc_uart.py içinde:

# X Motor
if TMC_MODE_X == 'speed':
    tmc_x.set_microstepping_with_interpolation(TMC2209Advanced.MRES_8, True)
    # veya MRES_4 (daha hızlı)

# Y Motor
if TMC_MODE_Y == 'precision':
    tmc_y.set_microstepping_with_interpolation(TMC2209Advanced.MRES_16, True)
    # veya MRES_8 (daha hızlı)
```

**DİKKAT**: MRES değeri config.py ile **eşleşmeli**!

```
config.py: MICROSTEPPING_MODE_X = 8  ↔  tmc_x: MRES_8
config.py: MICROSTEPPING_MODE_Y = 16 ↔  tmc_y: MRES_16
```

---

## ⚡ ÖRNEK: Y EKSENİNİ 32'DEN 16'YA DÜŞÜRME

### 1. config.py'yi güncelle:

```python
# ÖNCESİ:
MICROSTEPPING_MODE_Y: int = 32

# SONRASI:
MICROSTEPPING_MODE_Y: int = 16
```

### 2. Pico'daki tmc2209_advanced.py zaten doğru:

```python
# init_for_precision() fonksiyonu içinde:
self.set_microstepping_with_interpolation(self.MRES_32, interpolate=True)

# ↓ DEĞIŞTIR:
self.set_microstepping_with_interpolation(self.MRES_16, interpolate=True)
```

**VEYA** motor_control_pico_v2_tmc_uart.py içinde manuel ayarla:

```python
# Y Motor başlatma bölümünde:
if TMC_MODE_Y == 'precision':
    # Özel ayar: 1/16 + interpolasyon
    tmc_y.set_current_advanced(run_current=1000, hold_current=300, hold_delay=2)
    tmc_y.set_microstepping_with_interpolation(tmc_y.MRES_16, interpolate=True)  # 32 yerine 16!
    tmc_y.configure_hybrid_mode(threshold_rpm=80)
    tmc_y.enable_coolstep(min_current=1, max_current=0, step_down=2, step_up=1)
    tmc_y.optimize_chopper(mode='balanced')
    tmc_y.set_standstill_mode(delay=2)
```

### 3. Test et:

```bash
# Python'dan:
python main.py

# Gözlem:
# - Y ekseni 2x daha hızlı hareket etmeli
# - Hassasiyet aynı kalmalı (256 interp sayesinde)
# - FPS artmalı
```

---

## 📊 HESAPLAMA ÖRNEĞİ

### Örnek: Y ekseni için 1° hareket

#### ÖNCESİ (1/32, interpolasyon YOK):
```
Y_STEPS_PER_DEG = (200 * 32 * 2.0) / 360 = 35.56 adım/derece
1° hareket = 35.56 adım
Süre: ~35.56 * MIN_STEP_DELAY_US = ~1.78 ms
```

#### SONRASI (1/16, 256 interpolasyon):
```
Fiziksel: Y_STEPS_PER_DEG = (200 * 16 * 2.0) / 360 = 17.78 adım/derece
1° hareket = 17.78 adım (fiziksel)
Süre: ~17.78 * MIN_STEP_DELAY_US = ~0.89 ms

Hassasiyet: TMC2209 içinde 17.78 → 256 interp = 35.56 eşdeğer hassasiyet!
```

**SONUÇ**: **2x daha hızlı**, hassasiyet aynı! ✅

---

## 🔍 SORUN GİDERME

### Problem: config.py değiştirdim ama hız değişmedi

**Neden**: Pico'daki TMC2209 ayarları hala eski!

**Çözüm**: `motor_control_pico_v2_tmc_uart.py` içinde MRES değerini güncelle.

### Problem: Hassasiyet kayboldu

**Neden**: Interpolasyon kapalı!

**Kontrol**:
```python
chopconf = tmc_y.read_register(0x6C)
if chopconf & (1 << 28):
    print("Interpolasyon: AÇIK ✅")
else:
    print("Interpolasyon: KAPALI ❌")
```

### Problem: Motor adımları kaba

**Neden**: Mikroadım çok düşük (1/4) veya interpolasyon kapalı

**Çözüm**: 1/8 veya 1/16 kullan, interpolasyonu aç.

---

## ✅ KONTROL LİSTESİ

Değişiklik yaptıktan sonra kontrol et:

- [ ] config.py'de MICROSTEPPING_MODE_Y = 16 (veya yeni değer)
- [ ] Pico'daki tmc2209_advanced.py yeni MRES değeri ile güncellenmiş
- [ ] Interpolasyon AÇIK (bit 28 = 1)
- [ ] Motor hızı belirgin şekilde arttı
- [ ] Hassasiyet aynı kaldı (hedef takip kalitesi)
- [ ] PID ayarları hala çalışıyor

---

## 📝 ÖZET

| Değişiklik | config.py | Pico (TMC) | Sonuç |
|------------|-----------|------------|-------|
| **Y: 32→16** | `MODE_Y = 16` | `MRES_16 + interp` | 2x hız, aynı hassasiyet ✅ |
| **Y: 32→8** | `MODE_Y = 8` | `MRES_8 + interp` | 4x hız, aynı hassasiyet ⚡ |
| **X: 8→4** | `MODE_X = 4` | `MRES_4 + interp` | 2x hız, aynı hassasiyet ⚡ |

**EN ÖNEMLİ**: İki değer eşleşmeli:
```
config.py: MICROSTEPPING_MODE = N
Pico: MRES_N + interpolation
```

---

**Sonuç**: Interpolasyon sayesinde **düşük mikroadım = yüksek hız**, ama **hassasiyet kaybolmaz**! 🚀
