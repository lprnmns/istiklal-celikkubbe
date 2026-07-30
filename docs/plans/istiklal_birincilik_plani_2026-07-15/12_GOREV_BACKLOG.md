# 12 — Kanonik Görev Backlog’u

Bu dosya uygulamanın tek görev kaynağıdır. Diğer belgeler strateji ve kabul bağlamı verir. Görev durumu onay sonrasında TODO / DOING / BLOCKED / DONE olarak tutulacaktır.

Efor kişi-gün cinsindedir ve donanım tedarik süresini içermez. “Muhtemel dosyalar” uygulama sırasında doğrulanacak etki alanıdır; kullanıcı değişiklikleri incelenmeden dosya üzerine yazılmaz.

## A. Yönetim ve kaynak gerçeği

### GOV-01 — Planı onayla ve rol sahiplerini ata

- Öncelik / hedef kapı: P0 / G0.
- Sahip rol: Takım Lideri; destek tüm alan liderleri.
- Tahmini efor: 0,5 kişi-gün.
- Bağımlılık: Kullanıcı onayı.
- Muhtemel dosyalar: Bu plan klasörü, ekip görev panosu.
- Kabul kriteri: Güvenlik, firmware, kontrol, vision, platform, test, saha ve video için birincil/yedek kişi; günlük karar saati ve acil durdurma yetkisi yazılıdır.
- Test / kanıt: İmzalı/mesajla onaylı rol tablosu ve ilk kickoff notu.
- Geri dönüş koşulu: Kritik rol sahipsizse fiziksel çalışma başlamaz; takvim ekip kapasitesine göre yeniden bazlanır.

### GOV-02 — Resmî kaynak ve puan gerçeğini kilitle

- Öncelik / hedef kapı: P0 / G0.
- Sahip rol: Takım Lideri + Test/Kanıt.
- Tahmini efor: 0,5 kişi-gün; haftalık 15 dakika.
- Bağımlılık: GOV-01.
- Muhtemel dosyalar: docs/competition_ground_truth.md — yeni; kaynak hash manifesti.
- Kabul kriteri: ÖTR/KTR gerçek puanları, güncel şartname/genel/etik kural sürümleri, parkur/3MF hash’i, final tarihi ve resmî iletişim notları tek kayıtta.
- Test / kanıt: Resmî ekran/PDF/link ve SHA-256; haftalık değişiklik raporu.
- Geri dönüş koşulu: Kaynak revizyonu gelirse etkilenen görevler durur, requirement diff ve plan rebase yapılır.

### GOV-03 — Golden baseline manifesti ve geri dönüş paketi oluştur

- Öncelik / hedef kapı: P0 / G1.
- Sahip rol: Platform/Release; destek Kontrol, Firmware, Test.
- Tahmini efor: 1,5 kişi-gün.
- Bağımlılık: GOV-01.
- Muhtemel dosyalar: docs/golden_baseline.md — yeni; scripts/baseline_manifest — yeni; config, firmware ve lockfile snapshot’ları.
- Kabul kriteri: Commit+dirty diff, config, model, firmware, OS, launcher, kamera/Pico kimliği ve calibration hash’leri kayıtlı; mevcut iki balon davranışı 10 run ile yeniden üretilebilir.
- Test / kanıt: 10 run manifesti, video/log, geri dönüş yönergesi ve salt-okunur paket.
- Geri dönüş koşulu: Baseline yeniden üretilemiyorsa refactor ve temizlik durur; son fiziksel çalışan zincir aranır, tetik enerjisi kapalı tutulur.

### GOV-04 — Branch, değişiklik ve feature-freeze politikasını uygula

- Öncelik / hedef kapı: P0 / G1–G5.
- Sahip rol: Takım Lideri + Platform/Release.
- Tahmini efor: 0,5 kişi-gün.
- Bağımlılık: GOV-03.
- Muhtemel dosyalar: CONTRIBUTING.md veya docs/change_control.md — yeni; CI ayarları.
- Kabul kriteri: Video dalı, deney dalları, merge sahibi, gerekli testler, 4 Ağustos 18:00 freeze ve hotfix tanımı yazılıdır.
- Test / kanıt: Örnek PR/merge checklist’i; freeze sonrası P0 olmayan değişikliğin reddedildiği kayıt.
- Geri dönüş koşulu: Ana video dalı kırılırsa golden tag’e dönülür; deney dalı merge’i geri alınır.

### GOV-05 — Birincilik skor ve kapı panosunu işlet

- Öncelik / hedef kapı: P2 / sürekli.
- Sahip rol: Takım Lideri + Test/Kanıt.
- Tahmini efor: 1 kişi-gün kurulum; günlük 15 dakika.
- Bağımlılık: GOV-02, GOV-03.
- Muhtemel dosyalar: reports/competition_scoreboard.md veya evidence/scoreboard.json — yeni.
- Kabul kriteri: Video, ebat, A1, A2, A3, kurulum, bakım ve dost-vuruş metrikleri son kanıta bağlı kırmızı/sarı/yeşil görünür.
- Test / kanıt: Her gün timestamp’li pano snapshot’ı; sayıların run ID’ye linki.
- Geri dönüş koşulu: Kanıtsız manuel yeşil işaretler silinir; son doğrulanmış ölçüme dönülür.

## B. Güvenlik, firmware ve fiziksel komut

### SAFE-01 — As-built güç, kablo ve pin sözleşmesini çıkar

- Öncelik / hedef kapı: P0 / G1.
- Sahip rol: Güvenlik ve Donanım; destek Firmware.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: GOV-01.
- Muhtemel dosyalar: docs/hardware_as_built.md — yeni; config/config.yaml; config/pin_profiles; firmware sabitleri.
- Kabul kriteri: Pico modeli, bütün I/O pinleri, aktif seviyeler, motor/tetik güç hatları, sigorta, E-Stop, arm, limit/home fotoğraflı ve ölçülmüş; pin çakışması yok.
- Test / kanıt: Süreklilik/gerilim ölçüm formu, kablo fotoğrafları, iki kişi read-back.
- Geri dönüş koşulu: Gerçek kablo ile config/firmware uyuşmazsa enerji ve canlı komut kapatılır; düzeltme sonrası denetim tekrarlanır.

### SAFE-02 — Tek kanonik yarışma firmware’i ve protokolü seç

- Öncelik / hedef kapı: P0 / G2.
- Sahip rol: Firmware.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: SAFE-01, GOV-03.
- Muhtemel dosyalar: firmware/pico2/main.py veya seçilen kanonik yol; eski_sistem_arayüz/pico_arduino/...ino; backend/app/protocols; config/pin_profiles.
- Kabul kriteri: Tek aktif firmware yolu, semver/build hash, handshake, ACK/NACK, safe boot, E-Stop, limit/home ve watchdog sözleşmesi; README eski yolu aktif göstermiyor.
- Test / kanıt: Firmware unit/bench, protokol uyumluluk matrisi ve build artefact hash’i.
- Geri dönüş koşulu: Yeni firmware HIL’da hareket semantiğini/telemetriyi bozarsa önceki build tetik enerjisi kapalı tanı modunda kullanılır; canlı sistem eski güvensiz firmware’e dönmez.

### SAFE-03 — E-Stop’un iki eksen hareket enerjisini fiziksel kestiğini doğrula

