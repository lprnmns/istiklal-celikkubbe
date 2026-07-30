# 14 — Onay Sonrası İlk 72 Saat

Bu belge uygulama emri değildir. Kullanıcı planı onayladıktan sonra yürütülecek ilk üç günü tarif eder. Onaya kadar kaynak kod, firmware ve fiziksel sistem değiştirilmez.

## 1. İlk 72 saatin tek amacı

Yeni özellik yazmak değil, şu dört gerçeği kilitlemek:

1. Hangi sürüm gerçekten çalışıyor?
2. Gerçek sistem nasıl kablolanmış ve hangi firmware’i kullanıyor?
3. E-Stop hareket ve tetik enerjisini gerçekten kesiyor mu?
4. Hangi güvenli mimari üzerinden sonraki değişiklikler yapılacak?

72 saat sonunda auto-fire daha “akıllı” olmak zorunda değildir; fakat sistemin baseline’ı, pin/power gerçeği, riskleri ve uygulama dalı tartışmasız olmalıdır.

## 2. Başlamadan gerekli erişimler

- Takım lideri ve güvenlik sorumlusu.
- Fiziksel sistem, Pico, E-Stop ve güç şeması.
- Aktif çekim bilgisayarı.
- Güvenli test alanı/backstop.
- Mevcut CO₂/tetik düzeneği; ilk iki gün gerçek atış varsayılan değildir.
- ÖTR/KTR puanları ve KYS/resmî duyuru erişimi.
- Model dosyası/veri seti varsa salt-okunur kopya.

## 3. Saat 0–4 — Kickoff ve koruma

Görevler:

- GOV-01 rol ataması.
- GOV-02 ilk kaynak/puan kaydı.
- Mevcut kirli çalışma ağacının status/diff/hash envanteri.
- Fiziksel test durdurma yetkisinin açıklanması.
- Video P0 panosu.

Çıktılar:

- İsimlendirilmiş sahiplik.
- Günlük 10:00/akşam gate saati.
- Değişiklik yasağı: baseline bitene kadar ana fiziksel yol refactor edilmez.
- Tetik/servo enerjisi kapalı çalışma etiketi.

Kabul:

- Her P0 işin sahibi ve yedeği var.
- Hiçbir kullanıcı dosyası temizlenmedi.

## 4. Saat 4–12 — Golden baseline keşfi

Paralel akış A — Platform:

- Çalıştırma giriş noktalarını ve dependency sürümlerini kaydet.
- Disk/artefact envanteri.
- Kamera ve Pico kimliklerini kaydet.
- Golden OS adayını belirle.

Paralel akış B — Yazılım:

- Tracking → serial → firmware gerçek çağrı zincirini tek sayfaya çıkar.
- Gateway dışı write noktalarını listele.
- full_active, DRY_RUN ve readiness geçişlerini çıkar.
- Active vision profile/model/surrogate gerçeğini kaydet.

Paralel akış C — Fiziksel:

- Sistem enerjisizken fotoğraflı kablo/pin audit.
- Ebat ölçümü.
- Motor ve tetik güç yollarını ayır.
- E-Stop kontaklarının hangi hatları kestiğini ölçüm planına bağla.

Çıktılar:

- GOV-03 taslak manifest.
- SAFE-01 taslak as-built.
- OPS-01 ölçüm.
- Kritik kod yolları listesi.

Kabul:

- Aktif firmware ve pinout için kanıt vardır veya “belirsiz—enerji verme” kararı açıkça alınmıştır.

## 5. Saat 12–24 — Baseline tekrarı ve ölçüm

Önce:

- DRY_RUN.
- Tetik/servo enerjisi fiziksel kapalı.
- Kamera/Pico health.
- Pan/tilt düşük hızlı yön semantiği.

Sonra güvenlik sahibi izin verirse:

- Mevcut balon takip davranışını kontrollü tekrar.
- En az 10 run; gerçek atış zorunlu değil, hareket/aim replay ve geçmiş fiziksel video birlikte baseline olabilir.
- Config/model/firmware/device hash.

Bu blokta:

- Release tam testi çalıştırılmaz; önce PLAT-02.
- Büyük export/log temizliği yapılmaz.
- Yeni model ana profile alınmaz.

Gün 1 çıkışı:

- G1 GO veya açık blocker.
- Golden manifest v1.
- As-built v1.
- İlk risk panosu.

## 6. Saat 24–36 — Firmware ve E-Stop truth

