# İSTİKLAL — TEKNOFEST 2026 Birincilik Planı

Tarih: 15 Temmuz 2026  
Plan durumu: Kullanıcı onayı bekleniyor; uygulama başlamadı.  
Video son teslim: 10 Ağustos 2026, 17:00  
Depo tabanı: main-2 / 83cee632b12b34148c4f94cb1b37b74abf9dc2b6

## Sonuç cümlesi

İSTİKLAL’in birincilik yolu yeni ekranlar veya daha fazla demo özelliği üretmekten geçmiyor. Önce çalışan fiziksel çekirdek dondurulmalı, E-Stop ve bütün fiziksel komutlar tek ve denetlenebilir güvenlik zincirine alınmalı, Y1–Y5 videosu kusursuz geçilmeli; ardından Aşama 1 neredeyse garanti puana, Aşama 2 3/3 hedef güvenilirliğine ve Aşama 3 gerçek Body → IFF → Balloon Link → Range → Safety → Fire zincirine taşınmalıdır.

## Bu planın bağlayıcı ilkeleri

1. Video Y1–Y5, kalan en fazla 440 puanı açan eleme kapısıdır.
2. Fiziksel E-Stop hareket ve tetik/aktüatör enerjisini yazılımdan bağımsız kesmeden canlı atış yoktur.
3. Bütün hareket ve atış komutları tek CommandGateway üzerinden geçer; doğrudan serial/Pico çağrısı yasaktır.
4. DRY_RUN varsayılandır. Gerçek atış yalnız kısa ömürlü, görev bağlamlı arm ve fiziksel izinle mümkündür.
5. Aşama 2’de sınıflandırma değil çoklu iz, ilişkilendirme ve 3/3 bitirme önceliklidir.
6. Aşama 3’te balon rengi veya sabit kırmızı-düşman varsayımı kullanılmaz; gövde sınıfı, yapılandırılabilir IFF, doğru balon bağlantısı ve menzil birlikte doğrulanır.
7. “Kod derlendi”, “UI açıldı” veya “bir kez çalıştı” bitmiş sayılmaz. Her görev ölçülebilir kabul testi ve kanıtla kapanır.
8. Yeni UI/dijital ikiz geliştirmesi, zorunlu saha kapıları yeşil olana kadar dondurulur.
9. Kirli çalışma ağacındaki mevcut değişiklikler kullanıcı çalışmasıdır; korunur ve plansız temizlenmez.
10. Bu klasör onaylanana kadar proje kaynak kodunda uygulama değişikliği yapılmaz.

## Birincilik için çalışma hedefi

ÖTR ve KTR’den alınan gerçek sayısal puan bilinmiyor. Bu nedenle toplam hedef şu formülle yönetilir:

    Toplam = sabitlenmiş ÖTR+KTR puanı + gelecekte kazanılabilir puan

Gelecekte kazanılabilir en yüksek puan 440’tır: final sunumu 40, ebat 20, Aşama 1 100, Aşama 2 120, Aşama 3 160.

Birincilik çalışma hedefi:

| Kalem | Hedef |
|---|---:|
| Final sunumu | 36–40 |
| Ebat | 20 |
| Aşama 1 | 95–100 |
| Aşama 2 | 105–120 |
| Aşama 3 | 120–140 |
| Gelecekte kazanılabilir toplam | 376–420 / 440 |

Bu hedef, Aşama 3’te en az 10 puanlık ödül uygunluğu barajını yalnız geçmeyi değil, Aşama 2+3’te birincilik farkı oluşturmayı amaçlar.

## Belge haritası

Plan, 16 belgede toplam 69 kanonik görevi içerir. Her görevde öncelik, sahip rol, kişi-gün eforu, bağımlılık, muhtemel dosyalar, kabul kriteri, test/kanıt ve geri dönüş koşulu vardır.

