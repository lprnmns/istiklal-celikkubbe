# Live Akış Geçişi Güvenlik ve Yasaklar Raporu

Tarih: 2026-06-03

## Amaç

Bu raporun amacı, mevcut `teknofest` reposunda yanlışlıkla veya yetkisiz şekilde fiziksel komut üretilebilecek yüzeyleri belgelemek, mevcut çelişkileri görünür kılmak ve çalışanlara verilecek "yapılmayacaklar / yasaklar" listesini netleştirmektir.

Bu belge, fiziksel komutların nasıl açılacağını anlatmaz. Tersine, tamamen live akışa geçmeden önce hangi mimari, operasyonel ve güvenlik şartlarının **zorunlu** olduğunu ve mevcut repo ile neden doğrudan live kullanıma gidilmemesi gerektiğini açıklar.

## Kapsam

İncelenen ana yüzeyler:

- Ana çalışma konfigürasyonu
- Runtime setup wizard profili
- Seri haberleşme ve fiziksel komut servisleri
- Tracking loop
- Hardware test endpointleri
- Safety mode endpointleri
- Motion servisindeki dry-run kilitleri
- Setup Wizard güvenli/dry-run API davranışları
- Test setinin varsaydığı güvenlik modeli

## Yönetici Özeti

Mevcut repo, live kullanım açısından **içsel olarak tutarsız** durumdadır.

Bir tarafta:

- `config/config.yaml` ve `config/runtime/setup_wizard_profile.json` içinde fiziksel komutlara izin veren açık ayarlar vardır.
- `backend/app/services/serial_service.py`, `backend/app/services/tracking_loop.py`, `backend/app/api/hardware.py`, `backend/app/api/routes_motor.py` içinde fiziksel seri yazımı, motor hareketi ve tetik/servo hattına gidebilecek kod yüzeyleri mevcuttur.

Diğer tarafta:

- `backend/app/api/setup.py` hâlâ tüm Setup Wizard akışını dry-run/safe-only varsaymaktadır.
- `backend/app/services/motion_service.py` hâlâ fiziksel hareketi reddeden eski dry-run mantığını taşımaktadır.
- Çok sayıda test ve rapor dosyası sistemin `no_physical_command_generated=true` olduğu varsayımıyla yazılmıştır.

Sonuç:

**Bu repo şu haliyle "yanlışlıkla kimse açamaz" denebilecek güvenli bir live mimariye sahip değildir.**

## Mevcut Durum Bulguları

### 1. Ana konfigürasyon live davranışa açık

Dosya: `config/config.yaml`

Öne çıkan alanlar:

- `system.mode: "ARMED"`
- `system.default_fire_policy: "FIRE"`
- `system.dry_run: false`
- `system.hardware_enabled: true`
- `hardware.physical_command_enabled: true`
- `hardware.allow_physical_motion: true`
- `hardware.allow_physical_fire: true`
- `serial.real_serial_enabled: true`
- `serial.serial_tx_enabled: true`
- `motion.dry_run: false`
- `motion.real_motion_enabled: true`
- `runtime_mode.mode: "production"`

Not:

- Aynı dosyada `serial.transport_mode: "mock"` görülmektedir. Bu, ayarların bir kısmının live, bir kısmının mock olduğunu gösterir. Bu tür hibrit durumlar tehlikelidir; çünkü ekip "nasıl olsa mock" diye düşünebilirken başka bir yüzey fiilen fiziksel komut yazabiliyor olabilir.

### 2. Runtime setup wizard profili de açık

Dosya: `config/runtime/setup_wizard_profile.json`

Öne çıkan alanlar:

- `physical_command_enabled: true`
- `serial_tx_enabled: true`
- `no_physical_command_generated: false`

Bu profil, setup tarafında "kilitler açık" mesajı verirken backend setup endpointleri hâlâ safe-only davranmaktadır. Bu da operatör/çalışan açısından yanlış güven algısı üretir.

### 3. Gerçek seri yazımı ve fiziksel komut yüzeyi mevcut

Dosya: `backend/app/services/serial_service.py`

Önemli yüzeyler:

- `send_speed_command(...)`
- `send_motor_command(...)`
- `send_fire_command(...)`

Bu servis:

- `SPD,...` motor hız komutu üretebilir
- `DRV,1`, `DRV,0`, `STP`, `HOM` gibi motor komutları üretebilir
- `LZR,1`, `LZR,0` ile tetik/laser/servo benzeri ateş komutu üretebilir

Özellikle `send_fire_command(...)` fonksiyonu, `allow_physical_fire=true` olduğunda fiziksel çıkış yoluna giden net bir risk yüzeyidir.

