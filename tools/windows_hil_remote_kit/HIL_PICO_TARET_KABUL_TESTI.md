# Pico + taret HIL kabul paketi

Durum: donanım tekrar bağlanana kadar **BEKLEMEDE**. Bu belge, yazılım değişmeden tekrar edilecek saha test kaydıdır.

## Ön koşullar

- Güvenli backstop, boş parkur ve fiziksel E-Stop erişilebilir.
- Tetik/servo mekanizması ilk iki bölümde enerjisiz veya mekanik olarak ayrılmış.
- Pico firmware'i seçilen tek kart için yüklenmiş; kart/firmware dosyası, git revizyonu ve kablo fotoğrafı run formuna yazılmış.
- Cockpit açılmış; alt güvenlik panelindeki Pico portu doğru seçilmiş.

## Run formu

Her test için şu alanlar doldurulur: `run_id`, tarih/saat, operatör, gözlemci, Pico portu, firmware hash, config hash, kamera kaynağı, video dosyası, serial log dosyası, sonuç (`PASS`/`FAIL`) ve reason code.

## HIL-01 — Bağlantı ve preflight

1. Cockpit'te `CANLI TEST` seç.
2. Pico portu ve baudrate gir, `PICO BAĞLA` seç.
3. Taze kamera görüntüsü varken arm kutusunu seç ve preflight çalıştır.
4. Beklenen: `PICO_HEALTHY`, `ESTOP_RELEASED`, `CAMERA_FRESH`, `ACTUATOR_ARMED`; `PING`, `STAT`, `ARM,1` ACK'leri kayıtta.

## HIL-02 — İki eksen düşük hızlı hareket ve E-Stop

1. Tetik enerjisi kapalıyken LIVE_TEST preflight sonrası düşük hızlı `SPD` hareketi başlat.
2. Hareket sırasında fiziksel E-Stop'a bas.
3. Beklenen: iki eksen durur, servo release olur, sürücü kapanır; UI `ESTOP_ACTIVE` gösterir.
4. E-Stop çözülünce hareket veya arm otomatik başlamaz. Yeni preflight zorunludur.
5. Üç ardışık PASS run, video ve seri log kaydedilir.

## HIL-03 — Bağlantı/heartbeat kaybı

1. Düşük hızlı hareket sürerken USB bağlantısını kontrollü çıkar veya Pico gücünü kes.
2. Beklenen: host `PICO_CONNECTION_FAULT` veya `PICO_HEARTBEAT_STALE` gösterir; firmware watchdog fiziksel çıkışı keser.
3. Bağlantıyı geri tak; otomatik arm/hareket/atış olmamalıdır.
4. Kullanıcı `PICO BAĞLA → preflight → arm` ile tekrar hazır hale getirebilmelidir.

## HIL-04 — Kontrollü tetik ve E-Stop

1. Yalnız güvenli backstop ve yarışma mekanik güvenlik koşulları sağlandığında tetik enerjisini bağla.
2. LIVE_TEST, taze gerçek balon algısı, arm ve preflight ile Gateway üzerinden `LZR,1` ACK’ini doğrula.
3. Tetik darbesi sırasında E-Stop'a bas.
4. Beklenen: devam eden/daha sonraki tetik kesilir, `LZR,0`, `STP`, `DRV,0` trace'i görülür; E-Stop çözülünce eski komut tekrar edilmez.
5. Üç ardışık PASS olmadan 15 m atış denemesine geçilmez.

## HIL-05 — 15 m video kabulü

HIL-01…04 yeşil olmadan çalıştırılmaz. Her denemede mesafe ölçümü, balon kimliği, kamera kaydı, hedef/çapraz nişan konumu, serial ACK, sonuç ve video zaman kodu aynı `run_id` altında saklanır.

## HIL-06 — Aşama 2 üç hedefli track kabulü