- Öncelik / hedef kapı: P0 / G2 ve Y3.
- Sahip rol: Güvenlik ve Donanım; destek Firmware, Test.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: SAFE-01, SAFE-02.
- Muhtemel dosyalar: firmware kanonik dosyası; backend safety telemetry; as-built şema.
- Kabul kriteri: Pan+tilt hareket ederken buton iki ekseni durdurur; state latched; çözülünce otomatik hareket yok; güvenlik sahibi ölçülmüş gecikmeyi onaylar.
- Test / kanıt: Masa/HIL sonrası üç ardışık fiziksel run, video, telemetri ve ölçüm.
- Geri dönüş koşulu: Tek eksen hareket sürerse veya otomatik devam olursa motor enerjisi kapatılır; Y3/atış NO-GO.

### SAFE-04 — E-Stop’un gerçek tetik/aktüatör enerjisini fiziksel kestiğini doğrula

- Öncelik / hedef kapı: P0 / G2 ve Y4.
- Sahip rol: Güvenlik ve Donanım; destek Firmware, Test.
- Tahmini efor: 2 kişi-gün.
- Bağımlılık: SAFE-01, SAFE-02.
- Muhtemel dosyalar: as-built şema; kanonik firmware; config/config.yaml; safety telemetry.
- Kabul kriteri: E-Stop motor hattından bağımsız olabilecek 6 V servo/tetik yolunu da güvenli biçimde keser; E-Stop aktifken firmware tetik komutunu reddeder; reset sonrası eski atış yok.
- Test / kanıt: Elektriksel ölçüm ve üç ardışık kontrollü Y4 provası; komut/ACK/video aynı run ID.
- Geri dönüş koşulu: E-Stop sonrası tetik enerjisi/atışı görülürse gerçek atış tamamen dondurulur ve fiziksel interlock düzeltilmeden devam edilmez.

### SAFE-05 — Tek CommandGateway uygula

- Öncelik / hedef kapı: P0 / G2.
- Sahip rol: Kontrol ve Backend.
- Tahmini efor: 3–4 kişi-gün.
- Bağımlılık: SAFE-02, GOV-03.
- Muhtemel dosyalar: backend/app/services/command_gateway.py — yeni; tracking_loop.py; serial_service.py; pico_service.py; motion_service.py; turret_service.py; ilgili API’ler.
- Kabul kriteri: Bütün fiziksel hareket/atış write’ları gateway’den geçer; sequence, TTL, rate limit, ACK, correlation ID, queue flush ve DRY_RUN davranışı tek yerde.
- Test / kanıt: Unit/integration; repo statik taramasında gateway dışı write sıfır; HIL command trace.
- Geri dönüş koşulu: Gateway komut kaybı/duplicate/stale üretirse fiziksel TX kapatılır ve son güvenli dry-run sürümüne dönülür.

### SAFE-06 — Deterministik ve görev bağlamlı SafetyDecision uygula

- Öncelik / hedef kapı: P0 / G2.
- Sahip rol: Kontrol ve Backend; destek Güvenlik, Vision.
- Tahmini efor: 3 kişi-gün.
- Bağımlılık: SAFE-05.
- Muhtemel dosyalar: backend/app/services/decision_engine.py; safety_gate_service.py; schemas/decision.py; api/decision.py; config/config.yaml.
- Kabul kriteri: Immutable snapshot, sabit reason code, kısa ömürlü hedef-bağlamlı token; VIDEO_BALLOON, A1_MANUAL, A2 ve A3 politikaları; stale/unknown/ambiguous fail-closed.
- Test / kanıt: Aynı snapshot deterministik aynı sonuç; karar tablosu unit testleri; DRY_RUN’da fiziksel TX sıfır.
- Geri dönüş koşulu: Bir deny koşulu allow üretirse canlı fire dondurulur; token doğrulaması kapatılamaz.

### SAFE-07 — Doğrudan hareket/ateş bypass’larını kaldır ve CI’da engelle

- Öncelik / hedef kapı: P0 / G2.
- Sahip rol: Kontrol ve Backend + Platform.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: SAFE-05, SAFE-06.
- Muhtemel dosyalar: tracking_loop.py; auto_tracker_service.py; serial_service.py; API route’ları; yeni static-check script/CI.
- Kabul kriteri: send_fire_command veya transport.write benzeri fiziksel çağrı gateway dışından yapılamaz; FIRE_REQUIRED_FRAMES=1 yolu kaldırılmış/kapalı.
- Test / kanıt: rg/AST tabanlı CI kontrolü, negatif test ve code review.
- Geri dönüş koşulu: Yeni bypass bulunursa ilgili build yarışma dışı ilan edilir ve fiziksel arm kapalı kalır.

### SAFE-08 — Ayrı hareket/atış yasak bölgeleri, soft limit ve homing

- Öncelik / hedef kapı: P1 / final güvenlik.
- Sahip rol: Kontrol ve Backend + Firmware; destek Frontend.
- Tahmini efor: 3 kişi-gün.
- Bağımlılık: SAFE-01, SAFE-02, SAFE-06.
- Muhtemel dosyalar: config/config.yaml; motion_service.py; decision_engine.py; firmware; frontend SafetyView/SetupCenter.
- Kabul kriteri: Hareket ve fire bölgeleri ayrı, kalıcı profil; wrap-around/sınır testleri; soft limit, firmware limit, fiziksel limit ve home telemetrisi katmanlı.
- Test / kanıt: Unit/replay/HIL sınır matrisi; fiziksel düşük hızlı limit/home testi.
- Geri dönüş koşulu: Profil sıfırlanır veya sınır aşılırsa hareket/fire kapalı; güvenli sabit profil geri yüklenir.

### SAFE-09 — Watchdog, disconnect ve stale queue güvenliğini kapat

- Öncelik / hedef kapı: P0 / G2–G3.
- Sahip rol: Firmware + Kontrol/Backend.
- Tahmini efor: 2 kişi-gün.
- Bağımlılık: SAFE-02, SAFE-05.
- Muhtemel dosyalar: firmware; serial_service.py; device_manager_service.py; command_gateway.py; runtime_state.py.
- Kabul kriteri: Host/Pico/camera kopması safe stop; hareket TTL; ACK timeout; queue atomik temizleme; reconnect sonrası preflight ve otomatik arm yok.
- Test / kanıt: Fault-injection matrisi, HIL çıkar/tak, stale/duplicate command sayısı sıfır.
- Geri dönüş koşulu: Kopma sonrası fiziksel hareket/atış sürerse fiziksel test durur ve ilgili transport sürümü geri alınır.

### SAFE-10 — Birleşik güvenlik kabulünü imzala

- Öncelik / hedef kapı: P0 / G3–G4.
- Sahip rol: Güvenlik ve Donanım + Test/Kanıt; değişikliği yapan dışı onay tercih edilir.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: SAFE-03…SAFE-09, SAFE-11, PLAT-10, PLAT-11.
- Muhtemel dosyalar: evidence/safety_acceptance; reports safety özeti.
- Kabul kriteri: Açılış, DRY_RUN, arm, E-Stop, zones, limit, disconnect, crash, queue ve kontrollü fire senaryolarının tamamı yeşil.
- Test / kanıt: İki imzalı checklist, run paketleri ve Y3/Y4 üçer ardışık prova.
- Geri dönüş koşulu: Tek P0 safety testi kırmızıysa video/full mission fire NO-GO ve son imzalı safety release’e dönülür.

## C. Repo, cihaz ve platform

### PLAT-01 — Disk ve artefact envanterini sınıflandır

