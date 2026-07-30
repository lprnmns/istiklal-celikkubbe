# 🎯 OPTIMAL PID AYARLARI (Pico 2 + Microstepping)

## 📊 Mevcut Ayarlar (Optimized)

```python
# config.py → PIDConfig

# X EKSENI (Yatay)
KP_X: float = 1.8   # Hızlı tepki
KI_X: float = 0.004 # Hafif integral
KD_X: float = 0.35  # Moderate dampening

# Y EKSENI (Dikey)
KP_Y: float = 1.4   # Daha hassas
KI_Y: float = 0.002 # Hafif integral
KD_Y: float = 0.25  # Moderate dampening

# Motor Output
OUTPUT_MIN: float = -2500.0
OUTPUT_MAX: float = 2500.0
MIN_MOVE_SPEED: float = 40.0
INTEGRAL_MAX: float = 15000.0
```

---

## 🔧 Sorun Giderme Rehberi

### ❌ SORUN: Motor sallantılı (titremeli) gidiyor

**Belirtiler:**
- Motor hızlı gidip-geliyor
- Pozisyon etrafında sallanıyor
- Hedefi geçip geri geliyor

**Çözüm:**
```python
# 1. KD (dampening) artır → titremesini al
KD_X: float = 0.50  # (0.35'ten 0.50'ye)
KD_Y: float = 0.35  # (0.25'ten 0.35'ye)

# 2. KI (integral) azalt → stabilize et
KI_X: float = 0.002  # (0.004'ten 0.002'ye)
KI_Y: float = 0.001  # (0.002'den 0.001'ye)

# 3. OUTPUT limiti azalt → hız sınırla
OUTPUT_MAX: float = 1500.0  # (2500'den 1500'ye)
```

---

### 🐢 SORUN: Motor çok yavaş takip ediyor

**Belirtiler:**
- Balon kaçıyor
- Hedefin gerisinde kalıyor
- Tepki gecikmiş

**Çözüm:**
```python
# 1. KP (proportional gain) artır → hızlı tepki
KP_X: float = 2.2  # (1.8'den 2.2'ye)
KP_Y: float = 1.8  # (1.4'ten 1.8'e)

# 2. KI (integral) artır → biriktirilmiş error'u düzelt
KI_X: float = 0.006  # (0.004'ten 0.006'ya)
KI_Y: float = 0.003  # (0.002'den 0.003'e)

# 3. OUTPUT limiti artır → motora daha çok güç
OUTPUT_MAX: float = 3500.0  # (2500'den 3500'ye)
```

---

### 📍 SORUN: Hedefte titremeli duruş (chatter)

**Belirtiler:**
- Hedefte ulaşıyor ama sallantılı
- Açı biraz değişince motor sırıtlıyor
- Steplar irregular

**Çözüm:**
```python
# 1. Dead zone artır → hassasiyet azalt
DEAD_ZONE: int = 20  # (15'ten 20'ye)
DEAD_ZONE_STOP: int = 8  # (5'ten 8'e)

# 2. MIN_MOVE_SPEED artır → çok küçük hareketleri engelle
MIN_MOVE_SPEED: float = 60.0  # (40'tan 60'a)

# 3. KI azalt → integral hatası az
INTEGRAL_MAX: float = 10000.0  # (15000'den 10000'e)
```

---

### 🔴 SORUN: Hedefi tamamen özletiyor (steady state error)

**Belirtiler:**
- Motor hareket ediyor ama hedefi özletiyor
- Sabit bir offset kalıyor
- Pozisyon stabil değil

**Çözüm:**
```python
# 1. KI (integral gain) artır → biriktirilmiş error'u dü­zelt
KI_X: float = 0.008  # (0.004'ten 0.008'e)
KI_Y: float = 0.004  # (0.002'den 0.004'e)

# 2. INTEGRAL_MAX artır → integralin daha da artsın
INTEGRAL_MAX: float = 20000.0  # (15000'den 20000'e)

# 3. KP hafif artır → proportional error'u azalt
KP_X: float = 2.0  # (1.8'den 2.0'ye)
```

---

## ⚡ Hızlı Profiller

### Profil 1: BALANCED (Standart - ÖNERILEN)
```python
KP_X, KP_Y = 1.8, 1.4
KI_X, KI_Y = 0.004, 0.002
KD_X, KD_Y = 0.35, 0.25
OUTPUT_MAX = 2500.0
DEAD_ZONE = 15
```

### Profil 2: AGGRESSIVE (Çok Hızlı Takip)
```python
KP_X, KP_Y = 2.3, 1.9
KI_X, KI_Y = 0.006, 0.003
KD_X, KD_Y = 0.25, 0.15
OUTPUT_MAX = 3500.0
DEAD_ZONE = 10
```

### Profil 3: SMOOTH (Titremesiz)
```python
KP_X, KP_Y = 1.4, 1.0
KI_X, KI_Y = 0.002, 0.001
KD_X, KD_Y = 0.50, 0.40
OUTPUT_MAX = 1500.0
DEAD_ZONE = 20
```

### Profil 4: RESPONSIVE (Duyarlı - Hızlı Reaksiyon)
```python
KP_X, KP_Y = 2.0, 1.6
KI_X, KI_Y = 0.005, 0.0025
KD_X, KD_Y = 0.30, 0.20
OUTPUT_MAX = 2800.0
DEAD_ZONE = 12
```

---

## 📈 PID Tuning Adımları (Sistematik)

1. **Başla:** Balanced profile ile
2. **Test et:** `python main.py` - Hareketleri gözle
3. **Gözlem yap:**
   - Sallantılı mı? → KD artır
   - Yavaş mı? → KP artır
   - Offset var mı? → KI artır
4. **Tek bir değer değiştir** - birden fazla değil!
5. **Etkisini gözle** - En az 5 saniye test et
6. **İteratif iyileştir** - Yavaş yavaş adım adım

---

## 🎮 Test Komutu

```bash
# Önce tuning test dosyasını çalıştır
python donanim_test.py

# X motoru hızlı hareketi test et
SPD,500,0   # X'i 500 hız ile hareket ettir

# Y motoru hızlı hareketi test et  
SPD,0,100   # Y'i 100 hız ile hareket ettir

# İkisini beraber test et
SPD,300,80  # Diagonal hareket
```

---

## 💡 PID Temel Bilgiler

| Parametr | Amacı | Etkisi | Artırıldığında |
|----------|-------|--------|-----------------|
| **KP** | Doğrudan error düzeltme | Hızlı tepki | Sallantı artar |
| **KI** | Biriktirilmiş error'u düzeltme | Offset'i kaldırır | Dengesizlik |
| **KD** | Hız farkını kontrol etme | Titremesini alır | Tepki yavaşlar |

**Golden Rule:**
- Titreme var → **KD artır**
- Yavaş takip → **KP artır**
- Offset → **KI artır**

---

## ✅ Final Checklist

- [ ] Motor süzüldü mü? (İşitsel test)
- [ ] Hedefi yakalayor mı?
- [ ] Hedeftin gerisinde kalıyor mu?
- [ ] Titremeli duruşu var mı?
- [ ] Acil duruş çalışıyor mu?
- [ ] Lazer tetikler mi?

Hepsi "Evet" ise → **sistem optimal!** 🎉