1. Tetik enerjisi kapalıyken üç balon/maketle farklı hız, kısa occlusion ve çapraz geçiş senaryoları çalıştır.
2. Her run’da persistent track ID, age/hit/miss, predicted/fresh, FPS/p95 latency ve hedef sırası kaydedilir.
3. Beklenen: kısa occlusion sonrası aynı ID geri gelir; miss bütçesi aşılınca track temizlenir; Tracker → Gateway dışı fiziksel write yoktur.
4. Bu test tek başına fiziksel Aşama 2 fire yetkisi vermez; HIL-07 ve HIL-08 de PASS olmalıdır.

## HIL-07 — Body–balloon association güvenlik kabulü

1. 1/1, 2/2, 3/3; çapraz geçiş; yakın iki body; orphan balloon senaryolarını çek.
2. `stable`, `tentative`, `ambiguous`, `orphan` status ve stable frame sayısını run loguna al.
3. Beklenen: ambiguous/orphan hiç fire adayı değildir; association değişiminde eski stable link taşınmaz.
4. Bu test başarısızsa Aşama 2 fiziksel fire NO-GO kalır. PASS sonrasında yalnız `stable` linkli, selected-priority ve fresh track adayının Gateway'e ulaştığı doğrulanır.

## HIL-08 — Hit confirmation ve reengage kabulü

1. Güvenli backstopta kontrol edilmiş hit ve miss senaryoları uygula.
2. Her atışta Pico ACK, balloon/body track, association, confirmation state, atış sayısı/CO₂ ve video zaman kodunu aynı run ID’de tut.
3. Beklenen: shot doğrudan hit sayılmaz; body görünürken linked balloon kaybı `CONFIRMED_HIT`, kanıt yoksa `REENGAGE` olur.
4. False-hit veya duplicate hit görülürse Aşama 2 otomatik skor/fire bağlantısı NO-GO kalır.
5. HIL-06/07/08 PASS sonrası, güvenli backstopta bir Aşama 2 test atışı yap: `A2_TRACK_ID_UNRESOLVED`, `A2_ASSOCIATION_NOT_STABLE`, `A2_PRIORITY_TARGET_MISMATCH` ve `A2_HIT_CONFIRMATION_PENDING` durumlarında `LZR,1` sıfır; yalnız stable+selected+fresh adayda tek `LZR,1` ve `PENDING_CONFIRMATION` görülmelidir.

## HIL-09 — Aşama 3 IFF/range/score kabulü

1. Competition profilini seçmeden önce model package golden-inference sonucu, IFF HSV profil hash'iyle üç enemy + üç friend gerçek ROI reference/capture id'si, 5/10/15 m range observation/capture id'leri ve kamera profilini kaydet. `COMPETITION + stage3` seçildikten sonra bunların değişimi `A3_PROFILE_LOCKED` ile reddedilmelidir.
2. Sekiz turda class, IFF, stable association, range ve safety kararını her fire/NO_FIRE için kaydet.
3. Friend, unknown, ambiguous, orphan, stale, 9,5 m F-16 ve 15 m üstü senaryolarında fire output sıfır olmalı.
4. `A3_DECISION_TARGET_MISMATCH`, `A3_FRIEND_SAFETY_EVIDENCE_INCOMPLETE` ve `A3_FRIEND_HIT_SUSPECTED` senaryolarında LZR trace ve Stage3Engagement status kaydedilir; ilk ikisinde fiziksel fire sıfır olmalıdır.
5. Her turda enemy hit/friend hit/miss, puan ve miss streak kanonik Stage3 event ile karşılaştırılır.
6. Tek friend hit, yanlış class/range veya score/event uyuşmazlığı Aşama 3 fiziksel fire için NO-GO’dur.

## HIL-10 — Aşama 2 ölçülmüş latency lead A/B kabulü

Bu testte tetik enerjisi **kapalı** kalır. Amaç yalnız hareketli hedefte merkezleme kalitesini ölçmektir; lead'in faydası ölçülmeden açık profile alınmaz.

