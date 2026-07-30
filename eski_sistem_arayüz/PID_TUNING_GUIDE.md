# PID TUNING REHBERI - Salınım ve Takip Sorunları

## 🎯 Sorun Tanısı
- ❌ Hedef kaçıyor (çok hızlı hareket ettikten sonra takibi kesiyor)
- ❌ Salınım yapıyor (oscillation - ileri geri sallantı)
- ❌ Hedefi tutamıyor, stabil konuma gelemedigi

## ✅ Uygulanan Çözümler

### 1. **PID Kazançları Optimize Edildi**
```
❌ Eski (AGGRESSIVE):           ✅ Yeni (STABLE):
KP_X: 2.5  →                    KP_X: 1.2  (↓50%)
KD_X: 0.35 →                    KD_X: 0.8  (↑2.3x) ⭐ KRİTİK
```

**Neden:**
- **KP çok yüksek** = motor çok hızlı tepki verir → overshoot → salınım
- **KD düşük** = türev term salınımı damp edemez
- **Çözüm:** KP düşür, KD çok artır (damping)

### 2. **Output Limitlari Kontrol Edildi**
```
OUTPUT_MAX: 30000 → 8000  (↓73%)
```
Motorun aşırı hızlı hareket etmesini engelle.

### 3. **Minimum Hız Eşiği Artırıldı**
```
MIN_MOVE_SPEED: 35 → 120  (↑3.4x)
```
Çok düşük hızlarda motor jitter yapıyor (tik-tak titreşimi). Bunun altındaki hızları yoksay.

### 4. **Exponential Smoothing Düşürüldü**
```python
alpha: 0.5 → 0.3  (daha yavaş değişim)
```
Her frame'de kontrolü daha yumuşak yapar, ani değişimleri azaltır.

### 5. **Integral Anti-Windup Güçlendirildi**
```
KI_X: 0.001 → 0.0005  (↓50%)
KI_Y: 0.001 → 0.0003  (↓70%)
INTEGRAL_MAX: 25000 → 3000  (↓88%)
```
Integrator accumulator'ü kontrolde tutarak sürükleme (lag) önle.

### 6. **Hedef Kalıcılığı Eklendi** (main.py)
Frame'de tespit kaybı olursa eski hedef 5 frame tutulur:
- Glare / motion blur geçici sorunlarını çözer
- Tracking'i kesintisiz tutun

---

## 🎮 TEST ETME

### Hızlı Test
```bash
python pid_tuner.py --preset stable
python pid_tuner.py --preset balanced  
python pid_tuner.py --preset aggressive
python pid_tuner.py --compare
```

### Manuel Fine-Tuning
```bash
python pid_tuner.py --kp-x 1.5 --kd-x 1.0
```

---

## 🔧 Manual Tuning (GUI'de Canlı Ayar)

Eğer hala sorun varsa, adım adım:

1. **Salınım çok fazla?**
   ```
   → KD artır (0.8 → 1.2)
   → KP düşür (1.2 → 0.9)
   ```

2. **Hedefi tutmuyor / Yavaş?**
   ```
   → KP artır (1.2 → 1.8)
   → OUTPUT_MAX artır (-8000 → -12000)
   ```

3. **Jitter/Titreşim?**
   ```
   → MIN_MOVE_SPEED artır (120 → 150)
   → alpha düşür (0.3 → 0.2) [main.py:550]
   ```

4. **Lag/Gecikmesi?**
   ```
   → KI_X artır (0.0005 → 0.001)
   → KP artır
   ```

---

## 📊 PID Tuning Formülleri

```
Error = Target - Current
Output = Kp*Error + Ki*∫Error*dt + Kd*d(Error)/dt

Kp: Yanıt hızı (yüksek = hızlı ama salınım)
Ki: Steady-state hatası (yüksek = lag/salınım)
Kd: Damping (yüksek = stabil ama yavaş)
```

---

## 📁 İlgili Dosyalar

- `config.py` - PID parametreleri
- `pid_controller.py` - PID logic
- `main.py` - compute_control() → Smoothing ve MIN_MOVE_SPEED
- `pid_tuner.py` - Bu tool ⭐

---

## ⚡ Çabuk Referans

| Sorun | Çözüm | Parametre |
|-------|-------|-----------|
| Salınım | KD↑ KP↓ | KD_X, KD_Y |
| Yavaş Takip | KP↑ OUTPUT↑ | KP_X, KP_Y, OUTPUT_MAX |
| Jitter | MIN_SPEED↑ | MIN_MOVE_SPEED |
| Overshoot | KP↓ KD↑ | KP_X, KD_X |
| Lag | KI↑ | KI_X, KI_Y |

---

**Başarılı Takibi İsterim! 🚀**
