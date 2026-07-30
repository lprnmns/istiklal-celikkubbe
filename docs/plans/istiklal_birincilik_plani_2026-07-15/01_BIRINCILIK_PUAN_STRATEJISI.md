# 01 — Birincilik Puan Stratejisi

## 1. Puan matematiği

| Kalem | En çok | Durum |
|---|---:|---|
| ÖTR | 10 | Tamamlandı, gerçek puan bilinmiyor |
| KTR | 50 | Geçildi, gerçek puan bilinmiyor |
| Final sunumu | 40 | Kazanılabilir |
| Ebat | 20 | Kazanılabilir |
| Aşama 1 | 100 | Kazanılabilir |
| Aşama 2 | 120 | Kazanılabilir |
| Aşama 3 | 160 | Kazanılabilir |
| Toplam | 500 |  |

Video ayrı bir puan kalemi değildir; fakat finale ve gelecekteki 440 puanın tamamına erişim kapısıdır.

## 2. Üç hedef seviyesi

| Seviye | Sunum | Ebat | A1 | A2 | A3 | Gelecek puan |
|---|---:|---:|---:|---:|---:|---:|
| Yalnız uygunluk | 25 | 0 | 30 | 20 | 10 | 85 |
| Rekabetçi taban | 32 | 20 | 85 | 90 | 80 | 307 |
| Birincilik çalışma hedefi | 36 | 20 | 95 | 105 | 120 | 376 |
| Birincilik üst hedefi | 40 | 20 | 100 | 120 | 140 | 420 |

Gerçek toplam, tabloya gerçek ÖTR+KTR puanının eklenmesiyle bulunur. İlk 72 saatte bu iki puan öğrenilmeden rakiplere göre kesin puan açığı hesabı yapılmaz.

## 3. Puan başına yatırım önceliği

### Öncelik 0 — Video kapısı

Y1–Y5’ten biri eksikse diğer bütün final yatırımları değersizleşir. Bu nedenle 10 Ağustos’a kadar ekip kapasitesinin ana kısmı video kabulüne ayrılır.

### Öncelik 1 — Kolay kaybedilmemesi gereken 20 ebat puanı

KTR yaklaşık 60 cm bildiriyor. Tam sınırda kalmak kabul edilmez. Final konfigürasyonunda kablo, kamera, çıkıntı ve hareket zarfı dahil en uzun sabit ölçü mümkünse 58–59 cm altında tutulmalıdır. Hareketli maksimum zarfın nasıl ölçüleceği hakem yaklaşımıyla ayrıca doğrulanır.

### Öncelik 2 — Aşama 1’i 95+ yapmak

Aşama 1 tamamen manuel olduğu için algı/IFF belirsizliğinden bağımsız en kontrol edilebilir 100 puandır. Dört doğru hedef, doğru sıra, ilk Balistik Füze, uzun menzil güvenilirliği ve hızlı operatör akışı hedeflenir.

### Öncelik 3 — Aşama 2’de 3/3 tamamlamak

Tur puanları doğrusal değildir:

- 1 hedef: 5
- 2 hedef: 15
- 3 hedef: 30

Üçüncü hedef, ikinci hedeften sonra tek başına ilave 15 puan getirir. Bu yüzden “iki hedef yeter” stratejisi birincilik stratejisi değildir. Çalışma hedefi dört turda 3/3; yarışma tabanı en az üç tur 3/3 ve kalan tur en az 2/3, yani cezasız 105 puandır.

### Öncelik 4 — Aşama 3’te sıfır dost vuruşu ve 120+

Aşama 3 hem 160 puanla en büyük tek kalemdir hem de ödül için en az 10 puan zorunludur. Hedef yalnız balon değildir:

    Gövde algıla → sınıfı doğrula → IFF yap → doğru balonu bağla
    → sınıfa uygun menzil penceresini doğrula → SafetyDecision → ateş

Birincilik için yalnız bir turu geçmek değil, sekiz turda güvenilir ve açıklanabilir karar gerekir.

## 4. Aşama bazlı strateji

### Aşama 1

- Operatöre zarf sırasını girme/doğrulama ekranı verilir.
- İlk angajmanda Balistik Füze dışında ateş yazılımsal uyarı ve iki aşamalı onayla engellenir.
- Manuel hareket ve ateş dışında otonom yönelim kapalıdır.
- Önce güvenli 30 puan barajını koruyan rota, sonra 80 görev puanını ve zaman bonusunu maksimize eden rota prova edilir.
- En uzun menzil yalnız son kabul matrisinde yeterli başarı oranına ulaşırsa yarışma varsayılanı olur.