1. Aynı kamera, çözünürlük, PID, hedef yolu ve taret hız limitiyle en az üç yatay+dikey hedef geçişini `lead_enabled=false` durumunda kaydet. Her geçiş 10–15 saniye olmalı; frame timestamp, `total_latency_ms`, X/Y merkezleme hatası ve soft/physical limit olayları aynı `run_id` altında tutulmalıdır.
2. Motion ekranında görünür `Ölçülmüş latency lead` seçeneğini aç; ilk deneme için çarpan `1.0`, üst sınır en fazla `120 ms` kullan. Kod, environment veya gizli flag değiştirme.
3. Aynı üç geçişi tekrar kaydet. Her güncellemede `lead_horizon_ms`, `predicted_target_center_x/y`, track hızı, p50/p95 latency, p50/p95 X/Y hata ve osilasyon notu alınır.
4. Beklenen: horizon yalnız ölçülmüş `vision latency + command period` değerinden türemeli, `0 < horizon <= configured max`; hedefin yeni ölçümünün gerisine düşmemeli; soft/physical limite vurma, sürekli sağ-sol salınım veya target ping-pong olmamalıdır.
5. Lead A/B sonucunda merkezleme veya 15 m hit oranı iyileşmiyor, p95 yükseliyor ya da overshoot gözleniyorsa ekrandan `lead_enabled=false` yap ve stabil profil ile devam et. Bu bir FAIL değil, özellik için **NO-GO** kanıtıdır.

## HIL-11 — Ayrı hareket/ateş sektör profili kabulü

1. Mekanik ölçüm ve backstop kurulumundan sonra Motion ekranındaki `Güvenlik sektör profili` bölümünde hareket ve ateş için ayrı, isimli sektörleri gir. Her sektörün pan/tilt sınırı, ölçüm yöntemi, operatör ve profil hash'i run formuna yazılır.
2. `Profili kaydet ve güvenli durdur` seçildiğinde `LZR,0`, `STP`, `DRV,0` trace'i; `SAFETY_ZONE_PROFILE_CHANGED` ve disarm görülmeli. Hareket/ateş yalnız normal `preflight → arm` sonrası yeniden denenir.
3. Taret ölçülmüş hareket-sektörü içinde iken iki yönlü `SPD` isteği gönder; Pico'ya `SPD` çıkmamalı ve UI `MOTION_FORBIDDEN_ZONE` göstermelidir.
4. Taret ölçülmüş ateş-sektörü içinde iken tüm diğer preflight koşulları yeşilken FIRE isteği gönder; `LZR,1` çıkmamalı ve UI `FIRE_FORBIDDEN_ZONE` göstermelidir.
5. Aşama 3 COMPETITION başladıktan sonra aynı profil mutasyonunu dene; UI/API `A3_PROFILE_LOCKED` döndürmelidir. Bu aşamada profil değişikliği için yarışı bitirip güvenli hazırlık moduna dönülür.
6. Sınırda, sektör dışındaki güvenli konum için düşük hızlı kontrol testi ayrı video ve seri logla kaydedilir. Pico'dan gerçek konum/limit telemetrisi kanıtlanmadan sektörler saha güvenlik duvarının tek katmanı olarak kabul edilmez; fiziksel limit ve E-Stop birincil kalır.

## HIL-12 — Final PC gerçek YOLO cihaz/latency kabulü

Bu test fiziksel çıkış üretmez. A2 lead ve A3 kararının performans varsayımı olmaktan çıkması için final bilgisayarda gerçek production paketle uygulanır.

1. Golden body/balloon model paketi, `golden_cases.json` doğrulaması ve aktif kamera profilini kaydet. Test adapter, OpenCV surrogate veya doğrulanmamış modelle bu adım PASS sayılmaz.
2. Cihaz ekranında istenen cihaz ile çözümlenen cihazın aynı kaydını al: `cpu`, `auto → cuda` veya açıkça `cuda`. CUDA istenip bulunamazsa API/UI `cuda_unavailable`; izin kapalıysa `cuda_not_allowed` göstermelidir. Sessiz CPU düşüşü PASS değildir.
3. `Warmup` çalıştır. Sonuçta gerçek `frame_id`, `latency_ms`, `resolved_device` ve frame kaynağı görünmeli; `ultralytics_inference_failed:*` varsa FAIL.
4. `Benchmark` çalıştır. En az 10 bağımsız frame, gerçek `latency_p50_ms`, `latency_p95_ms`, `mean_latency_ms`, `measured_fps`, CPU/GPU/VRAM ve kamera FPS loglanır.
5. Aynı hedef geçişinde P95, tracking komut periyodu ve HIL-10 lead A/B sonucuyla birlikte değerlendirilir. Gerçek model GPU'da stabil değil veya Y5/A2 merkezlemeyi bozuyorsa doğrulanmış CPU profiline dönülür; CUDA iddiası yapılmaz.