- Öncelik / hedef kapı: P0 / G1.
- Sahip rol: Platform/Release.
- Tahmini efor: 0,5 kişi-gün.
- Bağımlılık: GOV-03.
- Muhtemel dosyalar: reports/storage_inventory.md — yeni; .gitignore; retention config.
- Kabul kriteri: Kaynak, venv/cache, model, dataset, export, log ve üretilebilir artefact ayrı; aktif/arşiv/silinebilir etiketi ve boyutu belli.
- Test / kanıt: du/file-count raporu ve hash’li envanter.
- Geri dönüş koşulu: Baseline’a etkisi bilinmeyen içerik silinmez; temizleme ayrı onaya gider.

### PLAT-02 — Release paketinin kendi çıktısını kopyalama/ENOSPC hatasını düzelt

- Öncelik / hedef kapı: P0 / G3.
- Sahip rol: Platform/Release.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: PLAT-01.
- Muhtemel dosyalar: backend/app/services/release_service.py; backend/tests/test_phase15_release_candidate.py; test_phase22_portable_release_package.py; test_phase23_24_cleanroom_jury_rehearsal.py; scripts/check_release.py.
- Kabul kriteri: Output input ağacında olamaz; export hariç; temp staging; maksimum boyut/adet; preflight disk kontrolü; cleanup.
- Test / kanıt: Küçük fixture ile bounded package; iki ardışık testte boyut sabit; ENOSPC yok.
- Geri dönüş koşulu: Paket boyutu tekrarlı büyürse release lane kapatılır ve son doğrulanmış manuel paket kullanılır.

### PLAT-03 — Log rotation ve runtime retention uygula

- Öncelik / hedef kapı: P0 / G3.
- Sahip rol: Platform/Release + Backend.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: PLAT-01.
- Muhtemel dosyalar: backend/app/services/log_service.py; storage_paths.py; config/config.yaml.
- Kabul kriteri: Boyut/gün tabanlı rotation, toplam kota, disk-low uyarısı; safety/competition evidence ayrı korunur; 30 dk soak’ta kontrolsüz büyüme yok.
- Test / kanıt: Rotation unit/integration ve soak disk grafiği.
- Geri dönüş koşulu: Kritik safety logu kaybolursa retention politikası geri alınır; disk dolmasını önlemek için fiziksel run sayısı sınırlandırılır.

### PLAT-04 — Pico handshake ve kalıcı cihaz kimliği

- Öncelik / hedef kapı: P0 / G3.
- Sahip rol: Firmware + Platform.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: SAFE-02, SAFE-09.
- Muhtemel dosyalar: device_manager_service.py; pico_service.py; protocols; schemas/device_manager.py; firmware.
- Kabul kriteri: Board UID, firmware/protokol/pin profile/capability; port adı değişse aynı cihaz; yanlış firmware INCOMPATIBLE; reconnect preflight.
- Test / kanıt: Sekiz senaryolu USB matrisi Windows/Linux veya seçilen platformlarda.
- Geri dönüş koşulu: Yanlış serial cihaz seçilirse fiziksel komut kapatılır; explicit Wizard seçimi geçici fail-safe olur.

### PLAT-05 — Kamera kalıcı kimliği, preview ve hotplug

- Öncelik / hedef kapı: P0 / G3.
- Sahip rol: Platform/Release + Vision.
- Tahmini efor: 2 kişi-gün.
- Bağımlılık: GOV-03.
- Muhtemel dosyalar: camera_runtime_service.py; camera_service.py; device_manager_service.py; schemas/camera_runtime.py; frontend DeviceManagerPanel.
- Kabul kriteri: Dahili+ELP doğru preview; port/index değişimi kodsuz; çıkarma stale/safe stop; geri takma format/FPS doğrulama ve kullanıcı onaylı devam.
- Test / kanıt: Yedi senaryolu kamera matrisi ve run logları.
- Geri dönüş koşulu: Yanlış kamera otomatik seçilirse auto-select kapatılır, profile-locked Wizard kullanılır.

### PLAT-06 — Video/final golden OS kararını ver

- Öncelik / hedef kapı: P0 / 27 Temmuz.
- Sahip rol: Takım Lideri + Platform/Release.
- Tahmini efor: 0,5 kişi-gün karar; Windows kanıtı ayrı.
- Bağımlılık: PLAT-04, PLAT-05.
- Muhtemel dosyalar: docs/golden_rig.md — yeni; start_linux.sh; start_windows.bat.
- Kabul kriteri: Tek çekim rig’i, sürücü/GPU/cihaz ve launcher manifesti; yeniden başlatma sonrası kabul. Windows yalnız gerçekten zorunluysa seçilir.
- Test / kanıt: Soğuk başlangıç ve Quick Preflight videosu/logu.
- Geri dönüş koşulu: Windows kapısı 27 Temmuz’da geçmezse Linux golden rig; çalışan rig son hafta değiştirilmez.

### PLAT-07 — Offline launcher ve Quick Preflight

- Öncelik / hedef kapı: P0 / G3.
- Sahip rol: Platform/Release + Frontend/UX.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: PLAT-04…PLAT-06, SAFE-06, SAFE-11.
- Muhtemel dosyalar: start_linux.sh; start_windows.bat; backend setup/first_run services; frontend SetupCenterView.vue; setupWizard API/store.
- Kabul kriteri: İnternetsiz start; disk/config/Pico/camera/E-Stop/arm/model/GPU/zone/log/dry-run adımları; bloklayıcı neden+eylem; teknisyen kaynak düzenlemez.
- Test / kanıt: Projeyi geliştirmemiş kişiyle usability; üç soğuk başlangıç, yazılım preflight beş dakika altında.
- Geri dönüş koşulu: Yeni Wizard başlangıcı bloklarsa basit doğrulanmış launcher+read-only checklist’e dönülür; güvenlik adımları atlanmaz.

### PLAT-08 — Gerçek GPU inference ve performans telemetrisi

- Öncelik / hedef kapı: P1 / Y6 ve A3.
- Sahip rol: Vision/ML + Platform.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: PLAT-06, A3-02.
- Muhtemel dosyalar: vision_pipeline.py; inference_adapter_service.py; config/config.yaml; frontend health panels.
- Kabul kriteri: auto/cuda/cpu seçimi; runtime gerçek device; warm-up, FPS, p50/p95 latency, VRAM; CPU’ya sessiz sabitleme yok.
- Test / kanıt: Hedef PC gerçek model benchmark’ı ve 30 dk soak.
- Geri dönüş koşulu: GPU export doğruluğu/kararlılığı bozarsa doğrulanmış format/CPU yalnız performans kapısını geçiyorsa kullanılır; aksi halde Y6/A3 NO-GO.

### PLAT-09 — Testleri hızlı, release ve fiziksel lane’lere ayır

- Öncelik / hedef kapı: P2 / sürekli.
- Sahip rol: Platform/Release + Test.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: PLAT-02.
- Muhtemel dosyalar: backend/pyproject.toml; test marker’ları; CI scriptleri; frontend/package.json.
- Kabul kriteri: Unit/replay her değişiklikte; release bounded; physical explicit; frontend typecheck; hangi lane’in geçtiği manifestte.
- Test / kanıt: CI süre/sonuç raporu; release testi normal komutta diski doldurmuyor.
- Geri dönüş koşulu: Lane ayrımı testleri yanlışlıkla atlıyorsa eski komut korunur ve marker düzeltilene kadar manuel gate uygulanır.

## D. Fiziksel operasyon

### OPS-01 — Final ebatını marjla doğrula

