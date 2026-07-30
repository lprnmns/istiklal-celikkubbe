# Phase 86 — Atış Görselleştirme, Hit/Miss Kanıtı ve Eşzamanlı Replay Planı

Tarih: 2026-07-16

Durum: İnceleme ve uygulama planı tamamlandı; implementasyon başlamadan önce
ürün kararı olarak onay bekliyor.

## 1. Karar

Fikir uygulanmaya değerdir. CommandGateway'in kabul ettiği gerçek bir atışın:

1. hangi hedefe yapıldığını değişmez bir hedef snapshot'ıyla kaydetmesi,
2. dijital ikizde namludan çıkan görünür bir mermi/atış izi üretmesi,
3. bağlı balonun atıştan sonraki davranışından `HIT`, `MISS` veya
   `UNCONFIRMED` sonucu çıkarması,
4. gerçek kamera ve dijital ikiz kanıtını aynı zaman çizelgesinde oynatması

operatör farkındalığını, hata ayıklamayı ve hakem kanıtını ciddi biçimde
güçlendirir.

Ancak tek karede veya yalnız `0.3–0.8 s` içinde balonun görünmemesini doğrudan
imha saymak güvenilir değildir. Namlu/taret titreşimi, motion blur, pozlama,
geçici örtülme, track ID değişimi veya düşen kare false-hit üretebilir. Bu nedenle
önerilen zaman aralığı birincil gözlem penceresi olacak; karar çok kareli ve
body–balon ilişkisinin sürekliliğine bağlı olacaktır.

## 2. Mevcut altyapıda bulunan parçalar

- `TrackingLoop` hedef merkezinin balon bbox'unun iç ateş yarıçapına girmesini
  üç ardışık kare boyunca doğruluyor.
- Atış adayı yalnız `CommandGateway.fire_from_tracking()` üzerinden geçiyor.
- Fiziksel tetik ancak Pico `LZR,1` komutunu ACK ederse kabul ediliyor.
- Gateway ACK'inden sonra `HitConfirmationService.register_shot()` çağrılıyor.
- `HitConfirmationService`, ilişkili body görünürken balon track'i kaybolursa
  `CONFIRMED_HIT`; süre aşılırsa `REENGAGE` üretiyor.
- Body–balon association ve kalıcı balon track ID temeli mevcut.
- Dijital ikizde namlu anchor'ı, hedef dünya konumu, yaw/pitch kinematiği ve
  read-only replay iskeleti mevcut.

## 3. Mevcut eksikler

- Hit confirmation tek kayıp frame'inde hit üretebilir.
- Body–balon association yalnız merkez uzaklığına dayanıyor; bbox içi bağlantı
  bölgesi, ortak hareket ve tekil eşleme henüz yeterli değil.
- Atış için kalıcı `shot_id`, değişmez hedef snapshot'ı ve ortak monotonic zaman
  ekseni yok.
- Dijital ikizde ACK tabanlı mermi, çarpma, balon patlama ve ıska animasyonu yok.
- Gerçek kamera video olay kaydı yok; mevcut session snapshot'ları çoğunlukla
  metadata/mock seviyesinde.
- Mevcut replay gerçek kamera ile dijital ikizi tek timeline'da eşzamanlı
  oynatmıyor.
- Cockpit'teki `EvidenceReplayPanel` gerçek bir medya oynatıcı değil.

## 4. Hedef geçerlilik sözleşmesi

Operasyonel ekranda geçerli hedef aşağıdaki birleşik nesne olacaktır:

```text
EngagementTarget
  = fresh body track
  + exactly one associated fresh balloon track
  + stable temporal association
  + balloon inside class/pose-specific attachment region
  + current frame and non-stale timestamps
```

Kurallar:

- Body var, bağlı balon yok: `TARGET_BALLOON_MISSING`, angajman hedefi değildir.
- Balon var, bağlı body yok: `ORPHAN_BALLOON`, angajman hedefi değildir.
- Bir body içinde/çevresinde birden fazla aday balon: `BALLOON_LINK_AMBIGUOUS`.
- Bir balon birden fazla body ile eşleşiyorsa: `BODY_LINK_AMBIGUOUS`.
- Yalnız `stable` association ateş adayı olabilir.
- Operatör görünümünde geçersiz nesneler hedef olarak vurgulanmaz. Mühendis/debug
  görünümünde tanılama için gri/uyarı etiketiyle gösterilmeye devam eder.
