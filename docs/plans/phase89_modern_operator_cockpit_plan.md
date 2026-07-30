# Phase 89 — Modern Operatör Kokpiti ve UI Sadeleştirme Planı

Tarih: 2026-07-17

Durum: Yazılımsal dilim tamamlandı; gerçek donanım kabulü HIL-19'a kaydedildi.

## 1. Hedef

Kokpitin amacı aynı anda mümkün olduğunca fazla teknik veri göstermek değil,
operatörün şu dört soruya bir bakışta doğru cevap vermesidir:

1. Sistem hangi görev ve çalışma modunda?
2. Kamera ne görüyor ve hangi hedef seçili?
3. Taret ne yapıyor; takip ve ateş hazır mı?
4. Komut engelliyse kesin neden ne ve güvenli durdurma nerede?

Yeni ekran gerçek kamera, 3B dijital ikiz, CommandGateway ve görev durumunu
koruyacak; mühendislik ayarlarını normal operatör görünümünden çıkaracaktır.

## 2. Değiştirilmeyecek sözleşmeler

- Fiziksel hareket/FIRE yalnız CommandGateway üzerinden çıkar.
- E-Stop ve SAFE STOP her zaman görünür ve erişilebilir kalır.
- Eksik donanım bütün uygulamayı kilitlemez; ilgili fiziksel komut reason code
  ile engellenir.
- Kamera, model, profil veya mock durumu gerçekte olduğundan daha hazır
  gösterilmez.
- Dijital ikiz gerçek pan/tilt ve kamera görüş ekseniyle senkron kalır.
- Operatör ve mühendis görünümü aynı backend gerçekliğini kullanır; ikinci bir
  sahte UI durumu oluşturulmaz.

## 3. Teknoloji kararı

Mevcut Vue 3.5, TypeScript, Pinia, Tailwind CSS 4 ve Three.js korunur.

Eklenecek küçük ve güncel katman:

- `reka-ui`: erişilebilir dialog, dropdown, tabs, tooltip ve drawer
  primitive'leri.
- `@lucide/vue`: tek tip, okunabilir ikon seti.
- `@vueuse/core`: fullscreen, media-query, event listener ve cihaz/viewport
  composable'ları.

İlk dilimde eklenmeyecekler:

- Ağır dashboard/component framework'ü.
- Yeni chart kütüphanesi.
- Animasyon framework'ü.
- İkinci state-management veya ikinci API cache sistemi.

Bu seçim bundle büyümesini sınırlarken güncel, erişilebilir ve tutarlı bir
bileşen sistemi sağlar. Windows/Linux/Docker davranışı UI kütüphanesine bağlı
olmaz.

## 4. Yeni bilgi mimarisi

### 4.1 Üst durum çubuğu

Tek satırda yalnız:

- Profil adı ve Test/Canlı rozeti.
- Görev/aşama ve süre.
- Kamera, Pico, E-Stop için üç kompakt durum göstergesi.
- Mühendis Paneli.
- Saat.

`ENGEL`, `FIRE`, `ACTUATOR` gibi aynı gerçeği tekrar eden alanlar ayrı büyük
kutular olmayacak. En yüksek öncelikli engel tek bir durum cümlesinde
gösterilecek; ayrıntısı tooltip/drawer içinde açılacak.

### 4.2 Ana operasyon alanı

Varsayılan oran:

- Sol `%62`: canlı kamera ve hedef overlay'i.
- Sağ `%38`: 3B dijital ikiz.

Her panelde yalnız bir başlık satırı bulunacak. İç içe iki kamera başlığı,
tekrarlanan `KAMERA ÖNİZLEME AKTİF`, çözünürlük ve adapter rozetleri
kaldırılacak.

Operatör kamera panelinde:

- Canlı görüntü.
- Bbox, hedef kimliği ve güven.
- Seçili hedef vurgusu.
- Gerekirse tek hata/uyarı bandı.
- Tam ekran butonu.

3B sahnede:

- Taret ve hedefler.
- Kamera FOV aç/kapat.
- Hedefe odaklan.
- Operatör için tek görünüm seçimi.

CAD/asset/debug, anchor ve ayrıntılı görünüm seçenekleri mühendis paneline
taşınacak.

### 4.3 Alt operasyon dock'u

Ekranın altında sabit, tek satırlı eylem alanı:

- Hedef seç/temizle.
- Takibi başlat/durdur.
- FIRE ve engel reason code'u.
- Büyük ve ayrı SAFE STOP.

`Seçili hedef`, `Takip`, `FIRE`, `Görev` özet kutuları eylem dock'uyla
birleştirilecek. Aynı bilgiler hem strip hem butonlarda tekrar edilmeyecek.

### 4.4 Mühendis paneli

Sağdan açılan drawer ve beş sekme:

1. Kamera
2. Algılama
3. Hareket
4. Kalibrasyon
5. Kayıtlar

Kamera/model seçimi, confidence, PID, asset/CAD debug, replay ve raw reason
listeleri yalnız burada bulunacak. Drawer kapalıyken operatör görünümünde yer
tutmayacak.

## 5. Kaldırılacak veya taşınacak fazlalıklar

| Mevcut öğe | Karar |
|---|---|
| İki ayrı kamera başlık/toolbar katmanı | Tek panel başlığına indir |
| `READ ONLY`, `3D DÜNYA AKTİF`, `HEDEF YOK` tekrarları | Bağlamsal tek durum satırı |
| Adapter adı ve çözünürlük rozetleri | Mühendis paneline taşı |
| `truth`, fixture ve evidence teknik metinleri | Operatörden kaldır; log/debug içinde koru |
| Kamera seç/yenile/bağlan/durdur butonları | Mühendis drawer veya Setup |
| CAD asset ve anchor ayrıntıları | Kalibrasyon sekmesine taşı |
| `v-if="false"` eski mission grid'leri | Koddan tamamen kaldır |
| Uzun Phase 43–55 yorum/uyumluluk kalıntıları | Test kanıtına taşı, template'ten kaldır |
| Aynı reason code'un üst bar, strip ve butonda tekrarı | En fazla iki yerde: durum + ilgili komut |
| Operatör ekranındaki İngilizce teknik etiketler | Türkçe ürün dili; reason code değişmeden kalır |