### 4. Tracking loop fiziksel zincire bağlanabiliyor

Dosya: `backend/app/services/tracking_loop.py`

Önemli noktalar:

- Başlangıçta `DRV,1` gönderebilir
- Döngü içinde `send_speed_command(...)` ile motorlara hız komutu yazabilir
- Hedef merkez hizalama koşulu sağlandığında `send_fire_command(1)` ve sonra `send_fire_command(0)` çağırabilir

Bu dosya, otomatik takip ve fiziksel tetikleme davranışının aynı zincirde bulunabildiğini gösterir. Bu repo içinde böyle bir zincirin bulunması bile, ayrı güvenlik katmanları kurulmadan live kullanım için kabul edilemez.

### 5. Hardware test endpointleri doğrudan riskli

Dosya: `backend/app/api/hardware.py`

Riskli endpointler:

- `/api/hardware/test-trigger`
- `/api/hardware/test-servo-tune`
- `/api/hardware/test-jog`

Bu endpointler:

- doğrudan tetik/servo komutu oluşturabilir
- doğrudan motor jog komutu yazabilir
- otomatik olmayan ama fiziksel test davranışı başlatabilir

### 6. Motor route yüzeyi dry-run dışında kalmış

Dosya: `backend/app/api/routes_motor.py`

Riskli endpointler:

- `/api/motor/driver/enable`
- `/api/motor/driver/disable`

`/api/motor/jog` 403 ile bloklanırken aynı route dosyasında `driver/enable` ve `driver/disable` açık tutulmuş. Bu, güvenlik modelinin tutarsız olduğuna işaret eder.

### 7. Safety mode route fiziksel yetki açabiliyor

Dosya: `backend/app/api/routes_safety.py`

`/api/safety/set-operational-mode` endpointi:

- `no_motion`
- `motion_no_fire`
- `full_active`

modlarını ayarlayabiliyor. `full_active` seçeneği:

- tracking’i aktif ediyor
- gerçek motion’u aktif ediyor
- `allow_physical_motion=true`
- `allow_physical_fire=true`
- `system.dry_run=false`

yapabiliyor.

Bu tür bir geçiş, ayrı build, ayrı kimlik doğrulama, ayrı onay mekanizması ve ayrı release prosedürü olmadan ana backend içinde durmamalıdır.

### 8. Motion service hâlâ eski dry-run varsayımında

Dosya: `backend/app/services/motion_service.py`

Burada `real_motion_disabled_by_phase7` gerekçesiyle fiziksel hareket reddedilmektedir. Yani:

- config live diyor
- serial/hardware route fiziksel komut üretebiliyor
- motion service ise hâlâ fiziksel hareketi yasaklıyor

Bu, sistemin tek bir operasyonel doğrusu olmadığını gösterir.

### 9. Setup Wizard API güvenli, runtime profil değil

Dosya: `backend/app/api/setup.py`

`_safe_flags()` fonksiyonu her yerde:

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

döndürür.

Ayrıca:

- `/api/setup/pico/connect`
- `/api/setup/pico/heartbeat`
- `/api/setup/pico/ack-test`
- `/api/setup/motor/test`
- `/api/setup/actuator/safe-test`

tamamı dry-run mantığında çalışır.

Bu yüzden setup wizard profili açık olsa bile wizard davranışı güvenlidir. Bu da ikinci bir tutarsızlıktır.

### 10. Test seti hâlâ safe-only repo varsayıyor

Dosyalar:

- `backend/tests/conftest.py`
- `backend/tests/test_config.py`
- çok sayıda phase testi

Test seti geniş ölçüde şu varsayımla yazılmıştır:

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

Yani repo hem live sinyalleri taşıyor hem de kendi test mirası bunu halen güvenli demo/release sistemi gibi kabul ediyor.

## Kritik Çelişkiler

Bu repo içindeki en tehlikeli durum, tek bir "çalışma gerçeği" olmamasıdır.

### Çelişki 1

- Ana config live açık
- Setup Wizard davranışı safe-only

### Çelişki 2

- Tracking loop fiziksel motor ve tetik çağırabiliyor
- Motion service hâlâ dry-run reject ediyor

### Çelişki 3

- Safety route `full_active` açabiliyor
- Test ve rapor mirası sistemi no-physical-command diye kabul ediyor

### Çelişki 4

- Serial config `serial_tx_enabled=true`
- Aynı anda `transport_mode=mock`

### Çelişki 5

- Operatör/mühendis UI tarafında bazı yerler hâlâ preview/dry-run dili kullanıyor
- Arkadaki config/live endpoint yüzeyi daha ileri yetki taşıyor