- Öncelik / hedef kapı: P0/P2 / G1 ve final.
- Sahip rol: Güvenlik ve Donanım.
- Tahmini efor: 0,5 kişi-gün; her mekanik değişiklikte tekrar.
- Bağımlılık: GOV-01.
- Muhtemel dosyalar: evidence/dimensions; CAD/BOM referansları.
- Kabul kriteri: Final kablo/kamera/koruma konfigürasyonunda bütün boyutlar 100 cm altı; 20 puan için en uzun boyut tercihen 58–59 cm altında; ölçüm yöntemi fotoğraflı.
- Test / kanıt: İki kişi, iki ölçüm aracı, tarihli foto/video.
- Geri dönüş koşulu: 60 cm marjı yoksa ilgili çıkıntı/montaj yeniden tasarlanır; puan varsayımı 0’a çekilip skor riski güncellenir.

### OPS-02 — CO₂, şarjör ve atış bütçesini ölç

- Öncelik / hedef kapı: P1 / final görevleri.
- Sahip rol: Güvenlik/Donanım + Saha Operatörü.
- Tahmini efor: 1–2 kişi-gün test.
- Bağımlılık: SAFE-10.
- Muhtemel dosyalar: evidence/shot_budget; UI shot counter; config maintenance thresholds.
- Kabul kriteri: Atış no → hız/isabet ilişkisi; aşama bazlı bütçe; yeni tüp/değişim eşiği; 24 başarılı hedef + ıska/test marjı; sayaç.
- Test / kanıt: Kontrollü seri, kronograf/sonuç varsa ölçüm, hit oranı ve tüp değişim süresi.
- Geri dönüş koşulu: Performans erken düşerse daha muhafazakâr değişim eşiği ve yedek tüp planı; finalde 30 atış varsayımına güvenilmez.

### OPS-03 — 30 dakika kurulum, 10 dakika bakım ve pit kitini prova et

- Öncelik / hedef kapı: P2 / final.
- Sahip rol: Saha Operatörü + Platform + Donanım.
- Tahmini efor: 2 kişi-gün.
- Bağımlılık: PLAT-07, OPS-02.
- Muhtemel dosyalar: docs/field_runbook.md — yeni; pit checklist/BOM.
- Kabul kriteri: Üç tam kurulum 30 dakika altında; üç bakım senaryosu toplam 10 dakika altında; her bakım talebi 30 saniye muhasebesi; kablo/USB/CO₂/yedek planı.
- Test / kanıt: Kronometreli tam prova videoları ve süre dökümü.
- Geri dönüş koşulu: Süre aşılırsa kit/iş sırası sadeleştirilir; gerekli olmayan bakım adımı/özellik final profilinden çıkarılır.

### OPS-04 — Kamera–namlu, home, zone ve saha profil kalibrasyonunu standartlaştır

- Öncelik / hedef kapı: P1 / Y2, A1–A3.
- Sahip rol: Vision/ML + Kontrol + Saha Operatörü.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: SAFE-08, PLAT-05.
- Muhtemel dosyalar: calibration_service.py; config profiles; frontend CalibrationView; docs/calibration_runbook.md.
- Kabul kriteri: 5/10/15 m paralaks, intrinsics, home, direction semantics, zones ve profile hash; değişiklik sonrası invalidation.
- Test / kanıt: Calibration target kayıtları, residual/error raporu ve bağımsız tekrar.
- Geri dönüş koşulu: Kalibrasyon residual’ı kabul dışıysa live fire yok; son kanıtlı profile veya yeniden mekanik hizalama.

## E. Video görevleri

### VID-01 — Y1 gerçek operatör akışını çekime hazırla

- Öncelik / hedef kapı: P0 / Y1.
- Sahip rol: Frontend/UX + Platform; destek Video.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: PLAT-07, SAFE-06.
- Muhtemel dosyalar: CockpitView.vue; SafetyModeBanner.vue; DeviceManagerPanel.vue; ilgili stores/API.
- Kabul kriteri: 45–60 sn’de gerçek camera/Pico/E-Stop/mode/track/FIRE-NO-FIRE/input/preflight; mock ana veri yok.
- Test / kanıt: Üç anlatım provası ve runtime truth ekran kaydı.
- Geri dönüş koşulu: Yeni UI gerçekliği gizler/kararsızsa son stabil operatör görünümü ve sözlü kısa anlatım kullanılır; kozmetik özellik çıkarılır.

### VID-02 — Y2 ölçülmüş 15 m imha kabulü

- Öncelik / hedef kapı: P0 / Y2.
- Sahip rol: Saha Operatörü + Kontrol + Test.
- Tahmini efor: 1–2 saha günü.
- Bağımlılık: SAFE-10, OPS-04, GOV-03.
- Muhtemel dosyalar: tracking/decision config; evidence/runs; video shot list.
- Kabul kriteri: Durağan taban, görünür 15 m ölçüm, güvenli backstop; 5’te 4 minimum, çekim öncesi 10’da 9 hedef; kesintisiz patlama kanıtı.
- Test / kanıt: Her run log/video/hash/CO₂; final geniş plan.
- Geri dönüş koşulu: Başarı oranı düşerse son kanıtlı model/config/calibration; model değişikliği ve Y6 çıkarılır.

### VID-03 — Y3 iki eksen hareket E-Stop kabulü

- Öncelik / hedef kapı: P0 / Y3.
- Sahip rol: Güvenlik/Donanım + Test + Video.
- Tahmini efor: 0,5–1 saha günü.
- Bağımlılık: SAFE-03, SAFE-10.
- Muhtemel dosyalar: evidence/runs; safety UI; video shot list.
- Kabul kriteri: Pan+tilt hareket, fiziksel buton, latched stop, otomatik resume yok; üç ardışık başarı.
- Test / kanıt: Kesintisiz geniş plan, telemetry ve ölçülmüş duruş.
- Geri dönüş koşulu: Tek başarısızlık safety release’i yeniden açar; final take yapılmaz.

### VID-04 — Y4 atış E-Stop kabulü

- Öncelik / hedef kapı: P0 / Y4.
- Sahip rol: Güvenlik/Donanım + Test + Video.
- Tahmini efor: 0,5–1 saha günü.
- Bağımlılık: SAFE-04, SAFE-10.
- Muhtemel dosyalar: evidence/runs; command/ACK logs; video shot list.
- Kabul kriteri: Önceden sayılı dizi, E-Stop öncesi en az bir atış, sonrası sıfır; queue replay yok; üç ardışık başarı.
- Test / kanıt: Kesintisiz geniş plan ve aynı run ID elektrik/command kaydı.
- Geri dönüş koşulu: E-Stop sonrası tek tetik olayı bile canlı atışı dondurur.

### VID-05 — Y5 iki eksenli hareketli takip kabulü

- Öncelik / hedef kapı: P0 / Y5.
- Sahip rol: Kontrol + Vision + Test.
- Tahmini efor: 2–3 kişi-gün + saha.
- Bağımlılık: SAFE-05, SAFE-09, OPS-04.
- Muhtemel dosyalar: auto_tracker_service.py; kalman_tracker.py; pid_controller.py; tracking_loop.py; config; UI overlay.
- Kabul kriteri: Hedef yatay+dikey, 10–15 s; track ID, kısa kayıp davranışı; osilasyon/limit yok; üç ardışık başarı; tetik kapalı olabilir.
- Test / kanıt: X/Y error, latency, track log ve fiziksel geniş video.
- Geri dönüş koşulu: Yeni tracker/PID salınım veya latency üretirse son kanıtlı Y5 profiline dönülür; fiziksel fire kapalı.

### VID-06 — Y6 sınıflandırma go/no-go kararı