- Algılama katmanı body ve balonu yine bağımsız bulur. “Görmemeli” ifadesi,
  algılamayı tamamen silmek değil, birleşik hedef olmayan nesneyi operasyonel
  hedef saymamak anlamına gelir.

## 5. Balon-önce aday üretimi

Balonun 14 cm ve görsel olarak daha kolay bulunması nedeniyle balon-önce aday
üretimi faydalıdır:

1. Balon detector/tracker aday balonları bulur.
2. Her balonun çevresinde sınıfa ve perspektife göre genişletilmiş body arama
   bölgesi oluşturulur.
3. Body detector sonucu bu bölgelerle eşleştirilir.
4. Bbox containment/attachment bölgesi, normalize konum, merkez mesafesi,
   ortak hız/optical flow ve geçmiş link sürekliliği maliyet matrisine girer.
5. Hungarian/bipartite one-to-one matching ile nihai bağlantı kurulur.

Balon-önce yöntem tek algılama yolu olmayacaktır. Balon kısa süre örtüldüğünde
body track korunmalı; body yalnız kaldığı için ateş çıkmamalı ama önceki link
hit confirmation için kullanılabilmelidir.

## 6. Atış olayı ve değişmez snapshot

Mermi animasyonu ve kayıt `fire request` anında değil, Pico'nun fiziksel tetik
ACK'i kabul edildiği anda başlatılacaktır. DRY_RUN'da ayrı ve açıkça etiketli
sentetik ACK fixture'ı kullanılabilir.

Her ACK tek bir olay üretir:

```text
ShotAcceptedEvent
  shot_id
  run_id
  mission_stage / round
  command_profile
  command = LZR,1
  pico_ack
  wall_clock_utc
  monotonic_ns
  frame_id / frame_timestamp
  body_track_id / balloon_track_id
  target_class / target_team
  association snapshot
  aim error / fire radius / stable frame count
  pan / tilt / step telemetry
  camera intrinsics/profile hash
  muzzle world pose
  target world pose and uncertainty
```

Snapshot atıştan sonra track ID değişse bile değiştirilmez. Sonraki görsel
kanıt bu `shot_id` üzerine eklenir.

## 7. Dijital ikiz mermi ve sonuç animasyonu

- Mermi yalnız kabul edilmiş `ShotAcceptedEvent` ile doğar.
- Başlangıç noktası launcher muzzle anchor'dır.
- İlk yön ACK anındaki namlu rayıdır.
- Görsel seyahat süresi yaklaşık `0.9–1.3 s` yapılır; bu gerçek balistik süre
  olarak sunulmaz ve UI'da `visualized trajectory` etiketi bulunur.
- Yolun ilk yaklaşık %70'i sonuçtan bağımsız ilerler. Böylece hit-confirmation
  kararı için zaman bırakılır.
- `HIT_CONFIRMED`: mermi snapshot hedef konumuna ulaşır; kısa ışık/partikül
  etkisi oluşur, bağlı balon söner/patlar, body `DESTROYED` görünümüne geçer.
- `MISS_CONFIRMED`: mermi hedefin yanından görünür bir offset ile devam eder;
  balon ve body sahnede kalır.
- `UNCONFIRMED`: mermi izi nötr/amber renkte kaybolur; sistem vurdu veya ıska
  iddiası yapmaz.
- Animasyon yalnız görseldir; CommandGateway, motor veya seri komut üretemez.

## 8. Hit/miss doğrulama durum makinesi

Önerilen başlangıç pencereleri yapılandırılabilir olacaktır:

```text
ACK
  -> 0.00–0.30 s TRANSIENT_GRACE
  -> 0.30–0.80 s PRIMARY_EVIDENCE_WINDOW
  -> en geç 1.50 s FINAL_CONFIRMATION_TIMEOUT
```

Başlangıç kararları:

- `HIT_CONFIRMED`:
  - atış öncesi link `stable`,
  - bağlı body track taze ve aynı kimlikle görünür,
  - yalnız bağlı balon belirlenen en az ardışık kare/süre boyunca kayıp,
  - kamera taze, frame drop sınırı içinde,
  - balon başka bir track ID ile aynı bölgede yeniden doğmamış.
- `MISS_CONFIRMED`:
  - doğrulama penceresi sonunda aynı bağlı balon taze olarak görünür,
  - body–balon linki tekrar stable ve kamera kanıtı geçerli.