Bu karışım, yanlışlıkla aktivasyon riskini artırır.

## Tamamen Live Akış İçin Asgari Gerekenler

Bu bölüm, nasıl açılacağını değil; live geçişin **hangi bağımsız şartlar sağlanmadan** yapılmaması gerektiğini tanımlar.

### 1. Ayrı dağıtım profili zorunlu

Aynı repo ve aynı varsayılan config ile hem:

- demo/release/sunum
- mühendis dry-run
- fiziksel live saha kullanımı

yönetilmemelidir.

Gerekli yaklaşım:

- live saha profili ayrı olmalı
- ayrı deployment paketi olmalı
- ayrı config kökü olmalı
- ayrı erişim yetkisi olmalı

### 2. Ayrı donanım güvenlik katmanı zorunlu

Yazılım tek başına güvenlik sınırı olmamalıdır.

Live kullanım için bağımsız olarak doğrulanmış şu katmanlar gerekir:

- bağımsız acil durdurma
- fiziksel driver enable hattı için ayrı interlock
- tetik/aktüatör hattı için bağımsız safety relay
- yazılım çökerse güvenli konuma dönen fail-safe davranış
- motion ve actuator için ayrı donanım kilidi

### 3. İki aşamalı yetkilendirme zorunlu

Tek tıkla veya tek config değişikliği ile live moda geçiş olmamalıdır.

Asgari olarak:

- ayrı rol yetkisi
- ayrı onay ekranı
- ikinci kişi onayı
- zaman damgalı audit kaydı

olmadan live yetki verilmemelidir.

### 4. Ayrı release ve denetim hattı zorunlu

Live saha yazılımı:

- operator UI build’i
- engineer UI build’i
- setup wizard
- backend route exposure

açısından imzalı ve denetlenmiş ayrı sürüm olmalıdır.

Demo veya geliştirme build’i ile live çalışma yasaklanmalıdır.

### 5. Operatör UI üzerinden tehlikeli yüzey kaldırılmalı

Operatör ekranı hiçbir durumda şunlara erişim vermemelidir:

- safety mode değişimi
- driver enable/disable
- jog
- trigger/servo test
- calibration sırasında fiziksel komut
- ham serial TX

### 6. Setup Wizard yalnızca hazırlık ve doğrulama aracı olmalı

Setup Wizard:

- cihaz seçme
- port teşhisi
- heartbeat
- ACK/telemetry okuma
- model doğrulama
- preview

için kullanılabilir.

Ancak live deployment öncesi bile wizard içinden fiziksel aktüasyon açılmamalıdır. Ayrı yetkili bakım aracı gerekir.

### 7. Uçtan uca audit log zorunlu

Şunların hepsi kayda alınmadan live akış kabul edilmemelidir:

- kim live moda geçti
- ne zaman geçti
- hangi config ile geçti
- hangi port seçiliydi
- hangi model aktifti
- hangi safety gate’ler açıktı
- hangi komut fiziksel hatta yazıldı
- hangi ACK alındı

### 8. Otomatik takip ve fiziksel aktüasyon aynı varsayılan zincirde bulunmamalı

Hedef algılama, takip, hizalanma ve fiziksel çıkış zinciri şu an aynı backend içinde bir araya gelebiliyor. Live kullanım için bu zincir:

- ayrı olarak incelenmeli
- ayrı güvenlik incelemesinden geçmeli
- varsayılan olarak kapalı olmalı
- açık olduğunda bağımsız olarak işaretlenmeli

## Çalışanlara Verilecek Yasaklar

Bu bölüm doğrudan operasyon/yazılım ekibine verilebilir.

### Yasak 1

Ana `config/config.yaml` veya `config/runtime/setup_wizard_profile.json` içindeki live bayraklar tek başına "çalıştırma izni" sayılmayacaktır.

### Yasak 2

`runtime_mode.mode=production` veya `field_live` yazıyor diye sistemin sahada güvenli olduğu varsayılmayacaktır.

### Yasak 3

Operator veya engineer arayüzünden görünen preview/dry-run metinleri, backend’in fiziksel komut üretmediğinin kanıtı sayılmayacaktır.

### Yasak 4

`/api/hardware/test-trigger`, `/api/hardware/test-servo-tune`, `/api/hardware/test-jog`, `/api/motor/driver/enable`, `/api/motor/driver/disable`, `/api/safety/set-operational-mode` gibi endpointler ana ortak geliştirme ortamında açık bırakılmayacaktır.

### Yasak 5

Tek kişi kararıyla live config değişikliği, live port eşlemesi veya fiziksel hareket/tetik testi yapılmayacaktır.

### Yasak 6

