# 02 — Mevcut Durum ve Kritik Boşluklar

## 1. Yönetici özeti

Proje güçlü bir arayüz, geniş raporlama altyapısı, çalışan kamera/Pico geçmişi ve iki balonun ardışık imhasını gösteren fiziksel kanıta sahip. Fakat mevcut depo hâlâ güvenilir bir yarışma sistemi değildir. En önemli neden, gerçek fiziksel komut yolunun karar/güvenlik mimarisinden kopuk olması ve final perception zincirinin çoğunun gerçek inference akışında bulunmamasıdır.

## 2. Güçlü taraflar

- İki balon ardışık olarak fiziksel biçimde imha edilmiş.
- Dış USB kameradan gerçek kare alma kabul kanıtı var.
- FastAPI + Vue/TypeScript mimarisi, operatör/mühendis ayrımı ve cihaz panelleri geniş.
- Replay, rapor, model paketi ve dijital ikiz için kullanılabilir altyapı kabukları var.
- Pico, serial, camera, motion, decision ve mission alanlarında test tabanı mevcut.
- UI jüri anlatımı için görsel olarak güçlü.
- KTR geçmişi mekanik ve sistem mimarisi açısından ciddi mühendislik emeği gösteriyor.

## 3. Kanıtlanmış ve kanıtlanmamış durum

| Yetenek | Durum |
|---|---|
| Gerçek kamera kare akışı | Kanıt var |
| Pico ile fiziksel hareket/atış geçmişi | Kanıt var |
| İki balonun sırayla imhası | Kanıt var |
| Ölçülmüş 15 m imha | Kanıt yok |
| Hareket sırasında fiziksel E-Stop | Kanıt yok |
| Ateş sırasında fiziksel E-Stop | Kanıt yok |
| İki eksenli hareketli hedef takibi | Güncel acceptance yok |
| Kalıcı çoklu track ID | Gerçek akışta kanıt yok |
| Gerçek hava aracı sınıflandırması | Kanıt yok |
| Dost/düşman ve doğru balon bağlantısı | Kanıt yok |
| Gerçek metrik menzil | Kanıt yok |
| Windows/offline yarışma paketi | Kanıt yok |
| 30 dakika kurulum / 10 dakika bakım | Tam prova yok |

## 4. En kritik mimari açıklar

### G-01 — Güvenlik ve gerçek atış yolu birbirinden kopuk

backend/app/services/tracking_loop.py içinde FIRE_REQUIRED_FRAMES değeri 1’dir ve merkezleme sonrası doğrudan send_fire_command çağrısı üretilebilmektedir. Bu yol DecisionEngine, gerçek IFF, menzil, E-Stop, yasak bölge ve kararlı track kapılarını atlar.

Diğer tarafta ana Fire Gate API yolu her atış talebini reddeden bir yapıda kalmıştır. Sonuç: güvenli görünen mimari ile fiziksel çalışan yol aynı yol değildir.

Ayrıca backend/app/api/routes_safety.py içindeki operational mode geçişi full_active seçildiğinde allow_physical_fire=true ve dry_run=false durumunu tek runtime çağrısıyla açabilmektedir. Bu geçiş güncel preflight, fiziksel arm ve kısa ömürlü yetki token’ına bağlı değildir.

Karar: Bütün fiziksel komutlar tek SafetyDecision → CommandGateway → Pico zincirine taşınmadan canlı test yok.

### G-02 — Firmware, pin ve E-Stop gerçeği çelişkili

- README/çalıştırma geçmişi eski Arduino firmware’ini aktif gösteriyor.
- config/config.yaml ve MicroPython tarafı E-Stop için GP20 bildiriyor.
- Arduino firmware GP18 kullanıyor.
- Aynı pin başka profil anlatımlarında tilt limit olarak geçiyor.
- Arduino firmware motorları E-Stop’ta durduruyor; LZR tetik komutunda doğrudan E-Stop kontrolü görünmüyor.
- KTR’de 24 V motor hattı ile 6 V servo hattı ayrı anlatılıyor; fiziksel E-Stop’un gerçek tetik enerjisini kestiği ölçülmemiş.

Karar: Fotoğraflı kablo şeması, multimetre/süreklilik ölçümü, tek pin sözleşmesi ve kanonik firmware olmadan sistem arm edilmez.

### G-03 — Final perception çekirdeği gerçek değil

backend/app/services/vision_pipeline.py gerçek YOLO akışında BalloonDetection üretirken body_detections boş bırakılıyor. Böylece:

- Gerçek gövde sınıfı yok.
- Gerçek IFF bağlamı yok.
- Hedef–balon association yok.
- Sınıfa göre menzil kapısı yok.
- Aşama 3 kararı üretilemiyor.

