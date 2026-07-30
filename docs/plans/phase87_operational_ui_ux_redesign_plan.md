# Phase 87 — Operasyonel UI/UX Yeniden Tasarım Planı

Tarih: 2026-07-16

Durum: Yazılımsal uygulama tamamlandı; gerçek donanım HIL kabulü bekleniyor.

## 1. Sonuç ve ürün kararı

Mevcut arayüz görsel olarak güçlü bir temele sahip olsa da aynı operasyonel
gerçek birçok yerde tekrar ediliyor, normal operatöre mühendislik kontrolleri
gösteriliyor ve Setup Wizard'ın bazı "donanım testleri" gerçek CommandGateway
yoluna değil yalnız dry-run cevaplarına bağlı bulunuyor.

Phase 87'nin hedefi yeni bir tema giydirmek değil; sistemi üç açık çalışma
alanına ayırmaktır:

1. **Başlangıç:** Yalnız `DRY RUN` veya `LIVE HARDWARE` niyeti seçilir.
2. **Kurulum:** Donanım ve preflight eksikleri dört sade adımda giderilir.
3. **Kokpit:** Operatör yalnız görev kararlarını, mühendis yalnız açtığı teknik
   paneli görür.

`LIVE HARDWARE`, gerçek hareket ve gerçek ateş yolunu seçilebilir hale getirir.
Bu seçim tek başına fiziksel çıkış üretmez. Hareket ve ateş yine yalnız
CommandGateway'in görünür preflight koşulları sağlandığında üretilir. Kaynak
kod, environment veya gizli feature flag değişikliği gerekmez.

## 2. Değiştirilmeyecek güvenlik ve görev sözleşmeleri

- Bütün fiziksel hareket ve ateş komutları CommandGateway üzerinden kalır.
- `DRY_RUN` seçilebilir bir test modudur; kalıcı sistem kilidi değildir.
- `LIVE_TEST` ve `VIDEO_DEMO` için Aşama 1 planı/timer gerekmez; Pico, E-Stop,
  kamera freshness, hareket sınırları ve actuator arm hazır olduğunda gerçek
  manuel hareket/ateş çalışabilir.
- `STAGE1_COMPETITION` hedef sırası, read-back, sıra kilidi ve yarışma timer'ı
  ister. Timer başlamadan hareket/ateş yoktur; tracking fiziksel komut üretemez.
- `STAGE2_COMPETITION` ve `STAGE3_COMPETITION`, Aşama 1 planı ve timer'ından
  bağımsızdır.
- Bir readiness koşulu eksik olduğunda bütün uygulama kilitlenmez. Yalnız ilgili
  fiziksel komut engellenir ve kesin reason code gösterilir.
- E-Stop/safe-stop her ekrandan erişilebilir kalır; görsel sadeleştirme bu
  kontrolü gizlemez.
- UI hiçbir fixture, mock, surrogate veya tahmin durumunu gerçek donanım
  durumuymuş gibi göstermez.

## 3. Mevcut ekran ve gerçeklik envanteri

### 3.1 Başlangıç ekranı

Ana dosya: `frontend/src/views/LandingView.vue`

Korunacak güçlü parçalar:

- Sinematik arka plan ve taret hero görseli.
- İSTİKLAL marka dili, saat ve tek güçlü başlangıç CTA'sı.
- Gerçek cihaz/runtime store'larından durum yenileme altyapısı.

Sorunlar:

- `DRY-RUN / NO TX` metni sabit yazılmıştır.
- `startCockpit()` yalnız localStorage ve query-string değiştirir; gerçek
  CommandGateway profilini seçmez.
- Pico bağlantı, komut ve telemetri satırları `OFFLINE BEKLENEN`, `SIM MODU` ve
  `MOCK` gibi metinlerle teşhis gösterir ama bağlantı/düzeltme aksiyonu yapmaz.
- 3B dijital ikiz durumu sabit `OK` değeridir.
- Manuel/otonom, hedef önceliği ve operatör/mühendis seçimleri görev bağlamı
  belirlenmeden önce sorulur.
- Asset adı, model adı ve benzeri mühendislik ayrıntıları başlangıç ekranında
  gereksizdir.

### 3.2 Setup Wizard

Ana dosyalar:

- `frontend/src/views/SetupCenterView.vue`
- `frontend/src/api/setupWizard.ts`
- `backend/app/api/setup.py`

Sorunlar:

- Sekiz adım vardır; aynı ekranda çok sayıda teknik buton, alan ve raw sonuç
  gösterilir.
- Kamera izin, tarayıcı envanteri, backend envanteri, capture release, preview,
  apply ve reset ayrı üst düzey eylemlerdir.
- Pico connect, heartbeat ve ACK üç ayrı operatör eylemidir.
- Raw JSON ve model yolu/confidence gibi bilgiler normal kullanıcıya açıktır.
- Motor yön düğmeleri ve aktüatör checklist'i setup akışını gereksiz ağırlaştırır.
- `/api/setup/pico/connect`, `/heartbeat`, `/ack-test`, `/motor/test` ve
  `/actuator/safe-test` fiziksel Gateway yolunu doğrulamaz; no-TX/dry-run sonucu
  üretir.