- Öncelik / hedef kapı: P3 / 2 Ağustos.
- Sahip rol: Vision/ML + Takım Lideri.
- Tahmini efor: En çok 3 kişi-gün video öncesi.
- Bağımlılık: VID-01…VID-05 iki tam yeşil prova, A3-02, A3-03.
- Muhtemel dosyalar: model package, vision pipeline, UI label.
- Kabul kriteri: 4 sınıf × 3 mesafe kayıtlı; 15 m stabil; Y5 performans regresyonu yok; 45 sn altında anlatım.
- Test / kanıt: Confusion/stability matrisi ve iki zorunlu tam video regresyonu.
- Geri dönüş koşulu: Herhangi koşul kırmızıysa Y6 videodan ve video dalından çıkarılır; A3 dalı sürer.

### VID-07 — Storyboard, shot list ve kanıt eşlemesini kilitle

- Öncelik / hedef kapı: P0 / G4.
- Sahip rol: Video/Sunum + Test.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: VID-01…VID-05.
- Muhtemel dosyalar: docs/video_storyboard.md — yeni; shot list; YouTube açıklama taslağı.
- Kabul kriteri: 4:00–4:40; resmî sıra/numara; her planın requirement ve run ID’si; Y2/Y3/Y4 kesintisiz geniş plan.
- Test / kanıt: Masaüstü read-through ve iki bağımsız şartname kontrolü.
- Geri dönüş koşulu: Süre 5 dakikayı aşıyorsa konuşma/opsiyonel insert kesilir; zorunlu fiziksel kanıt kesilmez.

### VID-08 — Aynı rig ile iki tam kostümlü prova ve feature freeze

- Öncelik / hedef kapı: P0 / G4.
- Sahip rol: Takım Lideri + bütün roller.
- Tahmini efor: 1 tam gün.
- Bağımlılık: VID-07, SAFE-10, PLAT-06.
- Muhtemel dosyalar: evidence/full_video_rehearsal; frozen release manifest.
- Kabul kriteri: İki prova 2–5 dakika, Y1–Y5 yeşil, aynı PC/kablo/güç/kamera/E-Stop; 4 Ağustos 18:00 freeze.
- Test / kanıt: İki ham video, checklist ve release hash.
- Geri dönüş koşulu: Prova kırılırsa çekim ertelenir, storyboard/opsiyonel özellik sadeleşir; freeze sonrası yeni feature yok.

### VID-09 — Çekim, kurgu, YouTube ve KYS teslimini kapat

- Öncelik / hedef kapı: P0 / G5.
- Sahip rol: Video/Sunum + KYS sorumlusu; yedek kişi.
- Tahmini efor: 3 gün takvim, 2–3 kişi-gün aktif.
- Bağımlılık: VID-08.
- Muhtemel dosyalar: Ham/final video, açıklama, teslim kanıtı; kaynak kod yok.
- Kabul kriteri: En az 720p; 2–5 dk; doğru sıra/numara/timestamps; liste dışı link iki cihaz/ağda; KYS iç teslim 10 Ağustos 12:00.
- Test / kanıt: Final SHA-256, link test ekranları, KYS gönderim kanıtı, iki disk yedek.
- Geri dönüş koşulu: Link/işleme sorunu varsa doğrulanmış yedek upload; son gün yeni kurgu/özellik değil yalnız teslim kurtarma.

## F. Final Aşama 1

### A1-01 — Joystick/gamepad ve klavye yedek girişini ürünleştir

- Öncelik / hedef kapı: P1 / A1.
- Sahip rol: Kontrol/Backend + Frontend; destek Saha Operatörü.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: SAFE-05, SAFE-09.
- Muhtemel dosyalar: Yeni input service/API; mission_service.py; MissionModesView.vue; mission store/types; config input profile.
- Kabul kriteri: Dead-zone/eğri/fine aim; güvenli tetik; focus/key-up/disconnect safe stop; kalibrasyon UI; klavye yedek.
- Test / kanıt: Unit, HIL ve iki operatör usability; stuck key/disconnect fiziksel hareket üretmiyor.
- Geri dönüş koşulu: Input kaybında hareket sürerse ilgili cihaz desteği kapatılır ve son kanıtlı manuel giriş profiline dönülür.

### A1-02 — AŞAMA1_MANUAL mod izolasyonunu uygula

- Öncelik / hedef kapı: P1 / A1.
- Sahip rol: Kontrol/Backend.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: SAFE-06, A1-01.
- Muhtemel dosyalar: mission_service.py; decision_engine.py; command_gateway.py; runtime_state.py; mission schemas.
- Kabul kriteri: Yalnız kullanıcı niyeti fiziksel hareket/ateş üretir; tracker yalnız overlay; mod geçişinde queue/track engagement temiz; auto servisler TX yapamaz.
- Test / kanıt: Negatif integration testleri ve HIL command trace.
- Geri dönüş koşulu: Otonom komut manual moda sızarsa A1 build’i NO-GO, fiziksel arm kapalı ve mod state machine geri alınır.

### A1-03 — Zarf sırası ve ilk Balistik Füze korumasını ekle

- Öncelik / hedef kapı: P1 / A1.
- Sahip rol: Backend + Frontend/UX.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: A1-02.
- Muhtemel dosyalar: mission_service.py; schemas/mission.py; api/mission.py; MissionModesView.vue; missionStore.ts.
- Kabul kriteri: Dört hedef read-back ile kilitlenir; ilk hedef Balistik Füze doğrulaması; sıradaki hedef ve yanlış niyet uyarısı; yarışma sırasında izinsiz sıra değişmez.
- Test / kanıt: Bütün permütasyon ve yanlış-ilk-hedef testleri; operatör prova videosu.
- Geri dönüş koşulu: Guard doğru hedefi yanlış engellerse manuel confirm yedeği yalnız iki kişi read-back ve event log ile; guard sessizce kapatılamaz.

### A1-04 — Resmî Aşama 1 skor, ceza, timer ve bonus motorunu düzelt

- Öncelik / hedef kapı: P1 / A1.
- Sahip rol: Backend.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: GOV-02, A1-03.
- Muhtemel dosyalar: mission_service.py; schemas/mission.py; backend/tests/test_mission_operations.py.
- Kabul kriteri: 5/10/20 puan; en çok 80 görev; yanlış hedef eksi 5; 300 s; yalnız 80 sonrası doğru bonus; 30 barajı.
- Test / kanıt: Şartname örnek vektörleri ve sınır zaman testleri; UI-backend eşitliği.
- Geri dönüş koşulu: Resmî yorum değişirse versioned scoring profile; eski yanlış motor kullanılmaz.

### A1-05 — 5/10/15 m manuel aim/paralaks profilini çıkar

- Öncelik / hedef kapı: P1 / A1.
- Sahip rol: Kontrol + Vision + Saha Operatörü.
- Tahmini efor: 2 saha günü.
- Bağımlılık: OPS-04, OPS-02.
- Muhtemel dosyalar: calibration_service.py; calibration profiles; UI crosshair; evidence.
- Kabul kriteri: Mesafe başına kamera–namlu ofset, backlash ve CO₂ etkisi; operatör profile göre doğru nişangâh; residual kabul eşiği.
- Test / kanıt: Her mesafe çoklu atış matrisi ve hit oranı.
- Geri dönüş koşulu: 15 m güvenilir değilse önce 30 puan geçişini koruyan orta/yakın plan; agresif uzun menzil varsayılan olmaz.

### A1-06 — Aşama 1 tam görev acceptance’ı