Model package doğrulamasında metadata iddiası ile gerçek sınıf çıktısı birbirine karışabiliyor. Inference cihazı kodda CPU’ya sabitlenmiş görünüyor.

Ek somut bulgular:

- models/active/registry.json içindeki legacy sınıf semantiği dost/düşman iken iki balloon sınıfı gibi kaydedilmiş.
- vision_pipeline.py gerçek box.cls değerini korumadan kutuları BalloonDetection’a dönüştürüyor.
- config/runtime/vision_profile.active.yaml aktif profili opencv_live_circle_surrogate olarak gösteriyor; body ve balloon model ID’leri boş.
- models/active/active_models.json seçimi aktif runtime profiline güvenilir biçimde yansımıyor.

Karar: Model adapter, gerçek logits/sınıf mapping testi ve GPU benchmark olmadan production-ready etiketi kullanılmaz.

### G-04 — Tracking ve görev mantığı yarışma şartnamesini karşılamıyor

- auto_tracker_service.py en yakın balonu seçmeye odaklı.
- Gerçek çoklu kalıcı iz ve time-to-exit önceliği yok.
- MissionService Aşama 1–3 puan/cezalarını şartnameye uygun hesaplamıyor.
- Joystick/gamepad entegrasyonu bulunamadı.
- Aşama 3 zinciri yok.

Karar: Aşama motorları ayrı ama ortak güvenlik/komut altyapısı kullanan ürün modları olarak kurulmalı.

### G-05 — Cihaz ve platform saha için kırılgan

- Device ID port/path tabanlı; Pico handshake ile kalıcı kimlik yok.
- Kamera keşfi Linux /dev/video yaklaşımına bağlı.
- COM veya kamera index değiştirmek için config/kod düzenleme anlatımları var.
- Windows launcher Python, uv ve internet erişimi bekliyor.
- Gerçek offline paket ve GPU doğrulaması yok.
- MicroPython PING JSON döndürürken backend raw probe farklı bir OK,PONG yanıtı bekleyebiliyor.
- Real-write serial yolu gerçek ACK almadan komutu “sent” sayabiliyor.
- Browser’dan bir kez gelen inference olayı freshness timeout olmadan yeniden kullanılabiliyor; tarayıcı kapanınca son frame canlı track gibi kalabilir.
- Self-test, hardware disabled veya warning durumunda overall_ready=true üretebiliyor.

Karar: Video için en düşük riskli golden rig seçilir; cihaz kimliği ve preflight kod düzenlemeden çalışır.

### G-06 — Depo operasyonel olarak kontrolsüz büyümüş

- Repo yaklaşık 70 GB.
- exports/release yaklaşık 54 GB.
- logs/backend.jsonl yaklaşık 8,7 GB.
- backend/.venv yaklaşık 5,4 GB.
- Release testi çıktı klasörünü tekrar pakete alarak ENOSPC oluşturabiliyor.
- Release service frontend dist’i birden fazla kez kopyalayabiliyor.

Karar: Golden baseline ve artefact sınıflaması alınmadan temizlik yok; ardından retention, bounded package ve log rotation uygulanır.

### G-07 — Kalibrasyon ve IFF servisleri gerçek ölçüm yerine placeholder taşıyor

- calibration_service.py homography için identity matrix ve sıfır hata döndürebiliyor.
- color_classifier_service.py gerçek gövde pikseli yerine request içindeki mock_team alanını kullanıyor.
- Gerçek metrik menzil üretimi yok.

Karar: Bu servisler jüri demosu veya Aşama 3 fire girdisi sayılmaz. Gerçek görüntü, kalibrasyon holdout’u ve hata dağılımı olmadan ilgili kapı NO-GO’dur.

### G-08 — Test sayısı güvenilirlik anlamına gelmiyor

- Seçilmiş 166 çekirdek backend testi geçti.
- Toplam 407 testin yaklaşık 160’ı string/yorum varlığı gibi zayıf assertion’lara dayanıyor.
- Frontend production build geçti; unit/component testi yok.
- CI, coverage kapısı ve pre-commit bulunmuyor.

Karar: P0/P1 alanlarında davranış, negatif durum ve uçtan uca contract testleri önceliklendirilir; ham test sayısı başarı metriği değildir.

## 5. Gereksinim–boşluk matrisi

