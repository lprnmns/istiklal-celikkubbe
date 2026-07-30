# 05 — Firmware, E-Stop ve Tek CommandGateway Planı

## 1. Hedef mimari

    Operatör / Mission / Tracker
                ↓ niyet
        Runtime Safety Snapshot
                ↓
          SafetyDecision
                ↓ yalnız ALLOW
          CommandGateway
                ↓ sequence + TTL + ACK
          Serial Transport
                ↓
          Kanonik Pico Firmware
                ↓
        Motor / Tetik Aktüatörü

Paralel, yazılımdan bağımsız güvenlik:

    Fiziksel E-Stop → hareket enerjisini keser
                    → tetik/aktüatör enerjisini keser
                    → firmware girişinde latched görünür

Hiçbir servis, API, tracker veya UI bu zinciri atlayarak serial/Pico komutu gönderemez.

## 2. Mevcut kritik sorun

- tracking_loop.py merkezleme sonrası doğrudan ateş üretebiliyor.
- FIRE_REQUIRED_FRAMES 1, kararlı iz için yetersiz.
- DecisionEngine’in IFF/range/E-Stop/zone kapıları gerçek fiziksel yola bağlı değil.
- Ana Fire Gate yolu fiilen sürekli red durumunda.
- Firmware seçenekleri ve E-Stop pini uyuşmuyor.
- Eski Arduino firmware’inde tetik komutunun E-Stop kontrolü belirsiz/yetersiz.
- 24 V motor ve 6 V servo hatları ayrı; E-Stop’un ikisini de kestiği kanıtlanmamış.
- full_active operational mode tek API çağrısıyla dry-run’ı kapatıp fiziksel fire izni açabiliyor.
- Serial real-write gerçek ACK olmadan “sent” sayılabiliyor.
- Stale browser/frame state güncelliği doğrulanmadan karar girdisi olabiliyor.

## 3. Kanonik pin ve güç sözleşmesi

SAFE-01 çıktısı tek sayfalık “as-built” belgedir:

| Alan | Kaydedilecek gerçek |
|---|---|
| Pico modeli/seri | Fiziksel kart ve handshake kimliği |
| Firmware | Repo yolu, commit ve build hash |
| Pan step/dir/enable | Gerçek pin |
| Tilt step/dir/enable | Gerçek pin |
| Pan/Tilt limit | Gerçek pin ve aktif seviye |
| Home sensörleri | Gerçek pin ve aktif seviye |
| E-Stop sense | Gerçek pin ve aktif seviye |
| Tetik çıkışı | Gerçek pin, sürücü ve varsayılan seviye |
| Motor gücü | Gerilim, sigorta, kesme elemanı |
| Tetik/servo gücü | Gerilim, sigorta, kesme elemanı |
| Fiziksel arm | Anahtar/kontak ve telemetri |

config/config.yaml, pin profili, firmware sabitleri ve gerçek kablolama bu belgeyle birebir eşleşmelidir. Bir pin iki kritik işleve atanamaz.

## 4. Kanonik firmware gereksinimleri

- Açılışta bütün çıkışlar güvenli.
- Açıkça doğrulanmış protokol sürümü ve cihaz kimliği handshake’i.
- Her komutta sequence ID, sınır kontrolü ve ACK/NACK.
- Hareket komutlarında TTL; host kaybında otomatik duruş.
- Tetik komutunda E-Stop, fiziksel arm ve firmware state kontrolü.
- E-Stop aktifken hareket/tetik komutlarına NACK.
- E-Stop çözülünce otomatik devam veya eski komut yürütme yok.
- Watchdog reset nedeni telemetride.
- Limit/home durumu gerçek telemetri.
- Pan/tilt soft limit + bağımsız fiziksel limit.
- Bilinmeyen komut fail-closed.
- Firmware hash ve pin profile hash preflight’ta görünür.

Telemetry-only firmware canlı hareket/atış firmware’iyle karıştırılmaz. Tek “yarışma firmware’i” adı ve sürümleme politikası kullanılır.

## 5. SafetyDecision girdileri

Her karar tek immutable snapshot üzerinden verilir:

- timestamp ve freshness.
- görev modu ve aşama.
- DRY_RUN.
- E-Stop latched durumu.
- fiziksel arm/aktüatör güç izni.
- Pico health/protokol/ACK.
- kamera health ve frame age.
- model health ve inference age.
- track ID, yaş, kararlılık ve merkezleme.
- body class ve confidence.
- IFF state ve confidence.
- body–balloon association ve stabilite.
- menzil ve belirsizlik.
- hareket/atış yasak bölgesi.
- mekanik limit/home.
- shot cooldown, shot budget ve CO₂ state.
- görev sırası ve turn deadline.