- `UNCONFIRMED`:
  - body ve balon birlikte kaybolmuş,
  - kamera stale/drop/blur kanıtı yetersiz,
  - track ID switch veya association ambiguous,
  - hedef görüş dışına çıkmış.
- `REENGAGE`:
  - görev süresi/shot budget uygunsa `MISS_CONFIRMED` veya belirli
    `UNCONFIRMED` sonuçlarından sonra hedef tekrar aday olur.

İlk yazılım varsayımı en az 4 ardışık kayıp frame ve en az 150 ms kayıp
kanıtıdır. Kesin sayı laptop replay ve gerçek 5/10/15 m HIL ölçümleriyle
kilitlenecektir.

## 9. Kayıt mimarisi

Atış emri geldiğinde kayda başlamak atış öncesi bağlamı kaçırır. Kamera ve
dijital ikiz için sürekli kısa bir RAM ring buffer tutulacaktır:

- önerilen pre-roll: 2 s,
- önerilen post-roll: sonuçtan sonra 3 s,
- canonical clock: backend `monotonic_ns`,
- duvar saati yalnız insan okunabilir tarih/saat içindir.

ACK geldiğinde recorder:

1. pre-roll tamponunu olay klasörüne boşaltır,
2. post-roll tamamlanana kadar devam eder,
3. kamera frame timestamp'lerini, vision/track/association state'ini,
   CommandGateway ACK'ini ve dijital ikiz state'ini aynı timeline'a yazar,
4. kontrol döngüsünü bloklamamak için bounded background writer queue kullanır,
5. queue dolarsa fiziksel kontrolü etkilemez; kaydı `EVIDENCE_DROPPED_FRAMES`
   olarak işaretler.

Orijinal kayıt gerçek hız ve timestamp'leri korur. Slow motion yalnız oynatma
hızıdır; 0.25×, 0.5×, 1×, 2× seçenekleri bulunur.

## 10. Kanıt dosya yapısı

```text
evidence/engagements/YYYY-MM-DD/<shot_id>/
  manifest.json
  camera_raw.mp4
  camera_overlay.mp4
  digital_twin_timeline.jsonl
  vision_timeline.jsonl
  command_and_ack.json
  outcome.json
  synchronized_review.mp4        # arka planda/sonradan üretilen yan yana kanıt
  thumbnail.jpg
```

Canonical kanıt `camera_raw.mp4 + timeline JSONL` olacaktır. Dijital ikiz
timeline'dan deterministik olarak yeniden kurulabilir. `synchronized_review.mp4`
hakeme/operatöre kolay izleme için türetilmiş dosyadır; kontrol döngüsü içinde
encode edilmez.

## 11. Olay kayıt defteri

Kayıt başlığı insan okunabilir olur ancak gerçek sorgulama manifest alanlarıyla
yapılır. Önerilen görünüm:

| Tarih/saat | Aşama/tur | Hedef | Atış sonucu | Görev sonucu | Reason | Replay |
|---|---|---|---|---|---|---|
| 2026-07-16 14:32:08 | A2/R2 | F-16 · body 17 · balloon 42 | HIT | devam ediyor | `LINKED_BALLOON_LOST_STABLE` | Oynat |

`shot_outcome` ile `mission_outcome` ayrı tutulur. Tek atış ıska olsa bile görev
sonraki atışla başarılı olabilir; bu iki bilgi tek “başarılı/başarısız” alanına
sıkıştırılmaz.

## 12. Eşzamanlı replay ekranı

- Sol: gerçek kamera raw/overlay seçimi.
- Sağ: kaydedilen state'ten üretilen dijital ikiz.
- Ortak play/pause, seek, frame-step ve hız kontrolü.
- Ortak timeline marker'ları:
  - target acquired,
  - lock entered,
  - fire candidate,
  - Pico ACK,
  - balloon first missing,
  - outcome committed,
  - reengage veya mission result.
- İki panel aynı `monotonic offset` ile ilerler; birbirinden bağımsız saat
  kullanmaz.
- Replay her zaman read-only ve `REPLAY_NO_FIRE` kalır.

## 13. Uygulama dilimleri

### 86A — Event ve outcome sözleşmesi