### Aşama 2

- Sınıflandırma ana görevden çıkarılır.
- Üç hedef kalıcı track ID ile birlikte tutulur.
- Öncelik, yalnız “en yakın” değil parkurdan çıkışa kalan süre, ateş çözümü kalitesi ve önceki deneme durumuna göre hesaplanır.
- Patlama veya hedef kaybı doğrulanmadan iz tamamlandı sayılmaz.
- İlk atış başarısızsa yeniden angajman için zaman bırakılır.

### Aşama 3

- Gerçek gövde renkleri saha profilinden seçilir; kırmızı/mavi sabitlenmez.
- Balon rengi IFF girdisi değildir.
- F-16 yalnız 10–15 m, Helikopter/Balistik Füze 5–15 m, Mini/Micro İHA 0–15 m penceresinde angaje edilir.
- Belirsiz association veya unknown IFF ateş üretmez.
- Üç ardışık düşman kaçırma sıfır puan riski nedeniyle turn deadline ve yeniden kazanım davranışı ayrıca tasarlanır.
- Sıfır dost vuruşu, yüksek ham atış sayısından daha değerlidir.

## 5. Zaman ve ekip yatırımı

### Video teslimine kadar

| Alan | Önerilen kapasite |
|---|---:|
| Firmware, E-Stop, CommandGateway | yüzde 35 |
| Y2/Y3/Y4/Y5 fiziksel kabul | yüzde 30 |
| Baseline, cihaz, launcher, log | yüzde 15 |
| Y1 operatör akışı ve video | yüzde 15 |
| Y6 keşif | en çok yüzde 5 |

### Video tesliminden sonra

| Alan | Önerilen kapasite |
|---|---:|
| Aşama 1 | yüzde 15 |
| Aşama 2 | yüzde 25 |
| Aşama 3 ve perception | yüzde 40 |
| Platform/saha güvenilirliği | yüzde 10 |
| Kanıt/sunum/mülakat | yüzde 10 |

Ekip kişi sayısı azsa Aşama 1 ve Aşama 2 güvenilirliği korunur, Aşama 3 özellikleri daha küçük dikey dilimler halinde alınır.

## 6. Atış ve bakım ekonomisi

Finalde teorik en az 24 başarılı imha gerekir:

- Aşama 1: 4
- Aşama 2: 12
- Aşama 3: 8

KTR, yaklaşık 30 atıştan sonra CO₂ performans düşüşü bildiriyor. Iska, test atışı ve yeniden angajmanla bu eşik aşılır. Bu nedenle:

- Her aşamaya yeni veya ölçülmüş yeterli basınçla başlanır.
- Atış sayacı UI ve fiziksel pit checklist’inde bulunur.
- Tüp değişimi 10 dakikalık toplam bakım bütçesi içinde prova edilir.
- Aşama bazlı maksimum atış bütçesi ve “değiştir/devam et” eşiği fiziksel testle belirlenir.
- Yedek tüp, conta, şarjör ve takım düzeni standartlaştırılır.

## 7. Dondurulacak yatırımlar

- Yeni dijital ikiz sahnesi, 3B parlatma veya kozmetik UI turu.
- 235 raporu daha da çoğaltmak.
- Fiziksel acceptance’a bağlanmayan mimari soyutlama.
- Video öncesi tam repo yeniden yazımı.
- Model hazır değilken sentetik metadata ile production-ready ilanı.
- Çekim makinesi gerektirmiyorsa kapsamlı Windows/Docker dönüşümü.

## 8. Haftalık skor tablosu

Her hafta şu tablo gerçek ölçümle güncellenir:

| Kapı | Ölçüm | Hedef |
|---|---|---|
| Video | Y1–Y5 ardışık temiz tam prova | 2 tam prova |
| Ebat | Final konfigürasyonu en uzun boyut | tercihen 58–59 cm altında |
| A1 | Son 10 tam turun puan ortalaması | 95+ |
| A2 | Son üç dört-turluk serinin puanı | 105+; üst hedef 120 |
| A3 | Son üç sekiz-turluk serinin puanı | 120+ |
| Dost güvenliği | Replay/HIL/fiziksel dost vuruşu | 0 |
| Kurulum | Güçten Quick Preflight tamamlanmasına süre | 5 dakika altında yazılım, 30 dakika altında tam saha |
| Bakım | Provalı toplam pit süresi | 10 dakika altında |

Sunum ve geliştirme iddiaları değil, bu tablo birincilik durumunu belirler.