Karar çıktısı:

- ALLOW_MOTION, DENY_MOTION veya SAFE_STOP.
- ALLOW_FIRE veya NO_FIRE.
- Sabit reason code listesi.
- Snapshot hash.
- Kısa geçerlilik süresi.
- İzin verilen hedef/track ve komut kapsamı.

Snapshot, tek camera producer ve tek inference worker’ın timestamp’li state bus çıktısıdır. Browser event’i veya REST isteği fiziksel kararın kalıcı kaynağı olamaz.

## 6. Görev bağlamlı güvenlik politikaları

Tek motor farklı görev profillerini destekler:

### VIDEO_BALLOON / AŞAMA 2

- Body sınıfı ve IFF şartı uygulanmaz.
- Geçerli balon/target track, association, menzil/zone, E-Stop, arm ve kararlılık şartları uygulanır.
- Profil explicit seçilir; Aşama 3’e sızamaz.

### AŞAMA 1 MANUAL

- Hareket ve ateş niyeti kullanıcıdan gelmek zorunda.
- Otonom tracker hareket komutu üretemez.
- Doğru hedef sırası ve ilk Balistik Füze uyarısı.
- E-Stop, arm, zone, limit ve cihaz freshness her zaman zorunlu.

### AŞAMA 3

- Body class KNOWN.
- IFF ENEMY.
- Association STABLE.
- Sınıfa uygun menzil penceresi.
- Unknown/ambiguous/friend durumunda NO_FIRE.

## 7. CommandGateway gereksinimleri

- Hareket ve ateş için tek giriş noktası.
- SafetyDecision token’ını doğrular.
- Token TTL ve hedef/track bağlamını kontrol eder.
- DRY_RUN’da fiziksel TX üretmez.
- Her komuta sequence ID ve correlation/run ID ekler.
- ACK timeout’ta safe stop.
- Fire komutu ACK’siz başarılı sayılmaz ve otomatik tekrar edilmez.
- E-Stop veya disconnect olayında bekleyen kuyruğu atomik temizler.
- Reconnect sonrası otomatik arm olmaz.
- Rate limit, cooldown ve duplicate suppression.
- Komut ve sonuç audit logu.
- Serial transport implementasyonunu görev servislerinden gizler.

Operational mode geçişi:

- full_active tek boolean değildir.
- Güncel preflight release hash’i, fiziksel arm, yetkili rol, kısa TTL ve audit gerekir.
- E-Stop, disconnect, reset, profile/model değişimi veya süre aşımında izin düşer.

Repo taraması, CommandGateway dışındaki fiziksel write noktalarını CI’da hata yapmalıdır.

## 8. Yasak bölge ve limit katmanları

1. Görev/parkur atışa yasak bölgesi.
2. Görev/parkur harekete yasak bölgesi.
3. Yazılım soft limit.
4. Firmware soft limit.
5. Fiziksel limit switch.
6. Mekanik son durdurucu.

Bu katmanlar birbirinin yerine geçmez. Atışa yasak ama harekete izinli bölgede taret dönebilir; ateş NO_FIRE_FORBIDDEN_ZONE ile engellenir.

## 9. E-Stop kabul zinciri

### Masaüstü, enerji kapalı

- Pin aktif seviye.
- State latch/reset.
- Queue flush.
- Command NACK.
- UI ve telemetry eşleşmesi.

### HIL, tetik enerjisi kapalı

- Pan/tilt hareket komutları.
- E-Stop sırasında iki eksen duruş.
- Host komutu devam ederken fiziksel duruş.
- Reconnect/reset davranışı.

### Fiziksel hareket

- Üç ardışık Y3 provası.
- Duruş gecikmesi ve mesafesi ölçümü.
- Çözülünce otomatik hareket yok.

### Kontrollü tetik

- Güvenli backstop.
- Üç ardışık Y4 provası.
- E-Stop öncesi atış, sonrası planlı atışın olmaması.
- Tetik enerji hattının ölçümü.
- Kuyrukta stale atış olmaması.

## 10. Geri dönüş politikası

Her firmware/gateway değişikliğinde:

- Golden baseline firmware ve config salt-okunur paket olarak tutulur.
- Yeni sürüm yalnız dry-run ve HIL geçerse fiziksele çıkar.
- Güvenlik acceptance başarısızsa gerçek tetik kapatılır, firmware geri alınır ve test yalnız telemetry/dry-run sürer.
- Baseline’a dönmek güvenlik bypass’ını geri getirecekse baseline yalnız tanı amaçlı, tetik enerjisi fiziksel kapalı kullanılır.

“Çalışan ama güvenlik kapılarını atlayan” sürüm yarışma geri dönüş seçeneği değildir.