- `ShotAcceptedEvent`, `ShotEvidenceManifest`, `ShotOutcome` şemaları.
- `shot_id/run_id/monotonic_ns` üretimi.
- Gateway ACK'inden recorder ve dijital ikize read-only event yayını.
- Red/rejected fire için mermi ve başarılı atış kaydı oluşmaması.

### 86B — Association v2

- Body attachment ROI/containment.
- Ortak hareket ve temporal link skoru.
- One-to-one bipartite matching.
- Orphan/ambiguous reason code'ları.
- Operatör görünümünde yalnız birleşik valid target; debug görünümünde tüm ham
  detections.

### 86C — HitConfirmation v2

- Grace, primary evidence ve timeout pencereleri.
- Ardışık kayıp frame/süre şartı.
- Track resurrection/ID-switch kontrolü.
- `HIT_CONFIRMED`, `MISS_CONFIRMED`, `UNCONFIRMED`, `REENGAGE` ayrımı.

### 86D — Dijital ikiz atış efektleri

- ACK tabanlı mermi state'i.
- Yavaş görünür trajectory.
- Hit/miss/unconfirmed son segmentleri.
- Balon pop ve body destroyed görsel state'i.
- Replay timeline serialization.

### 86E — Evidence recorder

- Kamera + state ring buffer.
- Background writer ve drop accounting.
- Manifest/hash/retention.
- Sonradan senkron review render/export.

### 86F — Olay defteri ve dual replay UI

- Filtrelenebilir olay tablosu.
- Yan yana senkron player.
- Slow motion/frame step/timeline marker.
- Outcome ve reason code görünümü.

## 14. Yazılım kabul testleri

- ACK yoksa projectile/evidence shot oluşmaz.
- Mock ACK ile doğru `shot_id` ve target snapshot oluşur.
- Aynı body görünür, bağlı balon 4+ frame kayıp: HIT.
- Balon tek frame kaybolup geri gelir: HIT oluşmaz.
- Balon pencere sonunda görünür: MISS.
- Body+balon birlikte kayıp: UNCONFIRMED.
- Kamera stale/drop eşiği aşılmış: UNCONFIRMED.
- Başka balon kaybolur, ateş edilen balon kalır: MISS; yanlış target HIT olmaz.
- Üç hedef çapraz geçerken one-to-one association korunur.
- Replay 0.25×/0.5×/1× hızda iki panelde aynı ACK marker'ını gösterir.
- Recorder baskı altındayken tracking/gateway latency bütçesi bozulmaz.
- Replay ve dijital ikiz hiçbir fiziksel komut üretmez.

## 15. Donanım geldiğinde HIL kabulü

- Gerçek Pico ACK'i ile projectile başlangıç zamanı karşılaştırılır.
- Kamera, muzzle flash/titreşim ve detector kaybı nedeniyle false-hit ölçülür.
- 5/10/15 m'de kontrollü hit, miss ve balon örtülmesi serileri yapılır.
- Gerçek 14 cm balon için min missing-frame ve zaman penceresi kilitlenir.
- Kamera–namlu extrinsic ile dijital mermi başlangıç/yön işareti doğrulanır.
- Olay videosu, ACK logu, Pico telemetrisi ve outcome aynı `shot_id` ile bulunur.

## 16. Muhtemel kod alanları

- `backend/app/services/command_gateway.py`
- `backend/app/services/tracking_loop.py`
- `backend/app/services/body_balloon_association_service.py`
- `backend/app/services/hit_confirmation_service.py`
- yeni `backend/app/services/engagement_evidence_service.py`
- yeni `backend/app/schemas/engagement_evidence.py`
- `backend/app/services/digital_twin_service.py`
- `backend/app/schemas/digital_twin.py`
- `frontend/src/components/digital-twin/DigitalTwinPanel.vue`
- `frontend/src/components/cockpit/EvidenceReplayPanel.vue`
- yeni olay kayıt defteri API/store/type bileşenleri
- phase 68/70 testlerinin v2 genişletmeleri ve yeni phase 86 contract testleri

## 17. Tamamlanmış sayılma koşulu

Bu dilim ancak accepted Gateway ACK → doğru hedef snapshot → dijital projectile →
çok kareli hit/miss/unconfirmed sonucu → kamera+dijital ikiz senkron replay → olay
defteri zinciri mock ile uçtan uca kanıtlandığında yazılım olarak tamamlanmış
sayılır. Fiziksel hit doğruluğu HIL tamamlanmadan iddia edilmez.
