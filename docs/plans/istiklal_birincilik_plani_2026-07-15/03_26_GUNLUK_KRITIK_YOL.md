# 03 — 26 Günlük Kritik Yol: 15 Temmuz–10 Ağustos

## 1. Planlama kuralı

Bu takvim video teslimi için hazırlanmıştır. Tarihler kayabilir; kapıların sırası kayamaz. Bir blok kabul kriterini geçmeden sonraki bloktaki riskli özellik ana video dalına alınmaz.

Plan onayı 15 Temmuz’dan sonra gelirse yeni özellikler azaltılır; E-Stop, Y2–Y5 ve teslim tamponu sıkıştırılmaz.

## 2. Kritik yol özeti

    Onay ve sahiplik
    → Golden baseline ve donanım gerçeği
    → Fiziksel E-Stop ve kanonik firmware
    → SafetyDecision + CommandGateway
    → Y2/Y3/Y4/Y5 ayrı acceptance
    → Tam video provası
    → Feature freeze
    → Çekim, kurgu, upload ve KYS

## 3. Tarihli uygulama planı

### 15 Temmuz — G0: Plan onayı ve savaş odası

Amaç:

- Bu planı onaylamak veya değiştirmek.
- Rol sahiplerini ve günlük karar saatini belirlemek.
- ÖTR/KTR puanlarını, final PC’yi, aktif firmware’i ve model durumunu toplamak.

Çıktılar:

- İsimlendirilmiş rol tablosu.
- P0 görev sahipleri.
- Tek iletişim/karar kanalı.
- Ana dal ve deney dalı kuralları.

Kapı:

- Güvenlik, firmware, kontrol, test ve saha sorumlusu belli değilse fiziksel çalışma başlamaz.

### 16–17 Temmuz — G1: Golden baseline ve gerçek sistem envanteri

Görevler:

- GOV-03 golden baseline manifesti.
- SAFE-01 gerçek güç/pin/kablo denetimi.
- OPS-01 ebat ölçümü.
- OPS-02 CO₂/atış bütçesi başlangıç ölçümü.
- PLAT-01 disk/artefact sınıflaması.
- Mevcut iki balon davranışını servo/tetik enerjisi kontrollü biçimde yeniden üretmek.

Çıktılar:

- Commit, config, model, firmware, cihaz ve launcher hash’leri.
- Fotoğraflı pin/power sözleşmesi.
- Final konfigürasyonu ölçü formu.
- Baseline çalıştırma ve geri dönüş yönergesi.
- En az 10 baseline denemesinin sonucu.

Kapı:

- Hangi firmware’in ve hangi pinlerin gerçek sistemi yönettiği kesin değilse canlı atış yok.
- Baseline tekrar üretilemiyorsa geniş refactor yok; önce çalışan zincir bulunur.

### 18–20 Temmuz — G2A: E-Stop ve kanonik firmware

Görevler:

- SAFE-02 tek firmware/protokol seçimi.
- SAFE-03 hareket enerjisi E-Stop doğrulaması.
- SAFE-04 tetik/aktüatör enerjisi E-Stop doğrulaması.
- SAFE-09 watchdog, timeout ve stale queue davranışı.
- PLAT-04 Pico handshake/uyumluluk tasarımı.

Çıktılar:

- Tek pin profili ve firmware build hash’i.
- E-Stop aktifken motor ve tetik enerjisi ölçümü.
- Başlangıç, E-Stop, reset, watchdog ve reconnect durum diyagramı.
- Servo/tetik enerjisi kapalı masaüstü HIL testleri.

Kapı:

- E-Stop tetik enerjisini yazılımdan bağımsız kesmiyorsa Y4 çekimi ve canlı atış NO-GO.

### 21–24 Temmuz — G2B: Tek güvenli komut zinciri

Görevler:

- SAFE-05 CommandGateway.
- SAFE-06 görev bağlamlı SafetyDecision politikaları.
- SAFE-07 doğrudan write bypass’larını kaldırma.
- SAFE-08 limit, home ve ayrı hareket/atış yasak bölgeleri.
- SAFE-11 DRY_RUN, fiziksel arm ve kısa ömürlü full-active izin.
- PLAT-10 tek producer ve stale-frame kapanışı.
- EVD-01 ortak run/event ID.

Çıktılar:

- Tracking veya API’den doğrudan serial/fire çağrısı kalmadığını gösteren statik tarama.
- Aynı snapshot için deterministik karar.
- Her NO-FIRE durumunda sabit reason code.
- E-Stop çözülünce eski komut replay edilmemesi.
- Kamera/Pico/model/track stale olduğunda safe stop.

Kapı:

- Her fiziksel komut tek gateway’den geçmiyorsa saha testi yok.
- DRY_RUN gerçek tetik çıkışı üretebiliyorsa saha testi yok.

### 25–27 Temmuz — G3A: Cihaz, operatör gerçeği ve video Y1

Görevler:

- PLAT-05 kamera kalıcı kimliği ve hotplug.
- PLAT-06 golden OS kararı.
- PLAT-07 offline launcher ve Quick Preflight.
- PLAT-11 fail-closed runtime readiness.
- VID-01 gerçek operatör ekranı.
- Y1 anlatım provası.

Çıktılar:

- Kod/config değiştirmeden Pico ve kamera yeniden keşfi.
- Tek çekim bilgisayarında dondurulmuş çalışma paketi.
- Beş dakika altında Quick Preflight.
- Kamera, Pico, E-Stop, mod, track ve NO-FIRE nedeni gerçek runtime’dan görünür.

Kapı:

- UI mock/dev verisi gösteriyorsa Y1 hazır değildir.
- Windows zorunluysa bu tarihe kadar temiz yeniden başlatma testi geçmelidir; değilse Linux golden rig dondurulur.

### 28 Temmuz–1 Ağustos — G3B: Zorunlu fiziksel yetenekler

Görevler:

- VID-02 ölçülü 15 m.
- VID-03 hareket E-Stop.
- VID-04 ateş E-Stop.
- VID-05 iki eksenli hareketli takip.
- SAFE-10 birleşik güvenlik kabulü.

Minimum test:

- Y2: en az 5 deneme, en az 4 başarı; çekim öncesi hedef 9/10.
- Y3: üç ardışık temiz prova.
- Y4: üç ardışık temiz prova.
- Y5: üç ardışık 10–15 saniyelik temiz prova.
- Her run: video, config/model/firmware hash, run ID ve log.

Kapı:

- Y1–Y5’ten biri kırmızıysa Y6 ana dala alınmaz.

### 2 Ağustos — Y6 ve platform go/no-go günü

Kararlar:

- VID-06 opsiyonel sınıflandırma videoya girecek mi?
- Windows dönüşümü devam edecek mi?
- Zorunlu akışta hangi commit/video rig dondurulacak?

Y6 yalnız şu durumda GO:

- 4 sınıf × 3 mesafe matrisi kayıtlıdır.
- 15 m etiketi kararlıdır.
- Inference, Y5 kontrol döngüsünü bozmaz.
- Zorunlu beş yetenek iki tam provada yeşildir.

Aksi halde Y6 videodan çıkarılır; final Aşama 3 çalışması ayrı dalda sürer.

### 3–4 Ağustos — G4: Tam kostümlü prova ve feature freeze

Görevler:

- VID-09 aynı PC, kablo, güç, kamera, E-Stop, hedef ve çekim ekipmanıyla iki tam prova.
- 4:30 hedef süreli storyboard.
- Ses, başlık, numara, geniş plan ve mesafe kanıtı kontrolü.
- P0 dışı bütün merge’leri durdurmak.

Hard feature freeze:

- 4 Ağustos 18:00.
- Sonrasında yalnız video bloklayıcı hata, güvenlik ve teslim düzeltmesi.
- Yeni model, yeni UI, refactor veya platform değişimi yok.

Kapı:

- İki tam prova 5 dakikanın altında değilse çekime geçilmez; storyboard sadeleştirilir.

### 5–7 Ağustos — G5A: Final çekim

5 Ağustos:

- Son güvenlik/mesafe/cihaz kalibrasyonu.
- Her yeteneğin bir temiz teknik provası.

6 Ağustos:

- Ana çekim günü.
- Y2/Y3/Y4 için kesintisiz geniş plan.
- Her kritik bölüm için en az üç temiz take.

7 Ağustos:

- Yalnız eksik veya teknik açıdan geçersiz bölüm için yedek çekim.
- Yeni özellik yok.

Her gün sonunda:

- Ham görüntü iki ayrı diske kopyalanır.
- Dosya hash ve çekim notu alınır.
- İlgili run ID/log paketiyle eşlenir.

### 8 Ağustos — G5B: Kurgu ve bağımsız teknik kontrol

- Y1–Y5 resmî sırada.
- Her bölüm açık numaralı.
- 2–5 dakika; hedef 4:00–4:40.
- En az 1080p H.264 çıktı.
- Kritik fiziksel olaylarda yanıltıcı kesme yok.
- Açıklama zaman damgaları hazırlanır.
- Şartnameyi okumamış iki ekip üyesi videoyu kontrol eder.

### 9 Ağustos — Upload ve KYS prova teslimi

- YouTube liste dışı yükleme.
- Oturum kapalı iki cihaz ve iki ağdan link testi.
- 720p/1080p işleme tamamlanma kontrolü.
- Başlık, açıklama ve zaman damgası kontrolü.
- KYS’ye prova girişi; ekran görüntülü kanıt.
- Video, açıklama, link ve ham dosyaların yedeği.

### 10 Ağustos — İç teslim 12:00, resmî teslim 17:00