- Öncelik / hedef kapı: P1 / G6.
- Sahip rol: Test/Kanıt + Saha Operatörü.
- Tahmini efor: 2 saha günü.
- Bağımlılık: A1-01…A1-05, SAFE-10.
- Muhtemel dosyalar: evidence/a1; scoreboard.
- Kabul kriteri: Son 10 tur 10/10 ilk füze ve sıra, 0 yanlış hedef, en az 9 tamamlama, en az 8 tur 90+, en az 3 tur 95+.
- Test / kanıt: Video, skor/timer event log, input ve command trace, atış/CO₂ kaydı.
- Geri dönüş koşulu: Hız hatayı artırırsa son güvenilir hız profili; önce 80 görev puanı ve geçiş barajı korunur.

## G. Final Aşama 2

### A2-01 — Üç hedefli kalıcı live tracker’ı devreye al

- Öncelik / hedef kapı: P1 / A2.
- Sahip rol: Vision/ML + Kontrol.
- Tahmini efor: 4–6 kişi-gün.
- Bağımlılık: VID-05, PLAT-10.
- Muhtemel dosyalar: auto_tracker_service.py; kalman_tracker.py; vision_pipeline.py; schemas/tracking.py; config.
- Kabul kriteri: En az üç eşzamanlı track; gerçek Kalman/ByteTrack veya kanıtlı eşdeğer; age/hit/miss/freshness/hız; kısa occlusion; using_kalman/live tracker gerçeği telemetride.
- Test / kanıt: Replay ID-switch/fragmentation ölçümü ve HIL üç hedef.
- Geri dönüş koşulu: ID switch veya latency baseline’dan kötüleşirse son kanıtlı tracker; tek-frame nearest canlı fire’a dönülmez.

### A2-02 — Generic body–balon association’ı uygula

- Öncelik / hedef kapı: P1 / A2.
- Sahip rol: Vision/ML.
- Tahmini efor: 3–4 kişi-gün.
- Bağımlılık: A2-01.
- Muhtemel dosyalar: Yeni association service; vision_pipeline.py; tracking schemas; config geometry.
- Kabul kriteri: 1/1, 2/2, 3/3; temporal/geometric link; orphan/ambiguous durumları; yalnız stable link fire adayı.
- Test / kanıt: Çapraz/yakın/kayıp replay matrisi ve fiziksel iki/üç maket.
- Geri dönüş koşulu: Yanlış link görülürse fiziksel fire kapalı; daha muhafazakâr stable threshold veya son kanıtlı geometri profili.

### A2-03 — Time-to-exit ve puan odaklı hedef önceliğini uygula

- Öncelik / hedef kapı: P1 / A2.
- Sahip rol: Kontrol/Backend.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: A2-01, A2-02.
- Muhtemel dosyalar: auto_tracker_service.py; mission_service.py; config priority weights.
- Kabul kriteri: Çıkışa kalan süre, çözüm kalitesi, dönüş maliyeti, önceki shot/hit ve yeniden angajman fırsatı; nearest-only yok; hysteresis.
- Test / kanıt: Replay senaryolarında 3/3 oranı ve karar açıklaması; ablation karşılaştırması.
- Geri dönüş koşulu: Yeni öncelik 3/3 oranını düşürür/ping-pong üretirse son yüksek skor ağırlıkları.

### A2-04 — Ölçülmüş latency tabanlı motion lead uygula

- Öncelik / hedef kapı: P1 / A2.
- Sahip rol: Kontrol + Vision.
- Tahmini efor: 2–4 kişi-gün.
- Bağımlılık: A2-01, OPS-04, PLAT-08.
- Muhtemel dosyalar: pid_controller.py; auto_tracker_service.py; performance_service.py; config.
- Kabul kriteri: Frame→guidance latency ve track hızıyla kısa öngörü; hız/ivme/limit; baseline’a göre merkezleme/hit iyileşmesi.
- Test / kanıt: A/B replay ve fiziksel p50/p95 error/hit.
- Geri dönüş koşulu: Osilasyon, overshoot veya hit düşüşünde lead feature flag kapalı ve stabil merkezleme profili.

### A2-05 — Hit confirmation ve yeniden angajman

- Öncelik / hedef kapı: P1 / A2.
- Sahip rol: Vision + Backend; destek Firmware/Donanım.
- Tahmini efor: 3 kişi-gün.
- Bağımlılık: A2-02, SAFE-05.
- Muhtemel dosyalar: vision_pipeline.py; mission_service.py; decision_engine.py; command_gateway.py; shot event schemas.
- Kabul kriteri: Atış sonrası hedef hemen tamamlanmaz; balon kaybı/patlama/opsiyonel sensörle confirm; timeoutta reengage; cooldown ve shot budget.
- Test / kanıt: Hit/miss replay, kontrollü physical; duplicate/boşa shot ölçümü.
- Geri dönüş koşulu: False hit confirmation hedef kaçırırsa daha muhafazakâr doğrulama; sensör güvenilmezse vision+time kuralı ve explicit unconfirmed.

### A2-06 — Resmî Aşama 2 tur ve skor motorunu uygula

- Öncelik / hedef kapı: P1 / A2.
- Sahip rol: Backend + Frontend.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: GOV-02, A2-05.
- Muhtemel dosyalar: mission_service.py; schemas/mission.py; API; mission UI/store.
- Kabul kriteri: Dört tur; 1/2/3 hedef 5/15/30; zero-hit eksi 5; başarısızlık kuralı; 20 barajı; tur reset ve event log.
- Test / kanıt: Bütün skor kombinasyonları ve sıfırlama testleri.
- Geri dönüş koşulu: Resmî yorum güncellenirse versioned profile; tracker/fire mantığı scoring’den ayrık kalır.

### A2-07 — Aşama 2 dört-turluk acceptance

- Öncelik / hedef kapı: P1 / G7.
- Sahip rol: Test/Kanıt + Saha Operatörü.
- Tahmini efor: 3 saha günü.
- Bağımlılık: A2-01…A2-06, OPS-02.
- Muhtemel dosyalar: evidence/a2; scoreboard.
- Kabul kriteri: Üç tam seri; her biri 105+, en az biri 120; son 12 turun en az 10’u 3/3; zero-hit tur yok; yanlış link/safety bypass yok.
- Test / kanıt: Track/association/priority/shot/hit/score logları ve geniş video.
- Geri dönüş koşulu: Son değişiklik skoru düşürürse son 105+ release; deney feature flag’leri kapalı.

## H. Final Aşama 3 ve perception

### A3-01 — Güncel hedef revizyonu ve gerçek veri planını kilitle

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Vision/ML + Test.
- Tahmini efor: 1 kişi-gün; haftalık takip.
- Bağımlılık: GOV-02.
- Muhtemel dosyalar: dataset manifest; model docs; official asset hash record.
- Kabul kriteri: Güncel 3MF/hash, basılı maket farkı, 5/10/15 m capture plan, dost/düşman ve balon renk varyasyonları, leakage’siz split.
- Test / kanıt: Dataset manifest ve capture coverage tablosu.
- Geri dönüş koşulu: Resmî hedef revizyonu değişirse etkilenen sınıf/model acceptance’ı açılır; eski veriye kör güven yok.

### A3-02 — Gerçek body model adapter ve runtime profilini devreye al

- Öncelik / hedef kapı: P1 / Y6-A3.
- Sahip rol: Vision/ML.
- Tahmini efor: 3–5 kişi-gün, model hazırsa.
- Bağımlılık: A3-01, GOV-03.
- Muhtemel dosyalar: vision_pipeline.py; inference_adapter_service.py; model_package_service.py; model_registry_service.py; models/active/registry.json; config/runtime/vision_profile.active.yaml.
- Kabul kriteri: OpenCV circle surrogate yerine seçilebilir gerçek model; body_detections dolu; body ve balloon semantiği ayrık; model ID/threshold/profile runtime truth.
- Test / kanıt: Golden images gerçek tensor çıktısı, API/UI runtime profile ve replay.
- Geri dönüş koşulu: Model hazır/değilse video baseline adapter’dan ayrık kalır; A3 fire NO-GO, surrogate production diye gösterilmez.