- Frontend `SetupSafetyResponse` ve backend `SetupProfile.safety` fiziksel komutu
  tip seviyesinde sürekli `false` kabul eder. Bu yapı gerçek LIVE kurulumu temsil
  edemez.

### 3.3 Operator ve Engineer Cockpit

Ana dosyalar:

- `frontend/src/views/CockpitView.vue`
- `frontend/src/components/cockpit/CockpitTopBar.vue`
- `frontend/src/components/cockpit/SafetyModeBanner.vue`
- `frontend/src/components/cockpit/EngineerTechnicalTabs.vue`

Sorunlar:

- Topbar dokuz küçük durum kartı gösterir; kamera toolbar, operasyon strip, alt
  banner ve mühendis paneli aynı gerçekleri tekrarlar.
- Topbar açıklaması ve bazı badge'ler `read-only/no physical command` varsayımına
  sabitlenmiştir.
- Operator kamera alanında cihaz, refresh, bağlan, durdur ve YOLO gibi kurulum
  kontrolleri vardır.
- Alt `SafetyModeBanner`, gerçek ve değerli CommandGateway kontrollerini içerir;
  fakat sürekli açık kaldığı için kokpitin ana görevini ezer.
- Operator operasyon strip'i boş `n/a/none` değerleri dahil sekiz alan gösterir.
- Dijital ikiz debug çizgileri ve teknik etiketleri normal operatör görünümünde
  gereğinden fazladır.
- Engineer sekmeleri doğru bir başlangıçtır; fakat sabit sayfa yoğunluğu içinde
  aynı anda çok fazla teknik bilgi görünür.

### 3.4 Uygulama kabuğu ve legacy sayfalar

Ana dosyalar:

- `frontend/src/components/layout/AppShell.vue`
- `frontend/src/router/index.ts`

Sorunlar:

- Router'da 25'ten fazla ekran vardır.
- Normal navigasyonda Debug, Eski Konsol ve Gelişmiş Sayfalar öne çıkar.
- Shell header dokuz canlı badge ile tekrar bilgi yoğunluğu oluşturur.
- Legacy route'ların açık kalması test/kanıt için yararlı olabilir; normal
  operatöre gösterilmeleri gerekli değildir.

## 4. Bilgi mimarisi

Normal kullanıcı akışı:

```text
Başlangıç
  ├─ DRY RUN
  │    └─ Operator Cockpit
  └─ LIVE HARDWARE
       ├─ readiness eksik → 4 adımlı Kurulum
       └─ readiness hazır → Görev Başlat → Operator Cockpit

Operator Cockpit
  ├─ Görev kontrolü
  ├─ Kamera + dijital ikiz
  ├─ Tek readiness/engel özeti
  ├─ Kanıt olayı/replay
  └─ Mühendis Panelini Aç

Mühendis Paneli
  ├─ Devices
  ├─ Vision
  ├─ Motion
  ├─ Calibration
  └─ Evidence / Logs
```

Normal ana navigasyon en fazla şu öğeleri gösterir:

- Kokpit
- Kurulum
- Kanıtlar
- Mühendis Paneli

Debug, legacy console ve alan bazlı eski sayfalar router'da geçici olarak kalır;
yalnız Mühendis Paneli içindeki "Gelişmiş araçlar" bölümünden açılır.

## 5. Ortak görsel ve etkileşim sözleşmesi

- Renk dekorasyon değil anlam taşır:
  - yeşil: hazır/başarılı,
  - amber: eksik/engelli ama uygulama kullanılabilir,
  - kırmızı: E-Stop, fault veya kritik kopma,
  - cyan: seçim ve nötr canlı veri.
- Durum yalnız renkle anlatılmaz; ikon, kısa metin ve reason code birlikte görünür.
- Yanıp sönen ışık yalnız gerçek acil durumda kullanılabilir.
- Operator ekranında boş `n/a`, `none` veya `0` kartları gösterilmez.
- Her ekranda birincil eylem sayısı bir olur. Safe-stop/E-Stop bundan bağımsız,
  sürekli erişilebilir güvenlik eylemidir.
- Teknik ham veri varsayılan olarak gizlidir; "Teknik ayrıntı" disclosure veya
  Mühendis Paneli içinde açılır.
- Sabit dekoratif badge yerine değişiklik olduğunda anlamlı durum satırı/toast
  kullanılır.
- Aynı gerçek aynı ekranda bir kez gösterilir.
- Minimum hedef çözünürlük 1366×768; ana doğrulama 1440×900 ve 1920×1080'de
  yapılır.

Yoğunluk bütçesi:

| Ekran | Üst düzey durum | Birincil eylem | Sürekli görünen kontrol |
|---|---:|---:|---:|
| Başlangıç | 4 readiness satırı | 1 | 2 mod kartı |
| Setup adımı | 3 ana kart | 1 | geri + yeniden tara |
| Operator | 4 üst durum + 4 alt özet | 1 görev eylemi | en çok 3 operasyon kontrolü + safe-stop |
| Engineer | Operator görünümü + 1 drawer | sekme başına 1 | aynı anda 1 teknik panel |

## 6. Yeni başlangıç ekranı

### 6.1 Wireframe

```text
┌──────────────────────────────────────────────────────────────────────┐
│ İSTİKLAL C2                                      saat / backend      │
│ HAVA SAVUNMA SİSTEMİ                                                │
│                                                                      │
│  ┌─ SİSTEM HAZIRLIĞI ─────────┐           [taret hero görseli]       │
│  │ Backend       HAZIR        │                                      │
│  │ Kamera        HAZIR        │                                      │
│  │ Pico + E-Stop BAĞLI DEĞİL  │  → Kur                              │
│  │ Hareket/Tetik PREFLIGHT YOK│  → Kontrol et                       │
│  └────────────────────────────┘                                      │
│                                                                      │
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ DRY RUN             │  │ LIVE HARDWARE                        │  │
│  │ Fiziksel komut yok  │  │ Gerçek hareket + gerçek ateş         │  │
│  │ Laptop kamera uygun │  │ Gateway preflight koşullarına bağlı  │  │
│  └─────────────────────┘  └──────────────────────────────────────┘  │
│                                                                      │
│                  [ SEÇİLEN MODDA DEVAM ET ]                          │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Gerçek readiness satırları

| Satır | Gerçek kaynak | Gösterilecek eylem |
|---|---|---|
| Backend | WebSocket/health ve system store | `Yeniden bağlan` |
| Kamera | `/api/devices`, `/api/camera/runtime/status` | `Kamera kur` veya `Yeniden tara` |
| Pico + E-Stop | `/api/safety/command-profile`, Gateway preflight gates | `Pico bağla` / `E-Stop'u kontrol et` |
| Motion + Actuator | `/api/motion/status`, Gateway preflight gates | `Preflight aç` / `Arm et` |

Readiness satırı tıklanınca yalnız açıklama açmak yerine tek gerçek eylem
çalıştırır veya Setup'ın doğru adımına gider. UI çözümü shell komutu olarak
uydurmaz; backend'in reason code ve suggested action bilgisini kullanır.

### 6.3 Mod seçimi davranışı

- `DRY RUN` seçildiğinde `POST /api/safety/command-profile` ile gerçek
  `DRY_RUN` profili seçilir ve Operator Cockpit açılır.
- `LIVE HARDWARE` seçildiğinde UI canlı çalışma niyetini kaydeder.
  - Donanım eksikse dört adımlı Setup açılır.
  - Donanım hazırsa görev bağlamı seçimine geçilir.
- LIVE kartının alt metni açık olur: "Gerçek hareket ve ateş, yalnız preflight
  READY olduğunda etkin."
- Manuel/otonom, hedef sırası ve operatör/mühendis seçimi Landing'den kaldırılır.
- Hedef önceliği yalnız ilgili yarışma aşamasının görev başlatma akışında görünür.
- Engineer bir yetki kilidi değil, Cockpit içindeki görünüm tercihidir.

## 7. Dört adımlı Setup Wizard

### 7.1 Adım yapısı

```text
1. Çalışma bağlamı
   DRY RUN veya LIVE HARDWARE
   LIVE ise: Canlı Test / Video Demo / Yarışma

2. Donanım
   Kamera preview + Pico bağlantısı + E-Stop gerçek durumu

3. Algılama ve hareket
   Aktif model/surrogate + kamera freshness + düşük hızlı hareket doğrulaması

4. Kontrol et ve başlat
   Tek preflight özeti + actuator arm + göreve devam
```