Demo/release için kullanılan build, yarışma/saha build’i yerine kullanılmayacaktır.

### Yasak 7

Mock, fixture, preview veya dry-run ile üretilmiş kanıtlar, fiziksel saha doğrulaması yerine sunulmayacaktır.

### Yasak 8

Test geçmişi `no_physical_command_generated=true` bekliyor diye sistemin bugün de o şekilde davrandığı varsayılmayacaktır; config ve runtime her seferinde ayrıca denetlenecektir.

### Yasak 9

Tracking loop ve fire zone mantığı içeren yazılım, bağımsız saha emniyet incelemesi olmadan live sistemde çalıştırılmayacaktır.

### Yasak 10

Tek repo / tek config / tek UI ile hem geliştirme, hem demo, hem live saha kullanımı yönetilmeyecektir.

## Mevcut Repo İçin Acil Düzeltme Başlıkları

Bu başlıklar enablement değil, yanlışlıkla aktivasyonu önleme amaçlıdır.

### A. Tehlikeli endpointlerin ayrılması

Şu yüzeyler ayrı, yetkili, audit edilen bir bakım/servis katmanına taşınmalıdır:

- `/api/hardware/test-trigger`
- `/api/hardware/test-servo-tune`
- `/api/hardware/test-jog`
- `/api/motor/driver/enable`
- `/api/motor/driver/disable`
- `/api/safety/set-operational-mode`

### B. Setup Wizard ile runtime profilinin uyumlu hale getirilmesi

Şu anda wizard API güvenli, ama profile JSON açık. Bu ikisi aynı şeyi söylemelidir. Aksi halde kullanıcı yanlış okur.

### C. Operatör arayüzünde live yetki algısını kaldırma

Operatör ekranında:

- preview / simulation / fixture / offline ayrımları net olmalı
- fiziksel komut yetkisi görünür şekilde ayrı işaretlenmeli
- ama tehlikeli buton ve rotalar operatöre hiç sunulmamalı

### D. Motion/Tracking/Hardware katmanlarının tek doğruda toplanması

Şu an motion service ve tracking loop aynı güvenlik modeline sahip değildir. Tek bir kaynak-of-truth zorunludur.

### E. Test setinin yeniden ayrıştırılması

Eski safe-only testleri ile yeni live niyetli config aynı repo içinde sessizce yaşamamalıdır.

Asgari ayrım:

- safe baseline testleri
- live-disabled integration testleri
- field candidate testleri

ayrı yürütülmelidir.

## Live Geçişe Hazırlık İçin Go / No-Go Ölçütleri

Bir ekip, aşağıdakilerin tamamı sağlanmadan "live akışa hazırız" diyemez:

1. Tekil ve tutarlı config davranışı
2. Operator UI’da tehlikeli yüzey yok
3. Setup Wizard ile runtime bayrakları uyumlu
4. Fiziksel komut route’ları ayrı erişim katmanında
5. Donanım interlock ve acil durdurma bağımsız doğrulanmış
6. Yetkilendirme ve audit log aktif
7. Production model, gerçek kamera ve donanım telemetrisi ayrı ayrı doğrulanmış
8. Dry-run, preview ve physical test modları karışmıyor
9. Back-end üzerinde fiziksel komut yazan her fonksiyon denetlenmiş
10. Saha dağıtımı demo/geliştirme dağıtımından ayrılmış

Bu maddelerden biri eksikse karar: **NO-GO**

## Sonuç

Bugünkü repo durumu:

- fiziksel komut üretebilecek kod yüzeyleri içeriyor
- bazı config’ler live açık
- bazı servisler ve wizard hâlâ safe-only davranıyor
- test mirası büyük ölçüde eski güvenli varsayıma dayanıyor

Bu nedenle mevcut yapı, "tamamen live akış" için hazır kabul edilmemelidir.

Bu repo önce:

- ayrıştırılmalı
- güvenlik katmanları netleştirilmeli
- tehlikeli endpointler taşınmalı
- operator/mühendis/demo/live sınırları kesinleştirilmeli

ondan sonra ancak ayrı bir saha dağıtım programı değerlendirilmelidir.

## Referans Dosyalar

- `config/config.yaml`
- `config/runtime/setup_wizard_profile.json`
- `backend/app/services/serial_service.py`
- `backend/app/services/tracking_loop.py`
- `backend/app/api/hardware.py`
- `backend/app/api/routes_motor.py`
- `backend/app/api/routes_safety.py`
- `backend/app/api/setup.py`
- `backend/app/services/motion_service.py`
- `backend/app/schemas/config.py`
- `backend/tests/conftest.py`
- `backend/tests/test_config.py`
