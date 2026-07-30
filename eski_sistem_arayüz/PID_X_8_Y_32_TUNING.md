# 🎯 X: 1/8 Microstepping vs Y: 1/32 Microstepping Ayarları

## 📊 Mevcut Durum

```
X Ekseni (Yatay): 1/8 Microstepping (8)
- Steps/Rev: 200 * 8 = 1600
- Gear Ratio: 10.0 (dişlili motor)
- Steps/Degree: 44.44

Y Ekseni (Dikey): 1/32 Microstepping (32) 
- Steps/Rev: 200 * 32 = 6400
- Gear Ratio: 2.0 (basit)
- Steps/Degree: 35.56
```

## ⚡ PID Ayarları (OPTIMIZED for X:1/8, Y:1/32)

```python
# X EKSENI (1/8 Microstepping - Normal)
KP_X: 2.1   # Yavaş takıp düzeltildi
KI_X: 0.004 # Pozisyon tutma
KD_X: 0.45  # Overshoot kontrol

# Y EKSENI (1/32 Microstepping - 4x Hassas!)
KP_Y: 2.2   # Hızlı tepki (hassas motor)
KI_Y: 0.005 # Daha agresif integral
KD_Y: 0.50  # Overshoot kontrol (önemli)

# Motor Output
OUTPUT: ±3000 (Daha güçlü takip)
MIN_MOVE_SPEED: 35 (Hassas hareket)
INTEGRAL_MAX: 18000 (Daha agresif)
```

---

## 🔍 Neden Ayrı Ayarlar?

| Parametre | X (1/8) | Y (1/32) | Fark |
|-----------|---------|----------|------|
| **Microstepping** | 1/8 | 1/32 | Y 4x hassas |
| **Steps/Rev** | 1600 | 6400 | Y 4x çok adım |
| **Resolution** | Orta | Çok İyi | Y daha hassas |
| **Control Difficulty** | Normal | Zor | Y daha dinamik |
| **Overshoot Risk** | Orta | YÜKSEK | Y için KD önemli! |

---

## 🚀 Yapılan Düzeltmeler

### ✅ Problem 1: Yavaş Takip
```
Sebeip: KP_X çok düşük (1.8)
Çözüm: KP_X = 2.1 (+16%)
Sonuç: Hızlı takip, balon kaçması azalır
```

### ✅ Problem 2: Overshoot (Hedefi Geçme)
```
Sebeip: KD çok düşük
Çözüm: 
  - KD_X = 0.45 (+29%)
  - KD_Y = 0.50 (+100%!) ← Y çok hassas!
Sonuç: Titreme yok, kontrollü hareket
```

### ✅ Problem 3: Tekrar Kaçırma (Ortalarken)
```
Sebeip: KI (integral) birikmesi eksik
Çözüm:
  - KI_X = 0.004 (normal)
  - KI_Y = 0.005 (+150%) ← Y hassas olduğu için
  - INTEGRAL_MAX = 18000 (+20%)
Sonuç: Pozisyon tutma daha stabil
```

---

## 📈 Test Adımları

```bash
# 1. Sistemi başlat
python main.py

# 2. X eksenini test et
# - Balon sağa taşı → Motor takip etmeli
# - Overshoot olmadan geçmeli
# - Durduktan sonra sallanmamalı

# 3. Y eksenini test et  
# - Balon yukarı/aşağı → Hızlı takip
# - Overshoot az (Y daha hassas!)
# - Yumuşak durdurma

# 4. Diagonal hareket
# - Balon diyagonalde → İkisi beraber
# - Senkronize hareket
# - Takip kaçmıyor
```

---

## 🔧 İnce Tuning (Eğer Gerekirse)

### Hala Yavaş Takip?
```python
KP_X: float = 2.3  # (2.1'den 2.3'e)
KP_Y: float = 2.4  # (2.2'den 2.4'e)
```

### Hala Overshoot?
```python
KD_X: float = 0.60  # (0.45'ten 0.60'a)
KD_Y: float = 0.65  # (0.50'den 0.65'e)
```

### Chatter (Titreme)?
```python
DEAD_ZONE: int = 20  # (15'ten 20'ye)
DEAD_ZONE_STOP: int = 8  # (5'ten 8'e)
```

### Yine Kaçırıyor?
```python
KI_X: float = 0.006  # (0.004'ten 0.006'ya)
KI_Y: float = 0.007  # (0.005'ten 0.007'e)
INTEGRAL_MAX: float = 20000  # (18000'den 20000'e)
```

---

## ⚠️ Uyarılar

1. **Y 4x Hassas** → Overshoot riski yüksek
   - KD_Y'yi çok düşük tutma!
   - KP_Y'yi çok yüksek tutma!

2. **Ayrı Microstepping** → Asimetrik hareket
   - X yavaş gidebilir vs Y hızlı
   - Diagonal hareketler check et!

3. **CNC Shield Jumper Kontrol**
   - X Jumper: MS1=HIGH, MS2=HIGH, MS3=LOW (1/8)
   - Y Jumper: MS1=HIGH, MS2=HIGH, MS3=HIGH (1/32)

---

## ✅ Final Checklist

- [ ] X ekseni yavaş takıp yapıyor mu? ✓
- [ ] Y ekseni hızlı takıp yapıyor mu? ✓
- [ ] Overshoot yok mu? ✓
- [ ] Ortalarken kaçmıyor mu? ✓
- [ ] Titreme (chatter) yok mu? ✓
- [ ] Lazer tetikliyor mu? ✓

Hepsi check edildi ise → **Sistem Optimal!** 🎉