Firmware ekibi:

- Arduino ve MicroPython seçeneklerini SAFE-02 kriteriyle karşılaştırır.
- PING/handshake, ACK, E-Stop, limit/home, watchdog farklarını kaydeder.
- Tek kanonik firmware önerisi ve migration riski çıkarır.

Donanım/güvenlik:

- Enerjisiz süreklilik.
- Kontrollü düşük gerilim/uygun ölçüm.
- Motor ve tetik/servo E-Stop kesme yolunu doğrular.
- Eksik fiziksel interlock varsa tasarım düzeltme kararı.

Backend:

- SafetyDecision ve CommandGateway API sözleşmesini yazar.
- Operational mode/full_active yetki akışını tasarlar.

Çıktılar:

- Kanonik firmware kararı.
- Pin profile hash sözleşmesi.
- E-Stop elektriksel test sonucu veya açık NO-GO.
- CommandGateway tasarım kaydı.

## 7. Saat 36–48 — Güvenli uygulama iskeleti

Yalnız G1 ve güvenlik tasarımı onaylıysa:

- SAFE-05 için yeni gateway iskeleti ve unit testleri.
- SAFE-06 karar token/snapshot/reason code sözleşmesi.
- SAFE-07 direct-write static check.
- SAFE-11 full_active preflight token tasarımı.
- PLAT-10 frame freshness/state bus tasarımı.

Varsayılan:

- Fiziksel TX kapalı.
- DRY_RUN true.
- Tetik enerjisi kapalı.

Kabul:

- Bir API/tracker çağrısının fiziksel write’a doğrudan ulaşamadığı testle gösterilir.
- Henüz canlı atış yapılmaz.

## 8. Saat 48–60 — HIL ve fault injection

Tetik enerjisi kapalı:

- Pico handshake/protokol.
- ACK timeout.
- Kamera çıkar/tak.
- Browser/son frame stale.
- E-Stop latch/reset.
- Queue flush.
- Host crash/restart.
- Yanlış firmware/device.
- DRY_RUN ve yetkisiz full_active.

Kabul:

- Bütün fault’lar safe stop/NO_FIRE.
- Stale/duplicate physical command sıfır.
- Readiness yanlış pozitif değil.

Başarısızlık:

- Canlı test planı ertelenir; hata P0 olarak kalır.

## 9. Saat 60–72 — İlk karar kapısı ve sonraki dört gün

Toplantı:

- G1 ve G2A durumu.
- Y1–Y5 için kalan en büyük bloklayıcı.
- Golden OS kararı için eksikler.
- 15 m saha tarihi ve ekipmanı.
- Y6 ilk tahmini: muhtemel GO/NO-GO.

72 saat teslimleri:

- Golden baseline manifest v1.
- As-built pin/power v1.
- Ebat sonucu.
- CO₂/atış bütçesi test planı.
- Kanonik firmware kararı.
- SafetyDecision/CommandGateway tasarımı.
- Risk panosu.
- 18–24 Temmuz görev sahipleri.

Sonraki dört gün önerisi:

1. SAFE-02…SAFE-09 ve SAFE-11 implementasyon ve bench.
2. SAFE-03/SAFE-04 fiziksel acceptance.
3. PLAT-04/05 cihaz kimliği.
4. PLAT-10 stale-frame kapanışı.
5. Y2/Y5 için ölçüm/kalibrasyon saha hazırlığı.

## 10. İlk 72 saatte yapılmayacaklar

- Yeni dijital ikiz/UI parlatma.
- Y6 modelini video dalına merge etme.
- Aşama 3 canlı ateş.
- Geniş Windows/Docker dönüşümü.
- Baseline alınmadan 54 GB export veya logların plansız silinmesi.
- Release recursive-copy düzelmeden tam release testleri.
- E-Stop elektriksel kabulü olmadan gerçek tetik.
- Kullanıcı onayı dışında repo temizleme/reset.

## 11. 72 saat başarı tanımı

Başarılı:

- Sistem hakkında daha fazla varsayım değil, daha az belirsizlik vardır.
- Çalışan sürüm geri döndürülebilir.
- Donanım ve firmware gerçeği eşleşir.
- Canlı komut yolu için güvenli tasarım ve test iskeleti vardır.
- Video takvimi kanıta göre güncellenmiştir.

Başarısız:

- Yeni ekran/özellik üretilmiş ama aktif firmware, E-Stop veya gerçek komut yolu hâlâ belirsizdir.
