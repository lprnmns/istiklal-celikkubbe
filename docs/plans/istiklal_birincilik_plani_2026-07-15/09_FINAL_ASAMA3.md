# 09 — Final Aşama 3: Dost/Düşman ve 120+ Puan

## 1. Resmî görev

Sekiz tur; her tur bir düşman ve iki dost hedef yaklaşır.

| Sınıf | Puan | Geçerli imha menzili |
|---|---:|---|
| F-16 | 30 | 10–15 m |
| Helikopter | 20 | 5–15 m |
| Balistik Füze | 20 | 5–15 m |
| Mini/Micro İHA | 10 | 0–15 m |

Kurallar:

- Dost vurulması ve/veya düşmanın vurulamaması tur başına en çok eksi 10.
- Üç ardışık tur düşman vurulamazsa aşama başarısız ve sıfır.
- Ödül sıralamasına girmek için bu aşamadan en az 10.
- Balon renkleri aynı olabilir ve değişebilir.
- Dost/düşman bilgisi gövde rengindedir; gerçek renkler sabit verilmemiştir.

## 2. Hedef karar zinciri

    Body Detection
      → Body Track
      → Class
      → Configurable IFF
      → Balloon Detection/Track
      → Body–Balloon Association
      → Range + Uncertainty
      → Zone + Stability + Device Safety
      → SafetyDecision
      → CommandGateway
      → Fire

Zincirin herhangi bir halkası stale, unknown veya ambiguous ise atış yoktur.

## 3. Görev profili

Saha öncesi profile girilecekler:

- Dost ve düşman gövde renk kümeleri.
- Aydınlatma/white-balance kalibrasyonu.
- Sınıf ID mapping.
- Sınıf başına menzil penceresi.
- Hedef model/3MF revizyon hash’i.
- Parkur ve yasak bölgeler.
- Association geometri parametreleri.
- Track/decision stabilite eşikleri.

Profil iki kişiyle read-back yapılır ve yarışma turu sırasında değiştirilemez.

## 4. IFF güvenlik kuralı

- Balon rengi IFF için kullanılmaz.
- Gövde rengi yalnız tek frame piksel örneğiyle kararlaştırılmaz.
- Renk/segmentation sonucu track boyunca zamansal olarak birleştirilir.
- UNKNOWN ve AMBIGUOUS dost gibi korunur: NO_FIRE.
- Düşman kararı için minimum stabilite süresi/confidence acceptance ile belirlenir.
- UI yalnız “enemy” değil, karar nedeni ve güvenini gösterir.

Sıfır dost vuruşu, Aşama 3’ün ana kalite metriğidir.

## 5. Sınıf ve menzil

Sınıf sonucu:

- F16.
- HELICOPTER.
- BALLISTIC_MISSILE.
- MINI_MICRO_UAV.
- UNKNOWN.

Menzil kararı yalnız nokta tahmini değildir; belirsizlik aralığıyla verilir. Güvenli politika:

- Geçerli menzil penceresi içinde yeterli güven.
- F-16 için 10 m altı atış yok.
- 15 m üstü bütün sınıflarda atış yok.
- Kalibrasyon dışı görünüm/ölçek NO_FIRE_RANGE_UNCERTAIN.

Menzil penceresine yeni girecek hedef için track devam eder; geçerli pencerede karar tekrar değerlendirilir.

## 6. Body–balon association

Association girdileri:

- Resmî maket/balon bağlantı geometrisi.
- Görüntüde göreli konum.
- Ortak hareket ve hız.
- Track sürekliliği.
- Perspektif ve kalibre edilmiş bağlantı bölgesi.
- Birden fazla adayda maliyet matrisi.

Durumlar:

- STABLE_LINK.
- CANDIDATE.
- AMBIGUOUS.
- ORPHAN_BODY.
- ORPHAN_BALLOON.
- LOST.

Yalnız STABLE_LINK ve ENEMY gövde ateş adayıdır.