| Gereksinim | Mevcut | Açık | Öncelik | Ana görevler |
|---|---|---|---|---|
| Video Y1 | Güçlü UI | Gerçek runtime truth ve sade akış | P0 | VID-01, PLAT-07 |
| Video Y2 | İki balon videosu | Ölçülü 15 m ve tekrar | P0 | VID-02 |
| Video Y3 | UI temsili | Gerçek iki eksen duruşu | P0 | SAFE-03, VID-03 |
| Video Y4 | Kanıt yok | Tetik enerjisi ve kuyruk kesme | P0 | SAFE-04, VID-04 |
| Video Y5 | Balon merkezleme geçmişi | Kalıcı ID, iki eksen, stabilite | P0 | VID-05 |
| Ebat 20 | Yaklaşık 60 cm | Tolerans marjı | P0/P2 | OPS-01 |
| Aşama 1 | Mission ekranı | Gerçek manuel giriş/sıra/skor | P1 | A1-01…A1-06 |
| Aşama 2 | Tek balon takibi | Üç iz, association, öncelik | P1 | A2-01…A2-07 |
| Aşama 3 | Şema/mock | Body, IFF, range, link | P1 | A3-01…A3-10 |
| Güvenli komut | Parçalı kapılar | Tek fiziksel gateway yok | P0 | SAFE-05…SAFE-07, SAFE-09, SAFE-11 |
| Yasak bölge | UI/şema | Runtime uygulaması yok | P1 | SAFE-08 |
| Pico kimliği | Port/path | Handshake ve uyumluluk | P0 | PLAT-04 |
| Kamera kimliği | Index/path | Kalıcı seçim/hotplug | P0 | PLAT-05 |
| Offline saha | Launcher var | Temiz PC kanıtı yok | P0/P2 | PLAT-06, PLAT-07 |
| Kanıt | Çok sayıda rapor | Küratörlü fiziksel dossier yok | P2 | EVD-01…EVD-05 |
| Stale frame/state | Browser/live yolları parçalı | Tek producer ve freshness yok | P0 | PLAT-10 |
| Runtime readiness | Geniş self-test UI | Yanlış pozitif ready riski | P0 | PLAT-11 |
| Operational arm | Runtime mode endpoint’i | Preflight/yetki token’ı yok | P0 | SAFE-11 |

## 6. Mevcut kodda muhtemel odak dosyaları

Güvenlik ve komut:

- backend/app/services/tracking_loop.py
- backend/app/services/auto_tracker_service.py
- backend/app/services/decision_engine.py
- backend/app/services/safety_gate_service.py
- backend/app/services/serial_service.py
- backend/app/services/pico_service.py
- backend/app/services/motion_service.py
- backend/app/services/turret_service.py
- backend/app/api/decision.py
- backend/app/api/routes_safety.py
- backend/app/api/routes_serial.py

Perception ve görev:

- backend/app/services/vision_pipeline.py
- backend/app/services/inference_adapter_service.py
- backend/app/services/model_package_service.py
- backend/app/services/model_registry_service.py
- backend/app/services/kalman_tracker.py
- backend/app/services/color_classifier_service.py
- backend/app/services/mission_service.py
- config/runtime/vision_profile.active.yaml
- models/active/registry.json
- models/active/active_models.json
- backend/app/schemas/tracking.py
- backend/app/schemas/mission.py
- backend/app/schemas/decision.py

Cihaz/platform:

- backend/app/services/device_manager_service.py
- backend/app/services/camera_runtime_service.py
- backend/app/services/device_profile_service.py
- backend/app/services/release_service.py
- backend/app/services/log_service.py
- backend/app/services/self_test_service.py
- config/config.yaml
- config/device_profiles/default.yaml
- start_linux.sh
- start_windows.bat

Firmware:

- firmware/pico2/main.py
- firmware/pico2_telemetry_only/main.py
- eski_sistem_arayüz/pico_arduino/motor_control_v2_optimized/motor_control_v2_optimized.ino

Operatör:

- frontend/src/views/CockpitView.vue
- frontend/src/views/MissionModesView.vue
- frontend/src/views/SetupCenterView.vue
- frontend/src/components/cockpit/SafetyModeBanner.vue
- frontend/src/components/cockpit/DeviceManagerPanel.vue
- frontend/src/components/cockpit/EngagementPanel.vue
- frontend/src/stores/missionStore.ts
- frontend/src/stores/deviceRuntimeStore.ts

## 7. Stratejik sonuç

Mevcut UI ve dijital ikiz jüriyi etkilemek için yeterince güçlüdür. Bundan sonraki değer, görünümü büyütmekten değil, fiziksel gerçekliği UI’ya bağlamaktan gelir. Birincilik için proje “demo/evidence platformu” olmaktan çıkıp ölçülmüş güvenlik, tekrar edilebilir saha görevi ve açıklanabilir karar sistemi haline gelmelidir.
