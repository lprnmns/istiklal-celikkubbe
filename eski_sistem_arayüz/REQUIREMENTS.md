# 📋 TEKNOFEST Yarışma Gereksinimleri (Yetenekler)

## Genel Bilgi
Bu dosya yarışmada gösterilmesi gereken tüm yetenekleri içerir. Her yetenek için kod içinde ilgili fonksiyonlar yazılmalıdır.

---

## Yetenek 1: Kullanıcı Arayüzü ✅
**Açıklama:** Sisteme kullanıcı tarafından komutların verildiği arayüzler (Kullanıcı Arayüz Yazılımı, Joystick, Klavye, vs.) tüm fonksiyonları ile anlatılacaktır.

**Gereksinimler:**
- GUI arayüzü (Tkinter veya PyQt)
- Klavye kontrolleri (WASD veya ok tuşları)
- Joystick desteği (opsiyonel)
- Durum göstergeleri (mod, pozisyon, hedef durumu)
- Ateş butonu
- Mod değiştirme (Manuel/Otomatik)
- Acil durdur butonu

**Klavye Mapping:**
```
W / ↑  : Yukarı hareket (Y+)
S / ↓  : Aşağı hareket (Y-)
A / ←  : Sol hareket (X-)
D / →  : Sağ hareket (X+)
SPACE  : Ateş (Lazer aç)
E      : Acil Durdur
M      : Mod değiştir (Manuel/Otomatik)
H      : Home pozisyona git
Q      : Çıkış
```

---

## Yetenek 2: Yan Eksen Hareketi (270°) ✅
**Açıklama:** Sistem yan eksende toplam 270 derece hareket kabiliyetine sahip olacaktır.

**Teknik Detaylar:**
- X ekseni: -135° ile +135° arası
- Toplam: 270°
- Dişli oranı: 10:1 (150 diş / 15 diş)
- Step motor: 1.8° adım açısı = 200 adım/devir
- Hesaplama: 270° × 10 × (200/360) = 1500 adım (full step)

**Kod Gereksinimleri:**
```python
X_MIN_ANGLE = -135  # derece
X_MAX_ANGLE = 135   # derece
X_GEAR_RATIO = 10   # 150:15
X_STEPS_PER_REV = 200  # 1.8° motor
```

---

## Yetenek 3: Yükseliş Ekseni Hareketi (60°) ✅
**Açıklama:** Sistem yükseliş ekseninde toplam 60 derece hareket kabiliyetine sahip olacaktır.

**Teknik Detaylar:**
- Y ekseni: -30° ile +30° arası
- Toplam: 60°
- Dişli oranı: 2:1 (30 diş / 15 diş)
- Hesaplama: 60° × 2 × (200/360) = 66.67 adım (full step)

**Kod Gereksinimleri:**
```python
Y_MIN_ANGLE = -30   # derece
Y_MAX_ANGLE = 30    # derece
Y_GEAR_RATIO = 2    # 30:15
Y_STEPS_PER_REV = 200
```

---

## Yetenek 4: Durağan Kırmızı Balon Patlatma (5m) ✅
**Açıklama:** Sistem durağan halde ateş ederek 5m mesafedeki Kırmızı renkli balonu patlatabilecektir.

**Gereksinimler:**
- YOLO ile kırmızı balon tespiti (class_id = 0 varsayalım)
- Hedef kilitleme (balon merkeze alındığında)
- Lazer açma ve belirli süre tutma (patlayana kadar)
- Patladıktan sonra sonraki hedefe geçme

**Kod Akışı:**
```
1. Kırmızı balon tespit et
2. Balonu merkeze al (PID ile)
3. Dead zone içindeyse "kilitlendi" say
4. Lazer aç
5. Belirli süre bekle (2-5 saniye)
6. Balon kaybolursa → patladı, sonraki hedefe geç
```

---

## Yetenek 5: Durağan Mavi Balon Patlatma (5m) ✅
**Açıklama:** Sistem durağan halde ateş ederek 5m mesafedeki Mavi renkli balonu patlatabilecektir.

**Gereksinimler:**
- YOLO ile mavi balon tespiti (class_id = 1 varsayalım)
- Manuel modda: Kullanıcı seçer ve ateş eder
- Otomatik modda: Mavi balonlara ateş ETMEZ (sadece kırmızı!)

**NOT:** Bu yetenek SADECE manuel modda test edilir. Otomatik modda sistem mavi balonları GÖRMEZDEN GELMELİ.

---

## Yetenek 6: Yan Eksen Acil Durdur ✅
**Açıklama:** Sistem yan eksende hareket ederken, Acil Durdur'a basılarak sistemin durduğu gözlenecektir.

**Gereksinimler:**
- Acil durdur butonu (fiziksel veya yazılımsal)
- Basıldığında:
  - Tüm motor hareketleri ANINDA durur
  - Lazer kapanır
  - Sistem "EMERGENCY_STOP" durumuna geçer
- Tekrar başlatmak için reset gerekir

**Kod:**
```python
def emergency_stop():
    motor_x.stop_immediately()
    motor_y.stop_immediately()
    laser.off()
    system_state = "EMERGENCY_STOP"
```

---

## Yetenek 7: Yükseliş Ekseni Acil Durdur ✅
**Açıklama:** Sistem yükseliş eksende hareket ederken, Acil Durdur'a basılarak sistemin durduğu gözlenecektir.

