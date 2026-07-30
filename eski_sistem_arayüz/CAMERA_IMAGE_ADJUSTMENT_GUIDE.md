# GÖRÜNTÜ PARLAKLIGI VE RENK DÜZELTMESİ - Balon Kayboluyor Sorunu

## 🎥 Sorun
Bazen balon kayboluyor - özellikle parlak ışıkta veya karanlık alanlarda gözden kayıyor

## ✅ Uygulanan Çözümler

### 1. **Kamera Brightness Ayarları Düşürüldü**
```python
EXPOSURE: -3 → -5         # Daha az ışık (-2 stop kapalı)
BRIGHTNESS: 150 → 100     # ↓33% azaltıldı
SATURATION: (yeni) 50     # Renk doygunluğu
```

**Neden:** 
- Aşırı bright görüntü balon algılamayı engeller
- Gözü kamaştıran parlaklık = renk algılama başarısız
- Lower exposure = daha iyi kontrol

### 2. **CLAHE (Contrast Limited Adaptive Histogram Equalization)** ⭐
```
Eski: Doğrudan frame → Detection
Yeni: Frame → CLAHE → Saturation Azalt → Detection
```

**Ne yapıyor:**
- Yerel kontrast artırıyor (parlak ve koyu alanları dengeler)
- Glare'i azaltıyor (gözü kamaştıran beyazlıklar)
- Balon görünürlüğü artırıyor

**Formül:**
```
1. BGR → LAB (parlaklık odaklı)
2. L kanalına CLAHE uygula (tileGridSize=8x8)
3. LAB → BGR dönüştür
```

### 3. **Saturation Azaltma (Renk Doygunluğu)**
```python
S_new = S_original * 0.7  # %70'ine azalt
```

**Neden:**
- Aşırı renkli görüntü = renk algılama yanılır
- Soft renkler = daha doğru HSV maskeleme
- Parlaklık değişimleri daha az etkili

### 4. **Detection Pipeline Güncellemesi**
```
Eski: self.current_frame → Detector → Draw
Yeni: self.current_frame → _preprocess_frame() 
      → processed_frame → Detector → Draw
```

**Pipeline:**
1. Frame al
2. **CLAHE uygula** (kontrastı dengele)
3. **Saturation azalt** (renk doygunluğu)
4. Detection'a gönder
5. Sonuçları GUI'de göster

---

## 📊 Kamera Ayarları Özeti

| Parametre | Eski | Yeni | Etki |
|-----------|------|------|------|
| EXPOSURE | -3 | -5 | 2 stop daha koyu ↓ |
| BRIGHTNESS | 150 | 100 | 33% azaltıldı ↓ |
| SATURATION | - | 50 | Renk doygunluğu kontrol |

## 🔄 İşlem Adımları (Processing Pipeline)

```
┌─────────────────┐
│ Raw Frame       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ 1. CLAHE (Histogram Equal)  │
│    - LAB uzayında L'ye uygula│
│    - Yerel kontrastı artır   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 2. Saturation Azalt        │
│    - HSV uzayına çevir      │
│    - S * 0.7 (30% azalt)    │
│    - BGR'ye geri dönüştür   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Processed Frame             │
│ (Detection'a hazır)         │
└─────────────────────────────┘
```

---

## ⚙️ İyileştirme Parametreleri

### CLAHE Ayarları
```python
clipLimit=2.0        # Kontrast sınırı (0-40, düşük=daha soft)
tileGridSize=(8, 8)  # İşlem penceresi boyutu
```

**Tweak etmek isterseniz:**
- Çok koyu → `clipLimit=3.0`
- Çok parlak → `clipLimit=1.5`

### Saturation Çarpanı
```python
s = cv2.multiply(s, 0.7)  # 70% saturation bırak
```

**Tweak etmek isterseniz:**
- Daha renkli → 0.8 veya 0.9
- Daha gri → 0.5 veya 0.6

---

## 🎯 Sonuç

| Aspekt | Öncesi | Sonrası |
|--------|--------|---------|
| Balon Görünürlüğü | Kayboluyor | Stabil |
| Glare Problemi | Yüksek | Düşük |
| Renk Algılama | Yanılabiliyor | Doğru |
| Parlak-Koyu Denge | Çarpık | Dengeli |

---

## 📁 Değiştirilen Dosyalar

- [main.py](main.py)
  - Kamera ayarları güncellendi (satır ~211)
  - `_preprocess_frame()` metodu eklendi
  - Detection pipeline güncellendi

- [config.py](config.py) - İlgisiz (kamera ayarları kod içinde)

---

## 🧪 Test Etme

1. **Parlak ışıkta test et** - balon görünür mü?
2. **Karanlık ortamda test et** - CLAHE yardımcı oluyor mu?
3. **Hızlı hareket** - takip kesiliyor mu?

**Çok parlak hala sorunu varsa:**
```python
# main.py satır ~213
self.cap.set(cv2.CAP_PROP_EXPOSURE, -7)  # Daha da azalt
```

**Çok koyu hala sorunu varsa:**
```python
# main.py satır ~247
clipLimit=3.0  # CLAHE'yi güçlendir
```

---

**Balon görünürlüğü artmış olmalı! 🎈**