| Dosya | Kullanım amacı |
|---|---|
| 00_KAYNAKLAR_VE_VARSAYIMLAR.md | Resmî gerçekler, kaynak hiyerarşisi, belirsizlikler |
| 01_BIRINCILIK_PUAN_STRATEJISI.md | Puan matematiği ve yatırım önceliği |
| 02_MEVCUT_DURUM_VE_GAP.md | Projenin doğrulanmış durumu ve kritik açıklar |
| 03_26_GUNLUK_KRITIK_YOL.md | Video teslimine kadar tarihli kritik yol |
| 04_VIDEO_Y1_Y5_PLANI.md | Video storyboard, kabul ve teslim kapısı |
| 05_FIRMWARE_ESTOP_COMMAND_GATEWAY.md | Güvenli fiziksel komut mimarisi |
| 06_BASELINE_REPO_CIHAZ_PLATFORM.md | Baseline, cihaz kimliği, OS, release ve disk |
| 07_FINAL_ASAMA1.md | Manuel görev ve 95+ puan planı |
| 08_FINAL_ASAMA2.md | Çoklu otonom takip ve 105–120 puan planı |
| 09_FINAL_ASAMA3.md | Dost/düşman, menzil ve 120+ puan planı |
| 10_MODEL_IFF_ASSOCIATION_RANGE.md | Algı çekirdeği ve doğrulama matrisi |
| 11_TEST_KANIT_JURI.md | Test piramidi, kanıt paketi ve 40 puanlık sunum |
| 12_GOREV_BACKLOG.md | Uygulanacak bütün görevlerin kanonik listesi |
| 13_RISK_VE_GO_NO_GO.md | Risk kaydı, durdurma ve ilerleme kapıları |
| 14_ONAY_SONRASI_ILK_72_SAAT.md | Onaydan sonraki ilk üç günün operasyon planı |

## Uygulama sırası

1. G0 — Plan onayı ve rol ataması.
2. G1 — Golden baseline, gerçek kablolama/pin sözleşmesi ve ebat ölçümü.
3. G2 — Fiziksel E-Stop, kanonik firmware ve tek CommandGateway.
4. G3 — Y1–Y5’in ayrı ayrı üç ardışık temiz provası.
5. G4 — Video feature freeze, tam kostümlü iki prova.
6. G5 — Çekim, kurgu, YouTube/KYS teslimi.
7. G6 — Aşama 1 tam görev kabulü.
8. G7 — Aşama 2 dört turluk kabulü.
9. G8 — Aşama 3 sekiz turluk kabulü ve sıfır dost vuruşu.
10. G9 — Final saha, bakım ve jüri provası.

Bir kapı kırmızıysa ona bağlı yeni özellik ana yarışma dalına alınmaz.

## Rol sözlüğü

| Rol | Ana sorumluluk |
|---|---|
| Takım Lideri / Program | Öncelik, kaynak, takvim, go/no-go |
| Güvenlik ve Donanım | E-Stop, güç, kablolama, mekanik limit, saha güvenliği |
| Firmware | Pico, pin sözleşmesi, watchdog, limit/home, telemetri |
| Kontrol ve Backend | SafetyDecision, CommandGateway, görev motorları, tracking |
| Görüntü İşleme / ML | Model, tracker, IFF, association, range |
| Frontend / Operatör UX | Gerçek durum gösterimi, manuel mod, preflight |
| Platform / Release | Cihaz keşfi, launcher, offline paket, disk ve log |
| Test / Kanıt | Acceptance, run ID, ölçüm, regresyon, evidence pack |
| Saha Operatörü | Kurulum, görev icrası, bakım ve tekrar edilebilirlik |
| Video / Sunum | Storyboard, çekim, kurgu, KYS ve jüri anlatısı |

Küçük ekipte bir kişi birden fazla rol alabilir; ancak Güvenlik ve Donanım kabulü ile değişikliği yapan kişinin onayı mümkün olduğunca ayrılmalıdır.

## Öncelik anlamı

| Öncelik | Anlam |
|---|---|
| P0 | Video, güvenlik veya yarışmaya çıkış bloklayıcısı |
| P1 | Birincilik puanını doğrudan belirleyen final görevi |
| P2 | Güvenilirlik, operasyon ve jüri puanını güçlendiren iş |
| P3 | Yalnız ana kapılar yeşilse yapılabilecek opsiyon |

## Şimdi yapılmayacaklar

- Kaynak kod implementasyonu.
- Yeni dijital ikiz, CSS veya görsel parlatma turu.
- Baseline alınmadan export/log/model silme.
- Mevcut auto-fire yoluyla fiziksel test.
- Zorunlu beş video yeteneği yeşil olmadan Y6’yı ana akışa alma.
- Çekim bilgisayarı gerektirmiyorsa video öncesi geniş Windows/Docker dönüşümü.

Bir sonraki adım yalnız kullanıcı onayıdır.