**Gereksinimler:**
- Yetenek 6 ile aynı, sadece Y ekseni hareket halindeyken test edilir

---

## Yetenek 8: Ateş Sırasında Acil Durdur ✅
**Açıklama:** Sistem ateş ederken Acil Durdur'a basılarak sistemin ateşi kestiği gözlenecektir.

**Gereksinimler:**
- Lazer açıkken acil durdur basılırsa:
  - Lazer ANINDA kapanır
  - Motorlar durur
  - Sistem "EMERGENCY_STOP" durumuna geçer

---

## Yetenek 9: Hareket Eden Balon Takibi ✅ (KRİTİK)
**Açıklama:** Sistem yan ve yükseliş ekseninde hareket eden bir balonu takip edebilecektir. Sahnede farklı balonlar da olacaktır. Hedef takibi yaparken bu balonların takip edilmediği görülecektir. Bu takip sırasında kamera kaydında sistemin fiziksel olarak hedefe yönlendiği ve kamera görüntüsünde hedefin ortalandığı görülecektir.

**Gereksinimler:**
- Hareket eden balon takibi (PID + Kalman Prediction)
- Tek hedefe kilitleme (en yakın veya en büyük kırmızı balon)
- Diğer balonları (mavi dahil) yok sayma
- Smooth takip (titreme olmadan)
- Kamera görüntüsünde hedef her zaman merkezde

**Algoritma:**
```
1. Tüm balonları tespit et (YOLO)
2. Sadece KIRMIZI balonları filtrele
3. Hedef seç (en büyük veya en yakın)
4. Kalman ile sonraki pozisyonu tahmin et
5. PID ile motorları tahmin edilen pozisyona yönlendir
6. Hedef kaybolursa → yeni hedef seç
```

**Kritik:** Bu yetenek için PID + Kalman + Non-blocking yapı ŞART!

---

## Yetenek 10: Yasak Bölge (Ateş Engelleme) ✅
**Açıklama:** Sistemde yan eksende (-15,15) dereceleri arasına ateşe yasak alan tanımlanır. Sistemin (-180,-15) ve (15,180) dereceleri arasında ateş ettiği, (-15,15) arasında ateş etmediği ateş tuşuna basılarak gözlenecektir.

**Gereksinimler:**
- Yasak bölge tanımı: X açısı -15° ile +15° arasındaysa
- Bu bölgede ateş butonu basılsa bile lazer AÇILMAZ
- GUI'de yasak bölge göstergesi (kırmızı/yeşil)

**Kod:**
```python
FORBIDDEN_ZONE_MIN = -15  # derece
FORBIDDEN_ZONE_MAX = 15   # derece

def can_fire():
    current_x_angle = get_current_x_angle()
    if FORBIDDEN_ZONE_MIN <= current_x_angle <= FORBIDDEN_ZONE_MAX:
        return False  # Yasak bölgede, ateş edilemez
    return True

def fire():
    if not can_fire():
        print("YASAK BÖLGE - Ateş engellendi!")
        return
    laser.on()
```

---

## Yetenek 11: Tam Otonom Mod (OPSİYONEL) ⭐
**Açıklama:** Sistemin karşısına 3 adet kırmızı 3 adet mavi balon yerleştirilecektir. Ve 2. aşamada belirtilen görev balonlar hareket ettirilmeden gerçekleştirilecektir. Sistem otonom moda alınarak, 3 adet kırmızı balonu sırası ile imha edecektir. 10 saniye beklendikten sonra Acil Durdur butonuna basılacak ve 10 saniye daha beklendikten sonra sistem kapatılacaktır. Bu süre dahilinde mavi balonlara ateş etmediği görülecektir.

**Gereksinimler:**
- Otonom mod butonu
- Otomatik kırmızı balon tespiti ve sıralama
- Sırayla her kırmızı balonu:
  1. Hedef al
  2. Merkeze getir
  3. Ateş et
  4. Patlamasını bekle
  5. Sonraki hedefe geç
- Mavi balonları ASLA hedef alma
- 10 saniye sonra Acil Durdur'a basılacak → sistem duracak
- Acil Durdur'dan sonra 10 saniye daha → kapatılacak

**Durum Makinesi:**
```
IDLE → AUTONOMOUS_START → SEARCHING → TARGET_ACQUIRED → 
TRACKING → FIRING → TARGET_DESTROYED → SEARCHING (tekrar) → 
(Acil Durdur) → EMERGENCY_STOP → SHUTDOWN
```

---

## Özet Tablo

| Yetenek | Açıklama | Mod | Öncelik |
|---------|----------|-----|---------|
| 1 | Kullanıcı Arayüzü | Tümü | Yüksek |
| 2 | X Ekseni 270° | Tümü | Yüksek |
| 3 | Y Ekseni 60° | Tümü | Yüksek |
| 4 | Kırmızı Balon (Durağan) | Manuel/Oto | Yüksek |
| 5 | Mavi Balon (Durağan) | Manuel | Orta |
| 6 | X Acil Durdur | Tümü | Yüksek |
| 7 | Y Acil Durdur | Tümü | Yüksek |
| 8 | Ateş Acil Durdur | Tümü | Yüksek |
| 9 | Hareket Takibi | Otomatik | Kritik |
| 10 | Yasak Bölge | Tümü | Yüksek |
| 11 | Tam Otonom | Otonom | Opsiyonel |