## 6. Uygulama sırası

### Dilim 89.1 — Kamera doğruluğu ve temel bileşenler

- Profil kamerası ile browser camera çift sahipliğini kaldır.
- Stale kareyi `kamera hazır` sayma.
- `AppCard`, `StatusPill`, `ReasonBanner`, `ActionButton` temel bileşenlerini
  oluştur.
- Reka UI, Lucide ve VueUse bağımlılıklarını ekle.

### Dilim 89.2 — Operatör kokpiti

- Üst durum çubuğunu sadeleştir.
- Kamera/3B ana grid'ini yeniden kur.
- Alt operasyon dock'unu oluştur.
- Tek ekrana sığan 1920×1080 ve 1366×768 yerleşimini tamamla.

### Dilim 89.3 — Mühendis drawer

- Mevcut teknik panelleri drawer sekmelerine taşı.
- Tekrarlanan kamera/model kontrollerini birleştir.
- Operatör görünümünden raw debug metinlerini kaldır.

### Dilim 89.4 — Temizlik ve performans

- Kullanılmayan component/import/computed/CSS ve `v-if="false"` bloklarını sil.
- Polling çağrılarını tek merkezde birleştir; aynı endpoint'i aynı anda isteyen
  tekrarları kaldır.
- Three.js render döngüsü ve kamera MJPEG akışının birbirini yavaşlatmadığını
  ölç.

## 7. Kabul kriterleri

- Profil seçilip Test başlatıldığında kayıtlı kamera 3 saniye içinde güncel
  kare üretir veya kesin `CAMERA_*` reason code gösterir.
- Aynı fiziksel kamera tarayıcı ve backend tarafından otomatik olarak iki kez
  açılmaz.
- Operatör ekranında ilk bakışta en fazla dört ana eylem bulunur.
- Kamera ve dijital ikiz 1920×1080 ile 1366×768'de scroll olmadan görünür.
- SAFE STOP hiçbir drawer/modal arkasında kalmaz.
- FIRE engelliyse buton üzerinde ilgili kesin reason code erişilebilir olur.
- Mühendis paneli kapalıyken kamera path'i, backend adapter'ı, model path'i,
  PID ve CAD debug metni görünmez.
- Klavye ile bütün ana eylemlere erişilir; focus/hover/disabled halleri açıkça
  ayırt edilir.
- `pnpm typecheck`, production build ve mevcut gateway/safety testleri geçer.
- Donanım geldiğinde kamera hotplug, Pico reconnect, hareket ve boş-hazne tetik
  testleri HIL listesine eklenir.

## 8. Uygulama dışı bırakılanlar

- Bu UI diliminde CommandGateway protokolü değiştirilmeyecek.
- Dijital ikizin balistik/menzil modeli yeniden yazılmayacak.
- Docker/Windows native device-agent bu planın içinde uygulanmayacak; UI ve
  profil yolları bu dağıtım modeline uyumlu tutulacak.
- Donanım olmadan fiziksel hareket/FIRE başarılı kabul edilmeyecek.

## 9. Tamamlanma kanıtı

- Profil kamerası ile browser kamera çift sahipliği kaldırıldı; browser kamera
  yalnız açık mühendislik fallback'i olarak başlatılabilir.
- Firefox/GPU altında siyah kalabilen uzun ömürlü MJPEG kokpit katmanı yerine
  `no-store` tek-kare JPEG akışı kullanılıyor. Bütün önizleme tüketicileri aynı
  profil-sahipli capture worker'ın güncel kare kopyasını okuyor.
- Gerçek kamera seçiliyken mock/fixture vision olayları kamera HUD'una veya 3B
  sahneye hedef olarak bindirilmiyor.
- Stale kare kamera-ready kanıtı üretmiyor; backend MJPEG ilk güncel kareyi
  oluşturabilmek için profil kamerası seçildiğinde deadlock olmadan açılıyor.
- Operatör kokpiti iki ana panel ve tek eylem dock'una indirildi. Teknik kamera,
  algılama, hareket, kalibrasyon ve kayıt kontrolleri Reka UI drawer'a taşındı.
- Dahili `DRY_RUN/LIVE_TEST/COMPETITION` ve `stage1/2/3` değerleri operatöre
  `TEST/CANLI TEST/YARIŞMA` ve `AŞAMA 1/2/3` olarak gösteriliyor; reason code'lar
  makinece okunabilir biçimde korunuyor.
- `pnpm typecheck` ve production build geçti.
- Phase 37, 39, 83 ve 89 kamera/kokpit sözleşme paketi: 21 test geçti.
- Görsel kabul kanıtları:
  - `reports/screenshots/phase89_modern_operator_cockpit/operator_1920x960.png`
  - `reports/screenshots/phase89_modern_operator_cockpit/operator_1366x768.png`
  - `reports/screenshots/phase89_modern_operator_cockpit/engineer_drawer_1366x768.png`
- Gerçek kamera hotplug, Pico reconnect, fiziksel pan/tilt/FOV eşleşmesi ve
  E-Stop saha doğrulaması `reports/HIL_PICO_TARET_KABUL_TESTI.md` içindeki
  HIL-19'a kaydedildi.
