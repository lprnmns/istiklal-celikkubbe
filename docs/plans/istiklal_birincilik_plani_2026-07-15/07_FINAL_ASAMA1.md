# 07 — Final Aşama 1: Manuel Mod ve 95+ Puan

## 1. Resmî görev

- Tamamen manuel hareket ve ateş.
- Yaklaşık 5, 10 ve 15 m hedefler.
- Dört hedef tipi, zarfla verilen sırada.
- İlk hedef Balistik Füze.
- Yakın 5, orta 10, uzun 20 puan.
- Görev puanı en çok 80.
- Yanlış hedef eksi 5.
- Beş dakika süre.
- 80 görev puanına ulaşınca kalan süre oranında en çok 20 bonus.
- Aşama 2’ye geçmek için en az 30.

Bonus formülü:

    bonus = 20 × kalan_saniye / 300

80 görev puanı alınırsa yaklaşık hedefler:

| Toplam hedef | Tamamlama süresi |
|---|---:|
| 85 puan | 225 saniye veya daha kısa |
| 90 puan | 150 saniye veya daha kısa |
| 95 puan | 75 saniye veya daha kısa |

Önce sıfır hata ve 80 görev puanı, sonra hız optimize edilir.

## 2. Ürün modu sözleşmesi

AŞAMA1_MANUAL modunda:

- Pan, tilt ve ateş niyeti yalnız operatör girdisinden gelir.
- Tracker hedef kutusu gösterebilir; otomatik hareket veya otomatik ateş üretemez.
- Joystick/gamepad ana, klavye yedek giriş olabilir.
- Fiziksel E-Stop, arm, yasak bölge, limit ve cihaz freshness manuel modu da bağlar.
- Mod değişimi sırasında bütün hareket/ateş kuyruğu temizlenir.
- Aşama 2/3 otonom komutları bu moda sızamaz.

## 3. Operatör ekranı

Tek ekranda:

- Zarf sırası ve sıradaki hedef.
- İlk hedef Balistik Füze güvenlik uyarısı.
- Kalan süre.
- Vurulan/hedeflenen hedefler.
- Ham görev puanı, ceza ve tahmini bonus.
- Pan/tilt konumu ve limit yaklaşımı.
- Kamera nişangâhı ve manuel hassasiyet modu.
- CO₂/atış sayısı.
- FIRE/NO-FIRE nedeni.
- E-Stop ve fiziksel arm.

Operatör hedef sırasını yarışma başlamadan girer, ikinci kişi read-back ile doğrular ve kilitler. Yarışma sırasında yanlışlıkla yeniden sıralama yapılamaz.

## 4. Girdi tasarımı

Joystick:

- Dead-zone kalibrasyonu.
- Eğri: merkezde hassas, dışta hızlı.
- Pan/tilt hız sınırı.
- Fine aim tuşu.
- Ateş için ayrı ve yanlışlıkla basılması zor tetik.
- E-Stop yazılımsal tuş değildir; yalnız ek stop komutu olabilir.

Klavye yedeği:

- Açık tuş haritası.
- Focus kaybında hareket yok.
- Key-up kaybı/watchdog’da duruş.
- Ateş iki aşamalı veya korumalı giriş.

Girdi cihazı koparsa SAFE_STOP; otomatik yedek moda geçip hareket etmez.

## 5. Sıra ve puan motoru

MissionService için şartnameye uygun kurallar:

- Dört hedef sırasını doğrula.
- İlk hedefin Balistik Füze olmasını ayrıca doğrula.
- Yanlış hedef cezasını açık olay olarak kaydet.
- Yakın/orta/uzun puanlarını doğru hesapla.
- Yalnız 80 görev puanı sonrası bonus hesapla.
- Beş dakikada görevi sonlandır.
- Aşama geçiş barajını 30 olarak göster.

Aşama 1’de ceza yorumunun resmî metinde belirsiz olduğu noktalarda en muhafazakâr hesap UI’da gösterilir ve yarışma toplantısında hakemden teyit edilir.

## 6. Nişan ve kalibrasyon

- Kamera–namlu paralaksı 5/10/15 m’de ölçülür.
- Pan/tilt backlash ve yön semantiği doğrulanır.
- Her mesafe için nişangâh ofset profili.
- CO₂ basıncı/atış sayısına göre düşüş gözlemi.
- Uzun menzilde başarı kabul eşiği sağlanmıyorsa yarışma risk planı orta mesafe güvenli puan rotasını içerir.

Amaç, operatörün tahminle değil doğrulanmış görsel ofsetle nişan almasıdır.

## 7. Yarışma stratejisi

### Güvenli geçiş modu

- Önce doğru sıra ve en az 30 puan.
- Sistem/atış beklenmedik davranıyorsa hız yerine geçiş barajı korunur.

### Birincilik modu

- Dört hedefi mümkün olan en yüksek geçerli puan mesafesinde imha.
- 80 görev puanı.
- Hedef 90+; üst hedef 95+.
- Operatör hareketleri önceden ezberlenmiş ama zarf sırasına uyarlanabilir.

Hız çalışması ancak son 10 tam provada yanlış sıra ve yanlış hedef sıfırsa başlar.

## 8. Kabul testleri

### Yazılım

- Gamepad ve klavye unit/integration.
- Focus loss, disconnect, stuck key.
- Manual modda tracker’dan fiziksel komut çıkmaması.
- Sıra, ceza, timer ve bonus test vektörleri.
- Mod geçişinde queue flush.

### HIL

- Tetik enerjisi kapalı tam hedef sırası.
- İki farklı operatör.
- E-Stop, USB kopma, kamera kaybı.

### Fiziksel

Son 10 tam tur:

- 10/10 ilk hedef Balistik Füze.
- 10/10 doğru sıra.
- 0 yanlış hedef.
- En az 9/10 dört hedef tamamlama.
- En az 8/10 turda 90+ simüle puan.
- En az 3 turda 95+.
- Hiçbir turda güvenlik bypass yok.

## 9. Muhtemel kod alanları

- backend/app/services/mission_service.py
- backend/app/services/command_gateway.py — yeni
- backend/app/services/decision_engine.py
- backend/app/schemas/mission.py
- backend/app/api/mission.py
- frontend/src/views/MissionModesView.vue
- frontend/src/stores/missionStore.ts
- frontend/src/api/mission.ts
- frontend/src/types/mission.ts
- config/config.yaml
- backend/tests/test_mission_operations.py
- yeni Aşama 1 input ve scoring testleri

## 10. Geri dönüş koşulu

Gamepad/manuel entegrasyon fiziksel komut güvenliğini veya video baseline’ını bozarsa:

- Otonom dallardan ayrılır.
- Gerçek tetik kapatılır.
- Son güvenli CommandGateway sürümüne dönülür.
- Klavye yedek akışı yalnız acceptance geçerse kullanılır.

Geçiş barajını tehlikeye atan hız ayarı yarışma profilinden çıkarılır.
