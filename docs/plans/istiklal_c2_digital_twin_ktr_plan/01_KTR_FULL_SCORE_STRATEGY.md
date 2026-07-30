# 01 — KTR Tam Puan Stratejisi: Mekanik + Elektronik + Yazılım + Digital Twin

## Temel tez

İSTİKLAL C2 yalnızca balon/hedef takip eden mekanik bir düzenek olarak sunulmamalı. KTR’de sistem şu şekilde konumlandırılmalı:

> Görüntü işleme, hedef takip, mekanik yönelim, Pico/aktüatör telemetrisi, güvenlik kapıları, olay kaydı ve 3D operasyonel dijital ikiz kokpitinden oluşan bütünleşik, kanıt üreten bir hava savunma kontrol sistemi.

Bu tez, mekanik/elektronik/yazılım bölümlerini birbirinden kopuk göstermemek için kritik.

## KTR puan alanlarına göre yaklaşım

| KTR bölümü | Beklenen şey | Bizim + değerimiz | Üretilecek kanıt |
|---|---|---|---|
| 3. Mevcut Durum | Ön tasarımdan sonra ne değişti | Balon takip çalışan sistem + real camera/Pico acceptance + digital twin dönüşüm planı | faz raporları, screenshot, run log |
| 4.1 Mekanik Tasarım | Malzeme, üretim, fiziksel özellik, final tasarım gerekçesi | CAD tabanlı pan/tilt mekanizma, 3B baskı iterasyonları, servis edilebilirlik, dijital ikizde eksen doğrulama | CAD görselleri, 3D model node mapping, mekanik risk tablosu |
| 4.2 Elektronik/Yazılım | Elektronik süreç, algoritma, UI, atış kontrol | Kamera + YOLO + tracker + Pico + TMC/servo + telemetry bus + digital twin state contract | blok şema, interface contract, sequence diagram |
| 4.3 Arayüzler | UI dışı arayüzler dahil mesajlaşma | Operasyonel dijital ikiz, kamera/serial/backend/frontend/Pico arayüzleri | message contract, websocket/rest diyagramı |
| 4.4 Senaryolar | Use case, mod, state, hata, diyagram | Detection→Tracking→Aiming→Engagement→Replay state machine | activity/sequence/state diyagramları |
| 5 Test | Test senaryoları ve sonuç | camera acceptance, Pico RX, tracker replay, digital twin replay, latency, clean-room | test matrix, evidence JSON, screenshots |
| 6 Güvenlik | Güvenlik önlemleri, acil stop | fire gate, E-stop, hardware enable, command authority boundary, no-command simulation | safety boundary, fail-safe state table |
| 7 Tecrübe | Hatalar ve çözümler | camera device selection, Pico permission, legacy migration, direction calibration | tecrübe logları |
| 8 Zaman/Bütçe/Risk | Plan ve risk | model training risk, mekanik backlash, camera calibration, serial latency | risk register |
| 9 Özgünlük | Alt sistemlerde özgünlük | telemetry-driven digital twin, replay evidence, dynamic calibration, class-agnostic target asset layer | özgünlük matrisi |
| 10 Kaynakça | Kullanılan kaynaklar | Three.js/R3F/Blender/glTF, kamera, Pico, TMC2209 kaynakları | kaynakça listesi |

## KTR'de asıl fark yaratacak 5 iddia

### 1. Operasyonel dijital ikiz

Sistem, yalnızca kamera görüntüsü göstermez; cihazın mekanik yönelimini, hedef izleme durumunu, güvenlik kilitlerini ve angajman olaylarını 3D dijital ikiz üzerinde anlık gösterir.

Dürüst sınır:

- Bu bir “gerçek fizik dünyasının kusursuz simülasyonu” değildir.
- Görüntü işleme ve telemetri kaynaklı yaklaşık bir operasyonel temsil sağlar.
- Hedefin 3D konumu “approximate” olarak işaretlenir.

### 2. Evidence-first yarışma kokpiti

Her tespit, takip, hedef kaybı, angajman ve hata olayı zaman damgalı kaydedilir. Bu sayede hakemler için sadece iddia değil, tekrar oynatılabilir kanıt üretilir.

### 3. Class-agnostic target layer

Bugün balon modeliyle çalışan pipeline, yarın 4 yarışma hedef sınıfı YOLO modeliyle çalışabilecek şekilde `class_id`, `class_label`, `confidence`, `bbox`, `asset_model_path` ayrımıyla tasarlanır.

### 4. Güvenlik sınırı yazılım mimarisinde görünür

Digital twin komut sahibi değildir. Motor/servo/fire komutu üretmez. Sadece state render eder. Komut yetkisi, güvenlik kapıları ve emergency stop ayrı tutulur.