### 7.2 Wizard wireframe

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Kurulum                           Adım 2 / 4        [Yeniden Tara]    │
│ ● Çalışma  ● Donanım  ○ Algılama  ○ Kontrol                          │
│                                                                      │
│  ┌─ Kamera ───────────────────┐  ┌─ Pico + E-Stop ────────────────┐ │
│  │ [canlı preview]            │  │ Pico adayı: /dev/ttyACM0      │ │
│  │ Laptop Camera · 1280×720   │  │ Durum: BAĞLI DEĞİL            │ │
│  │ HAZIR                      │  │ Reason: PICO_NOT_CONNECTED     │ │
│  │ [Kamerayı değiştir]        │  │ [Pico'yu Bağla ve Doğrula]    │ │
│  └────────────────────────────┘  └────────────────────────────────┘ │
│                                                                      │
│  Eksik: Pico bağlantısı                                              │
│                                             [ DEVAM ET ] disabled     │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.3 Sadeleştirme kuralları

- Cihaz envanteri otomatik çalışır; kullanıcıya tek `Yeniden Tara` verilir.
- Pico connect, PING/heartbeat, STAT/E-Stop ve ACK doğrulaması tek
  `Pico'yu Bağla ve Doğrula` akışında birleştirilir.
- Gerçek Pico eylemi `/api/safety/pico-connect` ve `/api/safety/preflight`
  üzerinden yapılır. `/api/setup/pico/*` dry-only akışı aktif kurulum kaynağı
  olmaktan çıkarılır.
- Kamera kartı cihaz adı, preview, frame freshness ve tek durum gösterir.
  Exposure/gain/white balance/resolution gibi ayarlar `Gelişmiş kamera ayarları`
  altında kalır.
- Model kartı yalnız aktif model, sınıflar ve doğrulama durumunu gösterir.
  Model yoksa `Model yüklü değil` ve `Model içe aktar` görünür.
- OpenCV circle surrogate yalnız DRY RUN'da açıkça `TEST SURROGATE` etiketiyle
  kullanılabilir; LIVE readiness'i üretim modeli gibi yeşile çeviremez.
- Motor testleri LIVE readiness sağlanmadan çalıştırılamaz. DRY RUN'da yalnız
  dijital ikiz preview olduğu açıkça yazılır.
- LIVE düşük hızlı hareket testi gerçek `/api/motion/jog` → CommandGateway
  yolunu kullanır ve fiziksel ACK sonucunu gösterir.
- Actuator arm, dördüncü adımda görünür tek kontroldür. Arm isteği
  `/api/safety/preflight` üzerinden yapılır.
- Setup profil JSON'u, path girişleri, ayrı heartbeat/ACK butonları ve uzun
  checklist normal akıştan kaldırılır.
- Profil otomatik kaydedilir. `Farklı kaydet`, baudrate ve ham log gibi alanlar
  yalnız mühendis ayrıntısındadır.
- Her `Devam et` engeli makinece okunabilir tek reason code ve insan okunabilir
  kısa açıklama taşır.

### 7.4 Setup backend düzeltmesi

`backend/app/api/setup.py` iki sorumluluğa ayrılacaktır:

1. Cihaz keşfi/profil kalıcılığı gibi gerçek ve zararsız setup yardımcıları.
2. Fiziksel komut gerektiren bütün işlemler için mevcut authoritative servisler.

Dry-only setup Pico/motor/actuator endpointleri ya kaldırılacak ya da geriye
uyumluluk için `410 Gone`/açık deprecation sonucu döndürerek yeni gerçek endpointi
işaret edecektir. Çalışan mock endpoint yeni UI tarafından kullanılmayacaktır.

## 8. Operator Cockpit

### 8.1 Wireframe

```text
┌──────────────────────────────────────────────────────────────────────┐
│ İSTİKLAL │ LIVE TEST │ GÖREV HAZIR │ E-STOP RELEASED │ 14:32:08     │
├─────────────────────────────────────┬────────────────────────────────┤
│                                     │                                │
│          KAMERA / OVERLAY           │        3B DİJİTAL İKİZ         │
│              %60                    │              %40               │
│                                     │                                │
├─────────────────────────────────────┴────────────────────────────────┤
│ Hedef: F-16 #17 │ Takip: KİLİTLİ │ FIRE: READY │ A2 · Tur 2 · 01:14 │
├──────────────────────────────────────────────────────────────────────┤
│ [Takibi Başlat/Durdur] [Hedef Seç] [FIRE]          [SAFE STOP]       │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.2 Operator bilgi önceliği

Üst bar yalnız şunları gösterir:

- çalışma modu/profil,
- görev/aşama,
- sistem `READY` veya tek birincil engel,
- gerçek E-Stop durumu.

Alt operasyon özeti yalnız şunları gösterir:

- seçili hedef,
- tracking/lock durumu,
- hareket/ateş readiness ve birincil reason code,
- görev/tur/süre.

Boş hedef veya görev değeri kart olarak gösterilmez; alan gerektiğinde ortaya
çıkar. Ayrıntılı bütün blocker listesi `Neden hazır değil?` popover'ında açılır.

### 8.3 Operator eylemleri

- Takibi başlat/durdur.
- İzin verilen görevde hedef seç.
- `LIVE_TEST/VIDEO_DEMO` veya Aşama 1 bağlamında izin verilen manuel FIRE.
- Safe-stop/E-Stop.
- Aşama 1 planı ve timer kontrolleri yalnız `STAGE1_COMPETITION` görev başlatma
  panelinde görünür.
- Aşama 2/3 görev kontrolleri Aşama 1 alanlarını hiç render etmez.

Kamera cihaz seçimi, model/YOLO ayarı, PID, baudrate, port ve calibration
Operator Cockpit'ten kaldırılır. Bir sorun oluşursa tek `Kurulumda düzelt`
aksiyonu Setup'ın doğru adımını açar.

### 8.4 Dijital ikiz sadeleştirmesi

Operator modunda yalnız şu öğeler sürekli görünür:

- taret ve gerçek pan/tilt pozu,
- kamera FOV/frustum,
- geçerli birleşik hedefler,
- seçili hedef/lock vurgusu,
- kabul edilmiş atış trajectory ve sonuç animasyonu.

Grid yoğunluğu, bbox projection debug, anchor adları, asset isimleri ve yardımcı
kinematik çizgiler yalnız Engineer görünümünde açılır.

## 9. Engineer Cockpit ve Mühendis Paneli

Engineer ayrı ve tekrarlı bir cockpit değildir. Aynı kamera/dijital ikiz sahnesi
üzerine sağdan açılan tek drawer'dır.

```text
┌──────────── Operator Cockpit ────────────┬──── Mühendis Paneli ──────┐
│                                          │ Devices | Vision | Motion │
│ Kamera + dijital ikiz + görev            │ Calibration | Evidence    │
│                                          │                           │
│                                          │ [yalnız aktif sekme]      │
└──────────────────────────────────────────┴───────────────────────────┘
```

Sekmeler:

- **Devices:** kamera, Pico, port, protocol, heartbeat ve E-Stop ayrıntısı.
- **Vision:** aktif model, sınıflar, threshold, FPS/latency ve test surrogate.
- **Motion:** pan/tilt, limits, driver, düşük hızlı jog/home ve Gateway ACK.
- **Calibration:** kamera/FOV/yön/range profilleri.
- **Evidence / Logs:** olaylar, shot replay, kanıt export ve ham log disclosure.

Aynı anda yalnız bir sekme açık olur. Başlangıçta drawer kapalıdır. Operator ve
Engineer görünümü arasında geçiş güvenlik profili veya fiziksel yetki değiştirmez.

## 10. DRY RUN / LIVE durum makinesi

```text
BOOTSTRAP
  ├─ backend yok ───────────────> DEGRADED_UI
  ├─ DRY RUN seçildi ───────────> DRY_READY
  └─ LIVE HARDWARE seçildi ─────> LIVE_SETUP_REQUIRED

LIVE_SETUP_REQUIRED
  ├─ cihaz eksik ───────────────> LIVE_BLOCKED(reason_code)
  └─ Pico connect + kamera ─────> PREFLIGHT_RUNNING

PREFLIGHT_RUNNING
  ├─ gate eksik ────────────────> LIVE_BLOCKED(reason_code)
  └─ tüm gate'ler + arm ────────> LIVE_READY

LIVE_READY
  ├─ görev başlat ──────────────> LIVE_ACTIVE
  ├─ E-Stop ────────────────────> ESTOP_ACTIVE
  ├─ heartbeat/camera stale ────> LIVE_BLOCKED(reason_code)
  └─ DRY RUN seç ───────────────> DRY_READY + gateway_safe_stop

ESTOP_ACTIVE / LIVE_BLOCKED
  ├─ uygulama ve kanıt ekranı açık kalır
  ├─ ilgili fiziksel komutlar NO_FIRE / NO_MOTION olur
  └─ sorun düzeldi + preflight ─> LIVE_READY
```

Profile matrisi:

| UI seçimi / görev | Gateway profili | Gerçek hareket | Gerçek FIRE | Ek görev koşulu |
|---|---|---:|---:|---|
| DRY RUN | `DRY_RUN` | Hayır | Hayır | Laptop kamera/surrogate kullanılabilir |
| LIVE HARDWARE · Canlı Test | `LIVE_TEST` | Preflight ile | Preflight + hedef/balon ile | Plan/timer yok |
| LIVE HARDWARE · Video Demo | `VIDEO_DEMO` | Preflight ile | Preflight + hedef/balon ile | Plan/timer yok |
| LIVE HARDWARE · Aşama 1 | `COMPETITION` | Timer sonrası manuel | Timer sonrası manuel | Plan + read-back + lock |
| LIVE HARDWARE · Aşama 2 | `COMPETITION` | Görev politikasına göre | Gateway otonom karar ile | Aşama 1'den bağımsız |
| LIVE HARDWARE · Aşama 3 | `COMPETITION` | Görev politikasına göre | Gateway IFF/karar ile | Aşama 1'den bağımsız |

## 11. API ve işlev eşleme tablosu

| UI ihtiyacı | Mevcut/doğru kaynak | Phase 87 kararı |
|---|---|---|
| Aktif profil ve preflight | `GET /api/safety/command-profile` | Tek otorite olarak kullan |
| DRY/LIVE profil seçimi | `POST /api/safety/command-profile` | Landing/Setup buraya bağlanır |
| Pico gerçek bağlantısı | `POST /api/safety/pico-connect` | Setup tek bağlantı eylemi |
| Preflight ve actuator arm | `POST /api/safety/preflight` | Setup 4. adım ve düzeltme drawer'ı |
| Cihaz envanteri | `GET/POST /api/devices[/refresh]` | Otomatik keşif ve tek yeniden tara |
| Kamera durumu/profili | `/api/camera/runtime/status`, `/profile` | Kamera readiness kaynağı |
| Kamera uygula/probe | `/api/camera/runtime/apply-profile`, `/probe-current` | Setup camera card |
| Vision aktif runtime | `/api/vision/runtime/status`, `/verify-active` | Model readiness kaynağı |
| Model paket yönetimi | `/api/models/packages/*` | Yalnız Setup advanced/Engineer |
| Hareket durumu | `GET /api/motion/status` | Operator özet ve Setup readiness |
| Gerçek/dry jog | `POST /api/motion/jog` | Gateway sonucuyla test; profile etiketi zorunlu |
| Acil durdurma | `POST /api/motion/stop` ve Gateway safe-stop yolu | Her ekranda erişilebilir |
| Eski setup Pico testleri | `/api/setup/pico/*` | Yeni UI kullanmaz; deprecate |
| Eski setup motor/actuator testleri | `/api/setup/motor/test`, `/actuator/safe-test` | Yeni UI kullanmaz; gerçek servise taşı/deprecate |

Readiness için UI'da ortak bir sözleşme oluşturulacaktır:

```text
OperationalReadinessItem
  key
  state = READY | BLOCKED | DEGRADED | UNKNOWN
  required_for = DRY_RUN | LIVE_MOTION | LIVE_FIRE
  reason_code
  message
  action_id
  source
  observed_at
  stale
```

Bu sözleşme mevcut authoritative endpointleri birleştiren read-only bir backend
readiness endpointi veya tek frontend store üzerinden üretilebilir. Tercih,
backend'de `GET /api/operations/readiness` read-only aggregator oluşturmaktır;
bu endpoint yeni güvenlik kararı vermez, yalnız mevcut Gateway/device/runtime
gerçeklerini normalize eder.

## 12. Kaldır / taşı / birleştir matrisi

| Mevcut öğe | Karar | Yeni yer |
|---|---|---|
| Landing manuel/otonom seçimi | Kaldır | Görev bağlamı |
| Landing hedef öncelik drag-drop | Kaldır | Aşama 1 görev başlatma |
| Landing Operator/Engineer kartları | Kaldır | Cockpit drawer toggle |
| Landing mock/sim Pico satırları | Değiştir | Gerçek readiness + düzelt aksiyonu |
| Landing asset/model ayrıntısı | Kaldır | Engineer paneli |
| Setup sekiz adım | Birleştir | Dört adım |
| Üç Pico test butonu | Birleştir | Tek bağla ve doğrula |
| Setup raw JSON | Kaldır | Engineer ham ayrıntı |
| Setup model path/confidence | Taşı | Advanced Vision |
| Setup PID/motion ham ayarları | Taşı | Engineer Motion |
| Cockpit dokuz top badge | Birleştir | Dört operasyonel durum |
| Cockpit kamera cihaz/YOLO toolbar | Taşı | Setup/Engineer Vision |
| Alt SafetyModeBanner | Taşı | Preflight drawer/modal |
| Operator sekizli boş strip | Birleştir | Dört bağlamsal özet |
| Dijital ikiz debug yardımcıları | Gizle | Engineer görünümü |
| Sidebar Debug/Legacy | Gizle | Engineer advanced links |
| Shell dokuz badge | Birleştir | Tek genel readiness + E-Stop |

## 13. Uygulama görev dilimleri

### 87A — Operasyonel gerçeklik katmanı ve tasarım temeli

- `OperationalIntent`, readiness item ve reason-code katalog tiplerini oluştur.
- CommandGateway, camera runtime, device inventory, vision ve motion gerçeklerini
  tek normalize readiness kaynağında birleştir.
- UI içindeki sabit `DRY-RUN`, `NO TX`, `MOCK`, sabit `OK` varsayımlarını
  envanterle ve kaldırılacak yerleri testle işaretle.
- Ortak durum bileşeni, tek aksiyon satırı, drawer ve kritik CTA primitives'i
  oluştur.
- Renk, tipografi, spacing ve yoğunluk token'larını mevcut sinematik tasarımla
  uyumlu hale getir.

Kabul:

- Aynı backend snapshot'ı Landing, Setup ve Cockpit'te aynı state/reason üretir.
- UI fixture durumunu `READY` gösteremez.
- Unknown/stale durum amber veya kırmızı ve açık reason code ile görünür.

### 87B — Landing yeniden inşası

- Landing'i iki mod kartı ve dört gerçek readiness satırına indir.
- `DRY RUN` seçimini gerçek profile API'ye bağla.
- `LIVE HARDWARE` seçiminden Setup/readiness akışına yönlendir.
- Her readiness satırına tek gerçek düzeltme eylemi ekle.
- Manuel/otonom, hedef sırası, rol seçimi, asset/debug ve ayrı 3B CTA'sını kaldır.

Kabul:

- Landing'de görülen bütün durumlar gerçek endpoint/store kaynağına izlenebilir.
- DRY RUN seçimi backend profilinde `DRY_RUN` olarak doğrulanır.
- LIVE seçimi kod/env değiştirmeden Setup'a ilerler.
- Donanım yokken `Pico bağlı` veya `Ateş hazır` gösterilemez.

### 87C — Gerçek dört adımlı Setup Wizard

- Setup'ı dört adımlı yapıya dönüştür.
- Kamera/device keşfini gerçek runtime API'leriyle birleştir.
- Pico'yu gerçek Gateway connect/preflight yoluna taşı.
- Model ve motion gelişmiş ayarlarını disclosure/Engineer alanına taşı.
- Tek preflight ve actuator arm sonucu üzerinden LIVE readiness üret.
- Eski dry-only setup endpointlerini yeni UI'dan çıkar ve deprecation testi ekle.

Kabul:

- Mock Pico contract testinde UI `Bağla ve Doğrula` sonrası Gateway gate'lerini
  birebir gösterir.
- Kamera stale ise ilerleme engeli `CAMERA_STALE`; yeni frame sonrası preflight
  yeniden çalıştırılarak hazır duruma dönülebilir.
- E-Stop aktifse yalnız live motion/fire hazırlığı engellenir; Setup ve uygulama
  kullanılmaya devam eder.
- DRY RUN akışı Pico istemeden tamamlanabilir.

### 87D — Operator Cockpit sadeleştirmesi

- Üst barı dört duruma indir.
- Kamera %60, dijital ikiz %40 ana yerleşimini responsive hale getir.
- Operator kamera toolbar ve teknik ayarlarını kaldır.
- SafetyModeBanner işlevlerini Preflight drawer'a taşı.
- Bağlamsal dört operasyon özetini ve izinli görev eylemlerini uygula.
- Stage 1/2/3 koşullu görünürlüğünü görev sözleşmesine göre ayır.
- Dijital ikiz normal/debug görünüm ayrımını uygula.

Kabul:

- Operator ana ekranında port, baudrate, model path, PID veya raw JSON yoktur.
- Aynı status iki ayrı kartta tekrar etmez.
- FIRE disabled ise buton üzerinde/bitişiğinde birincil exact reason code görünür.
- LIVE_TEST manuel hareket ve FIRE eylemleri gerçek Gateway cevaplarını gösterir.
- Aşama 1 timer başlamadan hareket/FIRE görünür biçimde engellidir.
- Aşama 2/3 ekranında Aşama 1 planı/timer alanı yoktur.

### 87E — Engineer drawer ve navigasyon temizliği

- EngineerTechnicalTabs'i sağ drawer mimarisine dönüştür.
- Devices, Vision, Motion, Calibration, Evidence/Logs sekmelerini bağla.
- Shell header ve sidebar status tekrarlarını kaldır.
- Debug/legacy/advanced route'ları normal navigasyondan gizle.
- Route'ları hemen silme; kullanım telemetrisi/test bağımlılığı denetiminden sonra
  deprecation listesi oluştur.

Kabul:

- Engineer drawer kapalıyken Operator ile aynı sade cockpit görünür.
- Aynı anda yalnız bir teknik sekme render edilir.
- Eski konsol normal operatör navigasyonunda bulunmaz.
- Legacy route'a doğrudan URL erişimi geçiş süresince korunur.

### 87F — Test, screenshot inceleme ve kabul

- Component/unit testleri: mode cards, readiness row, primary reason seçimi,
  conditional mission controls.
- API contract testleri: DRY profile, LIVE connect/preflight, camera stale/recover,
  E-Stop, Pico disconnect ve actuator arm.
- Mock Pico uçtan uca testleri: LIVE setup → preflight READY → motion/FIRE UI
  sonucu; E-Stop ve heartbeat kaybında NO_FIRE.
- Playwright akışları: ilk açılış, laptop kamera dry-run, live blocked setup,
  live ready fixture, operator ve engineer drawer.
- 1366×768, 1440×900 ve 1920×1080 screenshot setleri üret.
- Klavye focus, tab sırası, kontrast, color-independent status ve minimum
  dokunma hedeflerini kontrol et.
- Gerçek donanım gerektiren kabul maddelerini HIL notlarına ekle; yazılımsal
  contract testleri TODO bırakılmaz.

Kabul:

- Kritik akışlarda console error ve yatay taşma yoktur.
- 1366×768'de ana CTA, E-Stop ve birincil reason scroll gerektirmeden görünür.
- Screenshot karşılaştırmasında bilgi yoğunluğu bütçeleri aşılmaz.
- Donanım fixture/mock olarak görünüyorsa ekran açıkça `FIXTURE` etiketi taşır.

## 14. Screenshot inceleme döngüsü

Her ana ekran tek seferde "bitti" sayılmayacaktır:

1. Mevcut ekranların baseline screenshot'ı alınır.
2. Wireframe ve bilgi hiyerarşisi uygulanır.
3. 1366×768, 1440×900 ve 1920×1080 screenshot'ları alınır.
4. Şu sorularla görsel audit yapılır:
   - İlk üç saniyede mod, readiness ve birincil eylem anlaşılıyor mu?
   - Aynı bilgi birden fazla yerde görünüyor mu?
   - Mock/fixture gerçeğe benziyor mu?
   - Operatör bir sorunu tek eylemle doğru yere taşıyabiliyor mu?
   - E-Stop ve blocker reason gözden kaçabiliyor mu?
5. En az iki düzeltme turu yapılır.
6. Son screenshot'lar `reports/screenshots/phase87_operational_ui/` altında
   desktop çözünürlük ve state adıyla saklanır.

Önerilen state seti:

- `landing_dry_ready`
- `landing_live_blocked_pico`
- `setup_camera_ready_pico_missing`
- `setup_live_preflight_ready`
- `operator_dry_tracking`
- `operator_live_fire_ready`
- `operator_live_estop_active`
- `engineer_devices_drawer`
- `engineer_vision_drawer`

## 15. Test / HIL ayrımı

Donanım gelmeden tamamlanacaklar:

- Bütün UI yeniden tasarımı.
- Laptop kamera DRY RUN akışı.
- Mock Pico Gateway contract testleri.
- E-Stop, heartbeat loss, camera stale/recover ve arm reason-code senaryoları.
- Gerçek profile API üzerinden kod değiştirmeden DRY/LIVE geçiş testi.
- Screenshot, accessibility ve responsive testleri.

Donanım geldiğinde uygulanacak kayıtlı HIL testleri:

- Pico otomatik keşif ve yanlış cihaz ayırımı.
- Gerçek PING/STAT/ARM preflight gösterimi.
- E-Stop fiziksel durumunun UI'ya gecikmesiz yansıması.
- LIVE_TEST düşük hızlı pan/tilt jog ve ACK.
- LIVE_TEST kontrollü `LZR,1` FIRE ve ACK.
- Hareket/ateş sırasında E-Stop ile fiziksel kesme.
- Pico kablosu çıkarıldığında UI blocker ve fiziksel safe-stop.
- Kamera sökülme/stale sonrası komut engeli; yeniden bağlanma ve preflight recovery.

HIL sonuçları mevcut donanım test notlarına eklenir; Phase 87'nin yazılımsal
işleri donanım yok gerekçesiyle TODO bırakılmaz.

## 16. Legacy deprecation planı

1. Normal navigasyondan gizle; route'ları hemen silme.
2. Her legacy route için yeni karşılık ve kalan benzersiz işlevi envanterle.
3. Benzersiz işlevi Engineer drawer'a taşı.
4. Testlerde ve kodda route kullanımını tara.
5. İki doğrulanmış release boyunca doğrudan link uyumluluğunu koru.
6. Kullanılmayan route/component/API'leri ayrı ve kontrollü temizlik diliminde
   kaldır. Phase 87 sırasında çalışan fiziksel yol veya kanıt akışı silinmez.

## 17. Bitmiş sayılma ölçütü

Phase 87 ancak aşağıdakilerin tamamı sağlanınca tamamlanır:

- Başlangıç ekranında yalnız DRY RUN ve LIVE HARDWARE ana seçimleri vardır.
- Soldaki bütün readiness satırları gerçek duruma ve gerçek eyleme bağlıdır.
- LIVE seçimi gerçek `LIVE_TEST/VIDEO_DEMO/COMPETITION` akışına UI üzerinden
  ulaşır; kod/env/hidden flag gerekmez.
- Setup dört anlaşılır adımdır ve dry-only sahte Pico/motor/actuator API'lerini
  kullanmaz.
- Operator cockpit'te yalnız görev için gerekli bilgi ve eylemler görünür.
- Engineer ayrıntıları tek drawer'dadır; legacy araçlar normal navigasyonda yoktur.
- Mock/fixture/surrogate hiçbir yerde gerçek donanım gibi sunulmaz.
- Bütün fiziksel komutlar CommandGateway arkasında kalır.
- Blocked komut exact reason code gösterir; uygulamanın geri kalanı kullanılabilir.
- Laptop kamera dry-run ve mock Pico live contract akışları otomatik testlidir.
- Gerçek donanım HIL adımları kayıtlıdır.
- Son screenshot seti görsel audit'ten geçmiştir.

## 18. Uygulama sırası ve tahmini durum

Sıra güvenlik ve kullanıcı değerine göre sabittir:

1. 87A — gerçeklik/readiness temeli,
2. 87B — Landing,
3. 87C — gerçek Setup,
4. 87D — Operator Cockpit,
5. 87E — Engineer ve navigation,
6. 87F — bütünleşik test ve screenshot kabulü.

İlk implementasyon dilimi 87A + 87B birlikte ele alınmalıdır. Çünkü gerçek
readiness sözleşmesi kurulmadan Landing'i yalnız görsel olarak yenilemek, mevcut
mock bağlantı sorununu tekrar üretir.

## 19. Uygulama kaydı

2026-07-16 tarihinde 87A–87F'nin yazılımsal kapsamı uygulandı. Ayrıntılı kabul
sonucu: `reports/phase87_operational_ui_software_acceptance.md`. Gerçek Pico,
E-Stop, hareket ve FIRE kabulü HIL-17'ye kaydedildi; bu maddeler cihaz tekrar
bağlandığında tamamlanacaktır.