## HIL-13 — Kamera düzlemi / namlu paralaks kalibrasyonu

Bu testte homography yalnız ölçüm/nişan kalibrasyon kanıtıdır; fiziksel limit, E-Stop veya Gateway preflight yerine geçmez.

1. Sabit kamera, taret home ve seçili saha profiliyle en az dört iyi dağıtılmış, eş düzlemli gerçek referans işareti kaydet. World koordinatları metre, image koordinatları gerçek capture çözünürlüğünde olmalı; aynı çizgi üzerindeki dört nokta kabul edilmez.
2. Calibration ekranında noktaları gir ve `Compute` çalıştır. Beklenen: identity olmayan `world_plane_to_image_px` matrisi, en az 4 RANSAC inlier, reprojection error ve profile hash.
3. 5/10/15 m'de kamera çaprazı ile gerçek namlu/atış etkisinin paralaksını ayrı kaydet. Hedef ve namlu ekseni arasındaki residual ölçülür; model/kamera/namlu montajı değiştiğinde önceki hash geçersiz kabul edilir.
4. Collinear, duplicate, kötü reprojection veya kamera çözünürlüğü değişmiş noktada `homography_degenerate_points`, `homography_duplicate_points` ya da `homography_reprojection_error_too_high` görünmeli; valid profil/ateş düzeltmesi iddiası yapılmamalıdır.
5. Kalibrasyon sonucu HIL-10/12 ve 15 m atış kanıtı ile aynı run kimliğine bağlanır. Residual kabul eşiği saha ilk ölçümünden sonra takımca kilitlenir; ölçülmeden sıfır hata iddiası yapılmaz.

## HIL-14 — Pico ACK tabanlı atış/CO₂ bütçesi

1. Yeni tüp/şarjör takıldığında Competition ekranından gerçek kapasiteyi girip resetle. Bu işlem yalnız yazılım sayacını başlatır; kapasite ve tüp kimliği run formuna fiziksel olarak doğrulanmış biçimde yazılır.
2. Her Gateway `LZR,1` ACK’i sonrası ekrandaki `Pico ACK atış` ve kalan kapasite bir azalmalıdır. Fire candidate, UI tıklaması veya ACK'siz timeout atış sayılmaz.
3. Kapasite sıfırken `MAGAZINE_EMPTY` görünmeli, Pico’ya yeni `LZR,1` çıkmamalıdır. Sayaç JSON dosyası bozuksa sistem fail-closed olarak boş kapasiteyle açılır.
4. 5/10/15 m seri denemelerinde atış no, hedef sonucu, tüp/şarjör kimliği ve basınç/hız gözlemi aynı run ID’de tutulur. Bu saha verisi ile final kapasite/değişim eşiği belirlenir; başlangıç değeri yarışma kapasitesi iddiası değildir.

## HIL-15 — Kamera/namlu kinematiği ve sınıf bazlı 3B hedef doğrulaması

Bu test yalnız telemetri ve görsel doğrulama içindir; fiziksel fire kapalı kalır.