### 5. Mekanik tasarım yazılımla doğrulanır

Pan/tilt eksenleri, kamera bakış yönü, motor yön kalibrasyonu ve limitler dijital ikiz üzerinde doğrulanır. Böylece mekanik tasarım sadece çizim olarak değil, davranışsal olarak da raporlanır.

## Bölüm bazlı yazım notları

### 4.1 Mekanik Tasarım

Sadece “3D baskı aldık” demek zayıf olur. Şunlar yazılmalı:

- Neden pan/tilt mimarisi seçildi?
- Gövde neden modüler?
- Kamera ve namlu ekseni nasıl hizalandı?
- X/Y ekseni tersliği nasıl kalibre edildi?
- Tetik/servo mekanizması nasıl izole edildi?
- Kablo geçişi ve servis erişimi nasıl çözüldü?
- Mekanik tasarımın dijital ikiz için nasıl node/eksen yapısına ayrıldığı.

Özgün + kısım:

> Mekanik CAD modeli yalnızca üretim amacıyla değil, arayüzdeki dijital ikiz temsilinin kaynağı olarak da kullanılmıştır. Böylece mekanik tasarım, yazılım arayüzünde canlı telemetriyle ilişkilendirilmiştir.

### 4.2 Elektronik + Algoritma + Yazılım

Alt başlık önerisi:

- Kamera ve görüntü işleme hattı
- YOLO sınıflandırma ve hedef seçimi
- Takip kontrol algoritması
- Pico/serial haberleşme
- Motor/servo sürme mimarisi
- Digital twin state adapter
- Event log ve replay altyapısı

Özgün + kısım:

> Atış kontrol yazılımı yalnızca anlık komut üretmez; aynı zamanda her kararın hangi görüntü, hedef, güvenlik ve telemetri durumu altında verildiğini kaydederek geriye dönük doğrulanabilirlik sağlar.

### 4.3 Arayüzler

Bu bölümde UI screenshot tek başına yetmez. Şunlar mutlaka olmalı:

- Kamera arayüzü
- YOLO/tracker mesaj arayüzü
- Backend/frontend arayüzü
- Pico/serial telemetry arayüzü
- Digital twin state contract
- Operatör arayüzü
- Rapor/evidence export arayüzü

Özgün + kısım:

> Operatör arayüzü, kamera POV’u ile 3B dijital ikizi aynı anda göstererek hem algılayıcı merkezli hem mekanik merkezli durum farkındalığı sağlar.

### 4.4 Sistem Senaryoları

Use case listesi:

1. Sistem başlatma ve self-test
2. Kamera seçimi ve hedef algılama
3. Hedef takibe alma
4. Mekanik yönelim ve center alignment
5. Güvenlik kapılarıyla angajman izni
6. Angajman sonrası hedef kaybı/imha adayı değerlendirme
7. Hata durumunda fire block/E-stop
8. Replay ile olay inceleme

### 5 Test

Testler sadece “çalıştı” değil, ölçülebilir olmalı:

- Kamera device selection test
- USB camera frame capture test
- Pico port discovery test
- Direction calibration simulator test
- Tracker replay regression test
- Digital twin fixture render test
- Event replay determinism test
- Safety gate negative test
- UI fallback test
- Latency budget test

### 6 Güvenlik

Mutlaka yazılacaklar:

- Acil stop kabiliyeti
- Fire gate
- Hardware enable gate
- Manual/autonomous mode ayrımı
- Command authority ayrımı
- Digital twin read-only sınırı
- Komut kuyruğu ve pending ACK izleme
- Hata halinde default safe state

### 9 Özgünlük

Takım ismi veya “tasarımı biz yaptık” gibi şeyler özgünlükte zayıf kalır. Şunları yaz:

- Gerçek zamanlı operasyonel dijital ikiz
- Replayable engagement evidence
- Class-agnostic target asset layer
- Calibration direction simulator
- Safety-state-aware cockpit
- KTR export/evidence automation
- Clean-room package verification

## Rapor dili

KTR’de aşırı iddialı ve savunulamaz cümlelerden kaçın:

Yanlış:
- “Hedefin gerçek 3D konumu tam olarak bulunur.”
- “Sistem tamamen otonom imha garantisi verir.”
- “Dijital ikiz gerçek dünyayı birebir simüle eder.”

Doğru:
- “Hedefin kamera görüntüsü ve telemetriye dayalı yaklaşık operasyonel temsili üretilir.”
- “Angajman kararı güvenlik kapıları ve hedef takip durumu ile sınırlandırılır.”
- “Dijital ikiz, gerçek zamanlı telemetriye bağlı karar destek ve gözlem katmanıdır.”
