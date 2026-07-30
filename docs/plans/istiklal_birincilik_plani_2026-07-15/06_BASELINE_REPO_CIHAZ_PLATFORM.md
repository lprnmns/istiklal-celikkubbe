# 06 — Baseline, Repo, Cihaz ve Platform Planı

## 1. Golden baseline

Golden baseline yalnız commit değildir. Aşağıdakilerin birlikte hash’lenmiş manifestidir:

- Git commit ve kirli diff özeti.
- Backend/frontend dependency lock.
- Config ve device profile.
- Firmware dosyası/build hash’i.
- Model/threshold/class mapping.
- Kamera ve Pico fiziksel kimliği.
- İşletim sistemi, sürücü ve GPU bilgisi.
- Launcher komutu.
- Kalibrasyon.
- Son 10 fiziksel/replay run sonucu.

Baseline etiketi ancak kamera/Pico health, iki balon davranışı ve güvenli kapatma tekrar edilebildiğinde verilir.

## 2. Kirli çalışma ağacı politikası

Mevcut değişiklikler kullanıcıya aittir:

- Otomatik reset/checkout/clean yapılmaz.
- Plan kapsamındaki değişiklikler ayrı branch veya açık commit grubunda tutulur.
- Çakışan dosyada önce mevcut diff incelenir.
- Baseline için çalışma ağacının patch’i ayrıca hash’lenir.
- Büyük artefact temizliği ayrı onaylı görevdir.

## 3. Depo boyutu ve retention

Mevcut:

- Toplam yaklaşık 70 GB.
- exports/release yaklaşık 54 GB.
- logs/backend.jsonl yaklaşık 8,7 GB.
- backend/.venv yaklaşık 5,4 GB.

Hedef:

- Kaynak, dependency cache, model, veri seti, release ve runtime çıktısı ayrı sınıflansın.
- Log rotation boyut + gün sınırıyla çalışsın.
- Video/inference/replay retention ayarlı olsun.
- Release çıktısı kendi kaynak ağacına yeniden dahil edilmesin.
- Testler temp dizin ve maksimum paket bütçesi kullansın.
- Model dahil/hariç gerçek paket boyutu raporlansın.

Silme sırası:

1. Envanter ve hash.
2. Aktif/arşiv/silinebilir sınıflaması.
3. Baseline tekrar testi.
4. Yalnız açıkça üretilebilir artefact temizliği.
5. Tekrar baseline testi.

## 4. Release testindeki ENOSPC riski

Release testinin çıktı paketini yeniden girdiye alarak sınırsız büyüme olasılığı vardır. PLAT-02:

- export kökünü kaynak taramasından hariç tutar.
- Paket staging’i depo dışında temp dizinde yapar.
- Maksimum dosya/adet/boyut bütçesi koyar.
- Aynı output path’in input altında olmasını reddeder.
- Test sonunda temp artefact cleanup yapar.
- Disk boşluğu yetersizse başlamadan açık hata verir.

Bu düzeltme olmadan tam release test paketi tekrar çalıştırılmaz.

## 5. Pico kalıcı kimliği

Handshake en az şunları döndürür:

- device_type.
- hardware_id / board UID.
- firmware_semver.
- protocol_version.
- pin_profile_hash.
- capabilities.
- boot/reset reason.
- E-Stop/arm/limit state.

Test matrisi:

1. Pico yok.
2. Farklı USB portu.
3. tty/COM adı değişmiş.
4. Birden fazla serial cihaz.
5. Yanlış firmware.
6. Çalışırken çıkarma.
7. Farklı porta geri takma.
8. ACK timeout.

Reconnect sonrası otomatik arm veya stale komut yoktur.

## 6. Kamera kalıcı kimliği

Kimlik için platforma göre VID/PID/serial/device path veya Wizard profili kullanılır. Kamera index tek başına kimlik değildir.

Test matrisi:

1. Kamera yok.
2. Dahili kamera + ELP.
3. Farklı USB portu/index.
4. Çalışırken çıkarma.
5. Geri takma ve format/FPS doğrulama.
6. Düşük FPS/stale frame.
7. Yanlış çözünürlük/pixel format.

Kamera kopunca eski kareyle tracking veya ateş yoktur.