1. Taret home konumunda iken kamera optik ekseni, namlu ekseni, pan/tilt pivotu ve kamera–namlu dönüşümü ölçülür. Kamera namlu ucundaysa bile offset ve roll/pitch/yaw sıfır varsayılmaz; ölçülen değer profil hash’iyle kaydedilir.
2. Pico'dan gerçek `pan_deg`, `tilt_deg`, X/Y step ve heartbeat telemetrisi alınırken taret her eksende düşük hızla hareket ettirilir. Dijital ikizde taban sabit, yaw/pitch grupları, kamera FOV'u ve namlu rayı aynı yönde/işaretle hareket etmelidir.
3. Sabit bir 14 cm balon 5/10/15 m'de ve her supplied hava hedefi 5/10/15 m'de kaydedilir. Ekrandaki bbox, sınıf, 3B model konumu, tahmini mesafe, belirsizlik ve gerçek ölçüm aynı run ID'ye yazılır.
4. Taret hedefi merkezlerken hedef 3B dünyada yapay olarak taretle birlikte dönmemelidir; bbox açısı ile taret açısının bileşimi yaklaşık sabit dünya bearing üretmelidir. Kısa track kaybında model önce belirsizleşmeli, stale süresi sonunda kaybolmalıdır.
5. Beklenen: balon referansı 140 mm; F-16 500 mm, helikopter 583 mm, füze 500 mm ve Mini/Micro İHA 375 mm sınıf referansları görünür olmalıdır. Bu referanslar kalibrasyonsuz atış menzili sayılmaz.
6. Kamera/namlu/FOV işareti ters, model sınıfı yanlış, 3B hedef taretle yapışık hareket ediyor veya telemetri stale iken `POSE: TELEMETRY` gösteriyorsa HIL-15 FAIL; dijital ikiz yalnız debug aracı olarak kalır.

## HIL-16 — LOCK → ACK → hit/miss kanıt ve eşzamanlı replay kabulü

Bu test, Phase 86 engagement evidence zincirinin gerçek kamera/Pico kabulüdür.
Yazılımın ürettiği `engagement_id` ve varsa `shot_id`, kamera kaydı, dijital
ikiz timeline'ı, Pico ACK ve sonuç için ortak anahtardır. Tetik enerjisi kapalı
senaryolar ayrıca çalıştırılır; canlı tetik yalnız mevcut Gateway preflight,
backstop ve yarışma güvenlik kuralları altında denenir.

1. Laptop/USB kamera ile 14 cm balonu takip edip `LOCKED` durumuna gir. Olay
   klasöründe lock snapshot, pre-roll vision timeline ve kamera JPEG dizisi
   oluştuğunu doğrula. Kamera yoksa kayıt `TIMELINE_ONLY` kalmalı; gerçek video
   varmış gibi sunulmamalıdır.
2. Tetik enerjisi kapalıyken mock/fixture ACK senaryosunda `shot_id`, 3B
   visual trajectory ve `SHOT_PENDING_CONFIRMATION` kaydını doğrula. Bu adımda
   Pico'ya `LZR,1` çıkmamalıdır.
3. Gerçek güvenli atışta Pico `LZR,1` ACK zamanını, kamera frame timestamp'ini
   ve dijital ikiz timeline'ını aynı `engagement_id` altında karşılaştır.
4. Kontrollü hit serisinde bağlı body görünürken balonun en az 4 ardışık frame
   ve en az 150 ms kaybolduğunu doğrula. Beklenen sonuç: `HIT_CONFIRMED` ve
   `LINKED_BODY_VISIBLE_BALLOON_LOST_STABLE`.
5. Kontrollü miss serisinde balon 0.3–0.8 s ana gözlem penceresinde görünür
   kalmalıdır. Beklenen sonuç: `MISS_CONFIRMED` ve
   `BALLOON_STILL_VISIBLE_MISS_CONFIRMED`.
6. Body+balon birlikte kaybı, kamera blur/frame drop, track ID switch ve
   ambiguous association serilerinde sistem hit yazmamalıdır. Beklenen sonuç:
   `UNCONFIRMED`; yeni atış/yeniden angajman yalnız görev profilinin mevcut
   shot-budget ve safety kurallarıyla değerlendirilir.
7. Sonuçtan sonra 3 s post-roll'un tamamlandığını, sonra `camera_review.mp4`
   üretildiğini doğrula. Host MP4 codec'i yoksa `camera_review_status.json`
   reason code içermeli ve JPEG kaynak dizisi korunmalıdır.
8. Cockpit → Mühendis → Logs → Atış Olay Kayıtları'ndan aynı kaydı aç. Kamera
   videosunda play/pause/seek ve 0.25×/0.5×/1×/2× hız değiştirildiğinde ana 3B
   ikizin aynı engagement replay zamanına geçtiğini ekran kaydıyla kanıtla.