### A3-03 — Gerçek class ID/provenance ve model package doğrulaması

- Öncelik / hedef kapı: P1 / Y6-A3.
- Sahip rol: Vision/ML + Test.
- Tahmini efor: 1–2 kişi-gün.
- Bağımlılık: A3-02.
- Muhtemel dosyalar: models/active/registry.json; active_models.json; model_package_service.py; fixtures/model_packages; classes/metadata.
- Kabul kriteri: box.cls gerçekten okunur; dost/düşman veya sınıf semantiği balloon diye ezilmez; metadata iddiası golden inference ile doğrulanır; provenance/hash.
- Test / kanıt: Her class için golden output ve yanlış mapping negatif testi.
- Geri dönüş koşulu: Mapping belirsizse model yüklenmez; production_ready etiketi kaldırılır.

### A3-04 — Gerçek piksel tabanlı, yapılandırılabilir IFF

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Vision/ML.
- Tahmini efor: 3–5 kişi-gün.
- Bağımlılık: A3-02, PLAT-05.
- Muhtemel dosyalar: color_classifier_service.py; schemas/color.py; calibration/color API/UI; config field profile.
- Kabul kriteri: Request mock_team değil gerçek body ROI; friend/enemy renkleri profil; temporal aggregation; UNKNOWN/AMBIGUOUS; balon rengi etkisiz.
- Test / kanıt: Ters renk profili, ışık/white balance, aynı sınıf dost+düşman; confusion matrix.
- Geri dönüş koşulu: Bir false-enemy fiziksel olayda A3 fire dondurulur ve IFF yeniden kalibre edilir.

### A3-05 — Sınıfa özel body–balon association

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Vision/ML.
- Tahmini efor: 3–5 kişi-gün.
- Bağımlılık: A2-02, A3-02.
- Muhtemel dosyalar: association service; vision_pipeline.py; official model geometry config; tracking schemas.
- Kabul kriteri: Sınıfa özgü bağlantı bölgesi, temporal motion ve bipartite matching; dost yanından geçen balon yanlış bağlanmaz; stable/ambiguous/orphan.
- Test / kanıt: 1/1, 2/2, 3/3, dost+düşman yakın geçiş replay/fiziksel.
- Geri dönüş koşulu: Yanlış linkte canlı fire kapalı; daha muhafazakâr threshold/geometri.

### A3-06 — Gerçek homography/intrinsics ve metrik menzil

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Vision/ML + Kontrol.
- Tahmini efor: 4–6 kişi-gün.
- Bağımlılık: OPS-04, A3-02.
- Muhtemel dosyalar: calibration_service.py; vision_pipeline.py; new range service; config calibration profiles.
- Kabul kriteri: Identity matrix/sıfır sahte hata yok; gerçek intrinsics/distortion/homography veya doğrulanmış geometri; metre+belirsizlik; sınıfa göre 5/10/15 m kalibrasyon.
- Test / kanıt: Holdout mesafe/angle hata dağılımı ve sınır testleri.
- Geri dönüş koşulu: Hata aralığı menzil penceresini güvenle ayıramazsa ilgili sınıf fire NO-GO veya mevcut uygun sensör füzyonu.

### A3-07 — Sınıf/IFF/link/range tabanlı engagement manager

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Kontrol/Backend + Vision.
- Tahmini efor: 3–4 kişi-gün.
- Bağımlılık: A3-03…A3-06, SAFE-06.
- Muhtemel dosyalar: decision_engine.py; mission_service.py; new engagement manager; schemas/decision/tracking; config.
- Kabul kriteri: F-16 10–15; Heli/Füze 5–15; Mini 0–15; yalnız ENEMY+STABLE_LINK; token hedef bağlamlı; UI reason chain.
- Test / kanıt: Kural tablosu unit/replay; her fire event’te class/IFF/link/range/safety snapshot.
- Geri dönüş koşulu: Bir pencere veya dost kural ihlali canlı A3’ü kapatır; fail-closed release.

### A3-08 — Dost güvenliği ve ambiguity red regresyon paketi

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Test/Kanıt + Vision + Güvenlik.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: A3-07.
- Muhtemel dosyalar: new A3 replay fixtures/tests; evidence.
- Kabul kriteri: Dost, unknown, ambiguous, orphan, stale, menzil dışı, zone ve ters renk profillerinde fire output sıfır.
- Test / kanıt: En az 100 replay olayı, HIL ve seçili fiziksel no-fire senaryoları.
- Geri dönüş koşulu: Tek dost fire candidate bile release bloklar; model/threshold gevşetilmez.

### A3-09 — Tur deadline, reacquire ve üç ardışık miss koruması

- Öncelik / hedef kapı: P1 / A3.
- Sahip rol: Backend/Kontrol.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: A3-07, A2-05.
- Muhtemel dosyalar: mission_service.py; engagement manager; UI turn state.
- Kabul kriteri: Sekiz tur; miss streak; güvenli reacquire/reengage deadline; üç ardışık miss erken uyarısı; dışarıdan hedef yönlendirme yok.
- Test / kanıt: Replay fault scenarios ve HIL turn state trace.
- Geri dönüş koşulu: Recovery güvenlik kapısını zorlarsa konservatif karar; geç angajman yerine yeniden acquisition iyileştirilir.

### A3-10 — Aşama 3 sekiz-turluk acceptance

- Öncelik / hedef kapı: P1 / G8.
- Sahip rol: Test/Kanıt + Saha Operatörü + Güvenlik.
- Tahmini efor: 4 saha günü.
- Bağımlılık: A3-01…A3-09, OPS-02.
- Muhtemel dosyalar: evidence/a3; scoreboard; final release manifest.
- Kabul kriteri: Üç tam sekiz-tur seri; her biri 120+, en az biri 140+; dost vuruşu 0; üç ardışık miss yok; bütün fire kararları tam zincirli.
- Test / kanıt: Tur video/log, class/IFF/link/range/safety/command/ACK, skor ve CO₂.
- Geri dönüş koşulu: Dost, menzil veya association safety ihlalinde A3 live fire dondurulur; son sıfır-dost release veya NO_FIRE.

## I. Kanıt, kalite ve jüri

### EVD-01 — Ortak run ID, timestamp ve immutable event sözleşmesi

- Öncelik / hedef kapı: P0/P2 / video ve final.
- Sahip rol: Backend + Test/Kanıt.
- Tahmini efor: 2 kişi-gün.
- Bağımlılık: GOV-03, SAFE-05.
- Muhtemel dosyalar: log_service.py; report_export_service.py; schemas/log/session; command/decision services.
- Kabul kriteri: Frame/track/decision/command/ACK/shot/hit/video aynı run/correlation ID; monotonic+wall clock; config/model/firmware hash.
- Test / kanıt: Uçtan uca bir run timeline’ı ve schema testleri.
- Geri dönüş koşulu: Event eşleşmesi kırılırsa kanıt geçersiz; sade JSONL manifest ve manuel video mapping geçici yedek.

### EVD-02 — Tek gereksinim izlenebilirlik matrisi