## 6A. Tek producer ve stale-state kuralı

- Kamera karelerini tek servis üretir.
- Tek inference worker gerçek model/surrogate durumunu açıkça raporlar.
- REST/WebSocket/UI tüketicileri tekrar inference çalıştırmaz.
- Her frame, detection ve track monotonic timestamp/freshness taşır.
- Browser’dan gelen son olay tarayıcı kapandıktan sonra canlı kabul edilmez.
- Stale state hareket ve fire için fail-closed olur.

## 7. Golden işletim sistemi kararı

### Varsayılan

Mevcut çalışan sistem Linux ise video için Linux golden rig dondurulur.

### Windows yalnız şu durumda kritik yola girer

- Çekim/final bilgisayarının Windows olması zorunlu.
- Kamera ve Pico host erişimi kanıtlanabilir.
- RTX 4060 inference gerçekten GPU’da çalışır.
- Temiz yeniden başlatmadan Quick Preflight beş dakika altında.
- İnternet olmadan uygulama açılır.

Bu kapı 27 Temmuz’a kadar geçmezse video Linux rig ile çekilir. Windows geliştirmesi video sonrasına alınır.

## 8. Offline launcher ve Quick Preflight

Tek launcher:

1. Disk alanı ve saat kontrolü.
2. Config şema/hash.
3. Firmware/Pico handshake.
4. Kamera preview/format/FPS.
5. E-Stop ve fiziksel arm.
6. Model/GPU.
7. Yasak bölge ve calibration profile.
8. Log/evidence dizini.
9. DRY_RUN smoke.
10. Operatör onaylı görev geçişi.

overall_ready tek kaba boolean olarak kullanılmaz. En az system_ready, motion_ready ve fire_ready ayrılır; hardware disabled/warning/stale/incompatible durumda fire_ready false kalır.

Başarısız adım:

- Neden.
- Çözüm eylemi.
- Correlation ID.
- Bloklayıcı/uyarı sınıfı.

Teknisyen terminal veya kaynak dosya düzenlemeden ilerleyebilmelidir.

## 9. GPU ve inference

- Cihaz hard-code CPU olmamalı.
- Seçim auto/cuda/cpu profiliyle yapılmalı.
- Runtime gerçek seçilen cihazı raporlamalı.
- Model yükleme, warm-up, FPS, p50/p95 latency ve VRAM ölçülmeli.
- GPU yoksa görev profiline göre fail-closed veya açıkça düşük performans modu.
- Model benchmark’ı yalnız sentetik adapter değil gerçek ağırlık ve gerçek sınıf çıktısıyla yapılmalı.

## 10. Test hatları

| Hat | Ne zaman | Fiziksel çıktı |
|---|---|---|
| Unit/static | Her değişiklik | Yok |
| Replay/dry-run | Her değişiklik | Yok |
| HIL telemetry | Güvenlik değişikliği | Tetik enerjisi kapalı |
| Motion acceptance | Kontrollü | Hareket var, tetik kapalı |
| Fire acceptance | Yetkili saha | Sınırlı gerçek atış |
| Release/cleanroom | Gate öncesi | Cihazlar güvenli |

Backend tam testleri:

- Hızlı unit lane.
- Hardware-mock lane.
- Release/package lane.
- Fiziksel acceptance lane.

Release lane disk bütçeli ve bounded hale gelmeden genel test komutuna dahil edilmez.

Kritik testler string/yorum varlığına değil davranışa dayanır. Safety, mission ve vision için negatif contract testleri; operatör kritik frontend bileşenleri için component testleri eklenir.

## 11. Operasyonel bitiş ölçütleri

- Uygulamayı geliştirmemiş ekip üyesi çalıştırabilir.
- Kod/config değiştirmeden kamera/Pico port değişimi geçer.
- Güçten yazılım Quick Preflight’a beş dakika altında ulaşılır.
- Tam yarışma kurulumu 30 dakika altında en az üç kez prova edilir.
- 30 dakikalık soak testinde disk/memory kontrolsüz büyümez.
- Sistem kapanış, crash, disconnect ve E-Stop’ta güvenli kalır.
- Tanı paketi tek komut/ekran eylemiyle üretilir.