9. Her hit/miss/unconfirmed için ham kamera, review video, manifest, command
   timeline, digital twin timeline, reason code ve operator notu tek run
   paketi halinde saklanır. Bu paket olmadan jüriye hit oranı iddiası yapılmaz.

## NO-GO

E-Stop'ta hareket/tetik sürerse, bağlantı kopmasında çıktı kalırsa, `CAMERA_STALE` ile fire oluşursa veya reason code/UI ile fiziksel davranış çelişirse: tetik enerjisi kesilir, run FAIL olur ve fiziksel test durur.

## HIL-17 — Phase 87 operasyonel UI kabulü

Bu bölüm, yeni iki modlu başlangıç ekranı ve dört adımlı kurulumun gerçek
donanımla doğrulamasıdır. Yazılımsal contract testleri donanım yokken tamamlanır;
buradaki maddeler kart/kamera tekrar bağlandığında run formuna işlenir.

1. Başlangıç ekranında yalnız `DRY RUN` ve `LIVE HARDWARE` ana seçeneklerinin
   göründüğünü, dört readiness satırının gerçek backend/kamera/Pico/Gateway
   durumunu gösterdiğini video ile kaydet.
2. Pico bağlı değilken `LIVE HARDWARE` seç. Beklenen: uygulama kapanmaz;
   Setup Donanım adımına gider ve `PICO_HANDSHAKE_FAILED` (veya gerçek hata
   code'u) görünür. `Pico'yu bağla ve doğrula` dışında sahte ACK/bağlı iddiası
   olmamalıdır.
3. Gerçek Pico portunu seç, `Pico'yu bağla ve doğrula` çalıştır. PING/STAT
   trace'ini, `ESTOP_RELEASED` veya `ESTOP_ACTIVE` sonucu ile aynı run ID altında
   kaydet.
4. E-Stop aktifken preflight çalıştır. Beklenen: `ESTOP_ACTIVE`, motion/FIRE
   blocked; kamera, kanıt ve Mühendis Paneli kullanılabilir kalır.
5. E-Stop bırakılmış, gerçek kamera fresh ve actuator arm seçilmişken preflight
   çalıştır. Beklenen: `PICO_HANDSHAKE_OK`, `ESTOP_RELEASED`, `CAMERA_FRESH`,
   `MOTION_LIMITS_OK`, `ACTUATOR_ARMED`; Operator Cockpit üst barı `SİSTEM
   HAZIR` gösterir.
6. LIVE_TEST içinde düşük hızda hareket ve kontrollü FIRE isteği gönder. UI'nın
   Gateway ACK veya kesin reason code gösterdiğini, komutun legacy Setup
   endpointinden değil CommandGateway yolundan çıktığını seri logla doğrula.
7. Kamera stale veya Pico heartbeat kaybı üret. Beklenen: üst barda ve FIRE
   düğmesinde aynı birincil reason code; fiziksel çıkış yok. Sorun düzeldiğinde
   kullanıcı yalnız UI'dan preflight çalıştırarak tekrar READY olabilir.
8. Ekran görüntülerini 1366×768, 1440×900 ve 1920×1080'de al: Landing dry,
   Landing live blocked, Setup ready, Operator ready, Operator E-Stop ve
   Engineer drawer. Mock/fixture varsa görüntüde açık etiket bulunduğunu denetle.

## HIL-18 — Pico bulma, servo açıları ve boş hazne tetik testi

Firmware `firmware/pico2/main.py` karta yüklendikten sonra aşağıdaki sıra ile
uygulanır. Bu prosedür fiziksel atış değildir; namlu boş ve güvenli yönü
gösterirken servo/valf mekanizmasının hava atımı kontrol edilir.

1. Kurulum → Donanım'da `Pico ara (5 sn)` seç. Kart takılı değilken tam beş
   saniye sonunda `PICO_NOT_FOUND`; takılıyken doğrulanan port ve `PICO_FOUND`
   beklenir. Ardından `Pico'yu bağla ve doğrula` ile PING/STAT loglarını kaydet.
2. Kamera listesinden kullanılacak cihazın marka/modeli, `/dev/video*` ve
   kalıcı cihaz yolunun doğru olduğunu doğrula; seçip uygula ve canlı frame'in
   güncel olduğunu doğrula.
3. Canlı Test seç, Acil Durdurma serbestken aktüatörü arm ederek preflight'ı
   çalıştır. Başarılı koşullar: `PICO_HANDSHAKE_OK`, `ESTOP_RELEASED`,
   `CAMERA_FRESH`, `MOTION_LIMITS_OK`, `ACTUATOR_ARMED`.
4. Algılama ve hareket ekranında güvenli küçük yön komutlarını sırayla ver.
   Her biri için `SPD`, Pico ACK ve son `STP` yanıtının UI/seri kaydını sakla.
5. Başlangıç ve ateş açılarını girip `Açıları Pico'ya uygula` seç. Beklenen
   protokol/ACK: `SRV,CFG,<başlangıç>,<ateş>` / `SERVO_CONFIGURED`.
6. Namlu boşken `Tetiği test et (boş hazne)` seç. Beklenen protokol/ACK:
   `SRV,TEST` / `FIRE_SERVO_PULLED`, ardından Gateway zamanlayıcısından
   `LZR,0` / `FIRE_SERVO_RELEASED`. Bu test atış bütçesini azaltmaz.
7. Servo hareketliyken Acil Durdurma'ya bas. Firmware tetik çıkışını ve motor
   sürücülerini kesmelidir; UI'da sonraki fiziksel komut `ESTOP_ACTIVE` ile
   reddedilmelidir. Bu kanıt olmadan canlı atış testi GO değildir.

## HIL-19 — Phase 89 modern kokpit saha kabulü

Bu bölüm yazılımsal responsive/görsel kabulün gerçek kamera, Pico ve fiziksel
taret telemetrisiyle tekrarıdır. UI görünümü fiziksel güvenlik kanıtı yerine
geçmez; bütün hareket ve FIRE komutları CommandGateway üzerinden kalır.

1. Kaydedilmiş Test profiliyle sistemi aç. Kayıtlı kamera 3 saniye içinde canlı
   görüntü üretmeli veya kesin `CAMERA_*` reason code göstermelidir. Aynı kamera
   backend OpenCV ve browser `getUserMedia` tarafından otomatik olarak iki kez
   açılmamalıdır.
2. Kamerayı çalışırken çıkarıp yeniden tak. Mühendis → Kamera içinde `Yenile`
   sonrası marka/model ve cihaz yolu yeniden görünmeli; profilden tekrar seçilip
   kod/environment değiştirmeden görüntü geri gelmelidir.
3. Pico'yu bağlı başlat, sonra heartbeat kaybı üret. Operatör kokpiti kullanılabilir
   kalmalı; yalnız hareket/FIRE `PICO_*` reason code ile engellenmelidir. Bağlantı
   düzeldiğinde UI'dan preflight yenilenerek tekrar READY olunmalıdır.
4. Düşük hızlı X/Y hareketi sırasında gerçek pan/tilt telemetrisinin 3B taret,
   namlu ucu kamerası ve FOV ile aynı yönde ilerlediğini ekran+seri kaydıyla
   doğrula. Kamera ve 3B panel aynı anda akıcı kalmalıdır.
5. E-Stop aktifken SAFE STOP ve FIRE engel nedeni operatör ekranında görünür
   kalmalı; Mühendis drawer açıldığında SAFE STOP fiziksel güvenlik zinciri
   etkilenmemelidir. Seri logda tetik/motor çıktısının kesildiğini doğrula.
6. 1366×768, 1440×900 ve 1920×1080 çözünürlüklerinde gerçek kamera+3B sahne ile
   ekran görüntüsü al. Operatör görünümünde path, adapter, PID, CAD/debug ve raw
   truth metinleri görünmemeli; bunlar yalnız Mühendis drawer içinde bulunmalıdır.
7. Klavyeyle Mühendis, hedef bırak, takip, FIRE ve SAFE STOP kontrollerine ilerle.
   Focus/hover/disabled durumları ayırt edilebilir olmalı; FIRE engelliyse title
   veya görünür durum alanında aynı makinece okunabilir reason code bulunmalıdır.
