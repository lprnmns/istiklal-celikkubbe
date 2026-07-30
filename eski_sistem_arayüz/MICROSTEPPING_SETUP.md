# 🔧 Microstepping Ayarları ve Kod İlişkisi

## 📌 Jumper'ları Ayarladığında Kod Nasıl Değişmesi Gerekiyor?

### 1️⃣ Adım 1: CNC Shield'deki Fiziksel Jumper'ları Ayarla

MS1, MS2, MS3 jumper'larını aşağıdaki kombinasyonlardan birine göre ayarla:

```
┌─────────────┬──────┬──────┬──────┬──────────┬──────────┐
│ Mode        │ MS1  │ MS2  │ MS3  │ Hız      │ Hassas.  │
├─────────────┼──────┼──────┼──────┼──────────┼──────────┤
│ Full Step   │ LOW  │ LOW  │ LOW  │ 🔥 Hızlı | ⚠️ Az    │
│ Half Step   │ HIGH │ LOW  │ LOW  │ 🔄 Orta  │ ✓ Orta   │
│ Quarter     │ LOW  │ HIGH │ LOW  │ 🔄 Yavaş │ ✓✓ İyi  │
│ Eighth ⭐   │ HIGH │ HIGH │ LOW  │ 🔄 Yavaş │ ✓✓✓ Best │
│ Sixteenth   │ LOW  │ LOW  │ HIGH │ 🚀 Çok Y │ ✓✓✓✓ Max │
└─────────────┴──────┴──────┴──────┴──────────┴──────────┘
```

---

### 2️⃣ Adım 2: config.py'deki MICROSTEPPING_MODE'u Güncelle

Seçilen jumper kombinasyonuna göre `config.py`'de güncelle:

```python
# config.py → HardwareConfig

MICROSTEPPING_MODE: int = 8  # ← BURASI GÜNCELLENECEK!
```

**Değer Tablosu:**
| Jumper Ayarı | MICROSTEPPING_MODE | Açıklama |
|--------------|-------------------|----------|
| MS1=L, MS2=L, MS3=L | 1 | Full Step (200 step/rev) |
| MS1=H, MS2=L, MS3=L | 2 | Half Step (400 step/rev) |
| MS1=L, MS2=H, MS3=L | 4 | Quarter Step (800 step/rev) |
| MS1=H, MS2=H, MS3=L | 8 | Eighth Step (1600 step/rev) ⭐ |
| MS1=L, MS2=L, MS3=H | 16 | Sixteenth Step (3200 step/rev) |

---

### 3️⃣ Kodda Otomatik Olarak Değişen Değerler

config.py'de MICROSTEPPING_MODE'u güncellediğinde, aşağıdakiler **otomatik hesaplanır:**

```python
# config.py (otomatik hesaplama)

STEPS_PER_REV: int = 200  # Motor baseband (değişmez)
MICROSTEPPING_MODE: int = 8  # ← SEN BURAYA GÜNCELLEDİN

# Otomatik hesaplanan:
ACTUAL_STEPS_PER_REV: float = STEPS_PER_REV * MICROSTEPPING_MODE
# Örnek: 200 * 8 = 1600 step/rev

X_STEPS_PER_DEG: float = (ACTUAL_STEPS_PER_REV * X_GEAR_RATIO) / 360
# Örnek: (1600 * 10.0) / 360 = 44.44 step/derece

Y_STEPS_PER_DEG: float = (ACTUAL_STEPS_PER_REG * Y_GEAR_RATIO) / 360
# Örnek: (1600 * 2.0) / 360 = 8.88 step/derece
```

Bu değerler **motor kontrolü ve pozisyon hesaplamalarında** otomatik olarak kullanılır! ✅

---

## 📊 Örnek Senaryo

### Senaryo: Jumper'ı 1/8'den 1/16'ya değiştir

**CNC Shield Fiziksel:**
```
Eski: MS1=HIGH, MS2=HIGH, MS3=LOW (1/8)
Yeni: MS1=LOW,  MS2=LOW,  MS3=HIGH (1/16)
      ↑ Jumper'ı buraya taşı
```

**Python Kod Değişiklikleri:**
```python
# config.py

# ESKI
MICROSTEPPING_MODE: int = 8
ACTUAL_STEPS_PER_REV: float = 200 * 8 = 1600

# YENİ
MICROSTEPPING_MODE: int = 16  # ← SADECE BURASI DEĞİŞ!
ACTUAL_STEPS_PER_REV: float = 200 * 16 = 3200  # ← OTOMATIK HESAPLI
X_STEPS_PER_DEG: float = 88.88  # ← OTOMATIK HESAPLI (önceden 44.44)
Y_STEPS_PER_DEG: float = 17.77  # ← OTOMATIK HESAPLI (önceden 8.88)
```

**Sonuç:** Motor artık 2x daha hassas hareket edecek, ama 2x daha yavaş! 🐢

---

## ⚡ Hangisini Seçmeliyim?

| Durum | Mode | Jumper Konumu |
|-------|------|---------------|
| **Hızlı Takip** | 1 (Full) | MS1=L, MS2=L, MS3=L |
| **Dengeli** | 2-4 (Half/Quarter) | MS1=H, MS2=L, MS3=L veya MS1=L, MS2=H, MS3=L |
| **Standart (ÖNERILEN)** | **8 (Eighth)** | **MS1=H, MS2=H, MS3=L** |
| **Çok Hassas** | 16 (Sixteenth) | MS1=L, MS2=L, MS3=H |

**Başlangıç için: 1/8 Microstepping (Mode=8)** ⭐

---

## 🔍 Kodda Kullanılan Yerler

Bu hesaplanan değerler şu yerlerde otomatik olarak kullanılır:

1. **safety_manager.py** - Açı hesaplamalarında
2. **pid_controller.py** - Motor hız kontrol hesaplamalarında
3. **main.py** - Kalman filtrede pozisyon tahminine
4. **serial_comm.py** - Pico 2'ye gönderilen motor komutlarında

**Hepsi otomatik olarak config.py'deki değerleri kullanır!** ✅

---

## 🚀 Hızlı Kurulum

1. **CNC Shield'deki jumper'ları fiziksel olarak ayarla**
2. **config.py'de bu satırı güncelle:**
   ```python
   MICROSTEPPING_MODE: int = 8  # İstediğin mode (1, 2, 4, 8 veya 16)
   ```
3. **Python kodunu çalıştır - otomatik olarak yeni hesaplamalarla çalışacak!** ✅

Başka bir yerde kod değişikliği gerekmez! 🎉