- Yeni çekim veya özellik planlanmaz.
- Sabah link ve KYS kontrolü.
- İç son teslim 12:00.
- 12:00–17:00 yalnız platform, bağlantı veya hesap sorunu tamponudur.
- KYS gönderim ekranı ve doğrulama e-postası/ekranı arşivlenir.

## 4. Video sonrası final kritik yolu

Finalin kesin günü bağlam paketinde olmadığı için bu bölüm 24 Ağustos finalist duyurusunda resmî tarihe göre yeniden bazlanır. Takım duyuruyu bekleyip iki hafta kaybetmez.

### 11–16 Ağustos — Güvenli ortak çekirdek ve Aşama 1

- Video release’ini etiketle ve koru.
- A1-01…A1-05.
- A2-01 çoklu tracker başlangıcı.
- A3-01 gerçek veri/target revision capture.
- OPS-02 CO₂/atış bütçesi.

Kapı: Manuel modda otonom fiziksel komut sıfır; ilk tam Aşama 1 turları.

### 17–23 Ağustos — Aşama 1 kabulü ve Aşama 2 dikey dilimi

- A1-06 son 10 tur.
- A2-01…A2-03: üç track, association ve time-to-exit.
- A3-02/A3-03 gerçek body model ve class mapping.
- EVD-01/EVD-02 evidence ve requirement matrisi.

Kapı: Aşama 1 90+ trendi; Aşama 2 dry-run üç hedefi doğru kimlikle koruyor.

### 24 Ağustos — Finalist duyurusu ve takvim rebase

- Final tarihi, saha/lojistik ve resmî güncellemeleri kilitle.
- Kalan kişi-gün ve tedarik kapasitesine göre backlog yeniden sırala.
- Birincilik hedefi korunur: A1 95+, A2 105+, A3 120+.

### Final T-5/T-4 hafta — Aşama 2 105+ ve Aşama 3 algı

- A2-04…A2-07.
- A3-04 IFF, A3-05 association, A3-06 range.
- A2 üç adet dört-turluk acceptance.

Kapı: Aşama 2 her seride 105+; Aşama 3 replay’de dost/ambiguous fire sıfır.

### Final T-4/T-3 hafta — Aşama 3 karar ve fiziksel dikey dilim

- A3-07 engagement manager.
- A3-08 dost güvenliği regresyonu.
- A3-09 turn/reacquire/miss-streak.
- Önce HIL, sonra kontrollü tek düşman fiziksel acceptance.

Kapı: Body→IFF→Link→Range→Safety→Fire tek hedefte uçtan uca ve açıklanabilir.

### Final T-3/T-2 hafta — Sekiz tur ve saha operasyonu

- A3-10 üç tam sekiz-turluk seri.
- OPS-03 30 dakika kurulum/10 dakika bakım.
- OPS-01 final ebat tekrar ölçümü.
- Tam A1→A2→A3 günleri ve CO₂ pit planı.

Kapı: A3 120+, dost vuruşu sıfır; üç ardışık miss yok.

### Final T-2/T-1 hafta — Güvenilirlik ve jüri

- Son iki full competition day.
- KTR fark matrisi, final sunumu ve teknik mülakat.
- Spares, kablo, tüp, şarjör, kalibrasyon ve release dossier.
- Son performans dışı risklerin kapatılması.

### Final haftası — Hard freeze

- Yeni model, firmware, OS, mekanik veya büyük threshold değişikliği yok.
- Yalnız son release’e karşı kanıtlı bloklayıcı düzeltme.
- Aynı PC, kamera, Pico, firmware, config, model ve kablo seti.
- Günlük kısa preflight; fiziksel sistemi yıpratacak gereksiz atış yok.

## 5. Günlük çalışma ritmi

Sabah 15 dakika:

- P0 sağlık durumu.
- Dün kapanan kabul testleri.
- Bugünkü tek kritik kapı.
- Donanım ve saha erişimi.

Her değişiklik:

- Önce dry-run/replay.
- Sonra HIL, tetik enerjisi kapalı.
- Güvenlik sorumlusu onayı sonrası kontrollü fiziksel test.
- Başarılı commit/tag ve kanıt linki.

Akşam 20 dakika:

- Kırmızı/sarı/yeşil görev tablosu.
- Çalışan geri dönüş commit’i.
- Disk alanı, CO₂ sayacı ve cihaz durumu.
- Ertesi gün go/no-go kararı.

## 6. Kritik gecikme halinde kesilecek işler

Sırayla kesilir:

1. Y6 video bölümü.
2. Windows dönüşümü, Linux golden rig çalışıyorsa.
3. Yeni Setup Wizard özellikleri; yalnız Quick Preflight bırakılır.
4. Gelişmiş overlay ve rapor otomasyonu.
5. P0 olmayan refactor.

Kesilmeyecek işler:

- Fiziksel E-Stop.
- Tek CommandGateway.
- Y2, Y3, Y4, Y5 acceptance.
- Video formatı/link/KYS kontrolü.
- En az iki günlük teslim tamponu.