- Öncelik / hedef kapı: P2 / sürekli.
- Sahip rol: Test/Kanıt.
- Tahmini efor: 1 kişi-gün; günlük güncelleme.
- Bağımlılık: GOV-02, EVD-01.
- Muhtemel dosyalar: evidence/requirements_traceability.md/json — yeni.
- Kabul kriteri: Resmî requirement → tasarım → kod/firmware → test → son kanıt → R/Y/G; kanıtsız green yok.
- Test / kanıt: Haftalık bağımsız audit ve broken-link/hash kontrolü.
- Geri dönüş koşulu: Kaynak revizyonunda etkilenen satırlar sarı/kırmızı ve yeniden acceptance.

### EVD-03 — Otomatik/küratörlü evidence pack üretimi

- Öncelik / hedef kapı: P2 / video-final.
- Sahip rol: Test/Kanıt + Backend.
- Tahmini efor: 2–3 kişi-gün.
- Bağımlılık: EVD-01, PLAT-03.
- Muhtemel dosyalar: report_export_service.py; evidence export script; storage_paths.py.
- Kabul kriteri: Manifest, snapshots, metrics, safety decisions, commands/ACK, video link/hash; yalnız seçili 5–10 klip ve özet; disk kotası.
- Test / kanıt: Bir video ve bir full mission paketinin temiz makinede doğrulanması.
- Geri dönüş koşulu: Otomasyon kritik dosya kaçırırsa manuel imzalı manifest; 235 rapor topluca jüriye verilmez.

### EVD-04 — Test kalitesini davranış tabanlı hale getir

- Öncelik / hedef kapı: P2 / sürekli.
- Sahip rol: Test/Kanıt + alan geliştiricileri.
- Tahmini efor: 3–5 kişi-gün, iteratif.
- Bağımlılık: PLAT-09.
- Muhtemel dosyalar: backend/tests; frontend test setup — yeni; CI.
- Kabul kriteri: String/yorum varlığına dayalı kritik testler gerçek davranış assertion’ına döner; safety/mission/vision contract; frontend operator critical component tests; coverage trend.
- Test / kanıt: Mutation/negatif test örnekleri; test gerçekten bozuk davranışı yakalıyor.
- Geri dönüş koşulu: Test rewrite ürün işini bloke ederse önce P0/P1 contract testleri; kozmetik testler ertelenir.

### EVD-05 — KTR-plan-gerçekleşen fark matrisi ve final sunumu

- Öncelik / hedef kapı: P2 / final sunumu 40.
- Sahip rol: Video/Sunum + Takım Lideri + alan liderleri.
- Tahmini efor: 3 kişi-gün.
- Bağımlılık: EVD-02, A1-06, A2-07, A3-10.
- Muhtemel dosyalar: docs/final_presentation; evidence/ktr_delta.md.
- Kabul kriteri: KTR’de hedeflenen/uygulanan/değişen/neden/ölçüm/kanıt; 10 slayt; her iddia bir sayı+kanıt; başarısız deney dürüstçe açıklanır.
- Test / kanıt: İki jüri provası, süre ve soru listesi.
- Geri dönüş koşulu: Fiziksel kanıtsız iddia çıkarılır; demo/mock gerçekmiş gibi sunulmaz.

### EVD-06 — Teknik mülakat ve final saha dossier’i

- Öncelik / hedef kapı: P2 / G9.
- Sahip rol: Takım Lideri + tüm teknik roller.
- Tahmini efor: 2 kişi-gün + iki prova.
- Bağımlılık: EVD-03, EVD-05, OPS-03.
- Muhtemel dosyalar: docs/jury_qna.md; evidence/final_dossier.
- Kabul kriteri: Her konu birincil/yedek konuşmacı; danışmansız iki çapraz sorgu; requirement matrisi, as-built, safety, A1/A2/A3, setup/bakım/CO₂ ve release manifest tek dosyada.
- Test / kanıt: Kaydedilmiş mock jury ve eksik cevap aksiyonları.
- Geri dönüş koşulu: Cevabı kanıtsız konu sunumdan sadeleştirilir veya ilgili sahibi yeniden eğitilir.

## J. Ek P0 teknik gerçeklik görevleri

### SAFE-11 — full_active / allow_physical_fire geçişini preflight ve yetki token’ına bağla

- Öncelik / hedef kapı: P0 / G2.
- Sahip rol: Kontrol/Backend + Güvenlik.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: SAFE-05, SAFE-06.
- Muhtemel dosyalar: backend/app/api/routes_safety.py; safety_service.py; runtime_state.py; frontend SafetyModeBanner.
- Kabul kriteri: Tek endpoint çağrısıyla dry_run false ve fiziksel fire açılamaz; güncel preflight, fiziksel arm, rol/yetki, kısa TTL ve audit gerekir; reset/reconnect’te kapanır.
- Test / kanıt: Yetkisiz/expired/stale token negatif API ve HIL testleri.
- Geri dönüş koşulu: Bypass ile full_active açılırsa endpoint fiziksel fire için kapatılır; yalnız DRY_RUN erişimi.

### PLAT-10 — Tek camera producer, tek inference worker ve timestamp’li state bus

- Öncelik / hedef kapı: P0 / Y5 ve güvenlik.
- Sahip rol: Vision/ML + Backend/Platform.
- Tahmini efor: 3–5 kişi-gün.
- Bağımlılık: PLAT-05, GOV-03.
- Muhtemel dosyalar: vision_pipeline.py; camera_runtime_service.py; runtime_state.py; LiveCameraPanel.vue; WebSocket/REST consumers.
- Kabul kriteri: Browser/REST tekrar inference üretmez; son frame timestamp/freshness; stale browser event fiziksel karar olamaz; tek producer state snapshot.
- Test / kanıt: Browser kapanma, 650 ms event, frame freeze ve çoklu consumer fault tests; stale fire sıfır.
- Geri dönüş koşulu: Yeni worker Y5 latency/kararlılığını bozarsa son kanıtlı tek-process producer; browser event live fire girdisi olarak kapalı kalır.

### PLAT-11 — Self-test ve runtime readiness’i fail-closed yap

- Öncelik / hedef kapı: P0 / G3.
- Sahip rol: Backend + Platform + Güvenlik.
- Tahmini efor: 1 kişi-gün.
- Bağımlılık: SAFE-06, PLAT-07.
- Muhtemel dosyalar: self_test_service.py; routes health/system; frontend self-test/health stores.
- Kabul kriteri: Hardware disabled, warning, stale veya incompatible durumda overall_ready yanlış true olamaz; görev/fire readiness ayrı ve reason code’lu.
- Test / kanıt: Durum tablosu unit/integration ve UI truth kontrolü.
- Geri dönüş koşulu: Readiness yanlış pozitif üretirse görev başlatma/fire kapalı; ham alt health durumları gösterilir.

## K. Uygulama dalgaları

### Dalga 0 — Onay

GOV-01, GOV-02.

### Dalga 1 — İlk 72 saat

GOV-03, SAFE-01, OPS-01, PLAT-01, OPS-02 başlangıcı.

### Dalga 2 — Video güvenlik çekirdeği

SAFE-02…SAFE-09, SAFE-11, PLAT-10.

### Dalga 3 — Video saha güvenilirliği

PLAT-02…PLAT-07, PLAT-09, PLAT-11, OPS-04, SAFE-10, VID-01…VID-05.

### Dalga 4 — Video teslim

VID-06 go/no-go, VID-07…VID-09.

### Dalga 5 — Final yüksek güvenilir puan

A1-01…A1-06, A2-01…A2-07, OPS-02…OPS-03.

### Dalga 6 — Birincilik farkı

A3-01…A3-10, PLAT-08, EVD-01…EVD-06.

Bir sonraki dalga, önceki dalganın ilgili go/no-go kapısı yeşil olmadan ana yarışma release’ine girmez.