## 7. Tur ve başarısızlık yönetimi

Her tur:

1. Üç gövde ve bağlı balonları acquire et.
2. Dostları korunan track olarak işaretle.
3. Düşmanı sınıf+IFF ile doğrula.
4. Geçerli menzil penceresini bekle.
5. Ateş çözümü ve hit confirmation.
6. Başarısızsa turn deadline içinde yeniden angaje et.
7. Tur sonucunu ve ardışık miss sayacını kaydet.

Üç ardışık miss riski için:

- Track kaybında hızlı ama güvenli reacquire.
- İlk deneme için yeterli zaman bırakacak menzil stratejisi.
- CO₂/atış bütçesi.
- İkinci deneme için açık deadline.
- Operatöre yalnız durum/abort yetkisi; dışarıdan hedef yönlendirme yok.

## 8. Birincilik stratejisi

### Uygunluk kapısı

İlk hedef, sıfır dost riskiyle en az bir geçerli düşman imhasını garanti etmektir. Bu yalnız ödül barajını açar; yeterli sonuç değildir.

### Çalışma hedefi

- Sekiz turda sıfır dost vuruşu.
- Üç ardışık miss yok.
- Test parkurunun resmî benzeri 160 puanlık dağılımında 120+.
- Üst hedef 140+.

Ham confidence düşürülerek aşırı ateş etmek yasaktır. İyileştirme, daha erken acquire ve daha iyi association/range ile güvenli atış penceresini büyüterek yapılır.

## 9. Kabul matrisi

### Replay/sentetik

- Aynı sınıfta dost+düşman.
- Değişen balon rengi.
- Kırmızı/mavi eşlemesinin ters çevrildiği profil.
- İki balon yakın/kesişen.
- Gövde veya balon kısa kaybı.
- 9,5 m F-16.
- 10–15 m sınırları.
- 15 m üstü bütün sınıflar.
- Düşük ışık ve white-balance sapması.
- Üç ardışık miss senaryosu.

Beklenti:

- Dostta fire output sıfır.
- Ambiguous/orphan/stale durumda fire sıfır.
- Menzil dışı fire sıfır.

### HIL

- Tetik enerjisi kapalı sekiz tur.
- Gerçek pan/tilt ve camera latency.
- E-Stop/reconnect.

### Fiziksel

- En az üç tam sekiz-turluk seri.
- Her seride sıfır dost vuruşu.
- Hiçbir seride üç ardışık düşman miss yok.
- Her seride 120+ resmî-benzeri puan.
- En az bir seride 140+.
- Bütün fire kararlarında class/IFF/link/range/safety kanıtı.

## 10. Muhtemel kod alanları

- backend/app/services/vision_pipeline.py
- backend/app/services/inference_adapter_service.py
- backend/app/services/model_package_service.py
- backend/app/services/color_classifier_service.py
- backend/app/services/kalman_tracker.py
- backend/app/services/decision_engine.py
- backend/app/services/mission_service.py
- backend/app/services/command_gateway.py — yeni
- backend/app/schemas/vision.py
- backend/app/schemas/decision.py
- backend/app/schemas/tracking.py
- frontend/src/components/cockpit/EngagementPanel.vue
- frontend/src/stores/decisionStore.ts
- frontend/src/stores/missionStore.ts
- yeni Aşama 3 replay/HIL/fiziksel testleri

## 11. Geri dönüş koşulu

- Model class mapping belirsizse Aşama 3 canlı atış kapalı.
- IFF profilinde bir dost false-enemy olayı görülürse fiziksel fire dondurulur.
- Association yanlış balona bağlanırsa yalnız dry-run.
- Range sınır ihlali görülürse ilgili sınıf angajmanı kapatılır.
- Yeni perception sürümü latency veya Y5 baseline’ını bozarsa son kanıtlı model/adapter’a dönülür.

Geri dönüş “balon rengine göre ateş” değildir; güvenli NO_FIRE ve yeniden kalibrasyondur.
