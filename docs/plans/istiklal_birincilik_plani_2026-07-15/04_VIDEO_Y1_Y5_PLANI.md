# 04 — Görev Kabiliyeti Videosu Y1–Y5 Planı

## 1. Teslim sözleşmesi

- Tek YouTube videosu.
- 2–5 dakika.
- En az 720p; iç hedef 1080p H.264.
- Y1, Y2, Y3, Y4, Y5 resmî sırada.
- Bölüm numarası görüntü üzerinde açıkça yazılı.
- Açıklamada zaman damgaları.
- Y6 yalnız zorunlu akışı riske atmıyorsa eklenir.
- Link KYS’ye girilir ve oturum kapalı cihazlardan doğrulanır.

## 2. Önerilen 4:25 storyboard

| Zaman | Bölüm | İçerik |
|---|---|---|
| 00:00–00:08 | Kimlik | Takım, sistem ve tek cümle amaç |
| 00:08–00:55 | Y1 | Operatör arayüzü, girdiler, health, mod, safety, gerçek fiziksel sistem |
| 00:55–01:35 | Y2 | Ölçülmüş 15 m, durağan sistem, takip ve balon patlaması |
| 01:35–02:10 | Y3 | İki eksen hareket, fiziksel E-Stop, latched duruş |
| 02:10–02:50 | Y4 | Kontrollü atış dizisi, E-Stop sonrası atışın kesilmesi |
| 02:50–03:40 | Y5 | Yatay+dikey hareket eden hedefin 10–15 s takibi |
| 03:40–04:20 | Y6 opsiyonel | 4 sınıf × seçili net 5/10/15 m örnekleri |
| 04:20–04:25 | Kapanış | Sistem ve ekip geniş plan |

Y6 yoksa video 3:45–4:00 civarında bitirilebilir. Süreyi doldurmak için tekrarlı ekran veya uzun konuşma eklenmez.

## 3. Y1 — Arayüzler

Gösterilecekler:

- Gerçek canlı kamera.
- Kullanılan klavye/joystick/diğer girdiler.
- MANUAL, TRACK/VIDEO ve güvenli durum ayrımı.
- Pico, kamera, E-Stop, aktüatör izni, model ve log health.
- Hedef/track durumu.
- FIRE veya NO-FIRE ve açık reason code.
- Setup/Quick Preflight özeti.
- Fiziksel sistem ile ekran aynı bölümde.

Kabul:

- 45–60 saniyede anlaşılır.
- Mock/dev/no-TX verisi ana kanıt olarak görünmez.
- Operatör görev başlatmak için kod/config düzenlemez.
- Kamera veya Pico çıkarıldığında stale gerçekliği gizlenmez.

Çekim:

- Omuz üstü ekran+operatör planı.
- Kısa ekran kaydı insert’i.
- Girdinin fiziksel sistemdeki karşılığı görünür.

## 4. Y2 — 15 m durağan balon imhası

Kabul:

- Mesafe lazer metre veya şerit metreyle ölçülür; başlangıç ve hedef referansı görünür.
- Sistem tabanı durağandır.
- Güvenli backstop ve boş atış hattı vardır.
- En az 5 mühendislik provasında en az 4 başarı; final çekim öncesi son 10 denemede hedef en az 9 başarı.
- CO₂ durumu, atış sayısı ve konfigürasyon kayıtlıdır.
- Patlama ve sistem aynı kesintisiz geniş planda anlaşılır.

Çekim:

- Önce 15 m ölçüm insert’i.
- Sonra kesintisiz geniş ana plan.
- Ekran hedef kutusu ikincil picture-in-picture olabilir; fiziksel kanıtın yerini almaz.

## 5. Y3 — Hareket sırasında E-Stop

Kabul:

- Pan ve tilt gerçekten hareket eder.
- Fiziksel kablolu E-Stop kadrajda basılır.
- İki eksen fiziksel olarak durur.
- UI durumu ESTOP_ACTIVE/SAFE_STOP olarak latched gösterir.
- Buton çözülünce otomatik yeniden hareket yoktur.
- Üç ardışık başarılı prova.
- Duruş gecikmesi video/telemetriyle ölçülür ve güvenlik sahibi tarafından onaylanmış limite uyar.

Çekim:

- Tek geniş planda taret, E-Stop butonu ve operatör.
- Gerekirse eşzamanlı ekran insert’i.
- Hızlandırma veya olay anında kesme yok.

## 6. Y4 — Ateş sırasında E-Stop

Kabul:

- Kontrollü ve önceden sayısı belirlenmiş atış dizisi.
- E-Stop öncesi en az bir gerçek atış.
- E-Stop sonrası planlanan atışlar gerçekleşmez.
- Tetik/servo enerji yolu fiziksel olarak kesilir; yalnız host yazılım komutuna güvenilmez.
- Kuyruktaki komutlar temizlenir, E-Stop çözülünce replay olmaz.
- Servo güç/komut/ACK olayları aynı run ID’ye bağlıdır.
- Üç ardışık başarılı prova.

Çekim:

- Güvenli backstop.
- Taret, hedef hattı ve buton görünür.
- Atışların ses/görüntüyle sayılabildiği kesintisiz plan.
- E-Stop sonrası beklenen fakat oluşmayan atış için yeterli bekleme süresi.

## 7. Y5 — İki eksenli hareketli hedef takibi

Kabul:

- Hedef hem yatay hem dikey hareket eder.
- En az 10–15 saniye stabil fiziksel takip.
- Kalıcı track ID korunur; kısa kayıp/reacquire davranışı tanımlıdır.
- X/Y merkezleme hatası ve frame→guidance latency loglanır.
- Mekanik limite çarpma, kontrolsüz tarama ve belirgin osilasyon yok.
- Fiziksel tetik kapalı veya DRY_RUN olabilir.
- Üç ardışık başarılı prova.

Çekim:

- Hedef hareketi ve taret iki ekseni geniş planda görünür.
- Ekran insert’inde track ID ve merkezleme kutusu.
- Yalnız ekran videosu kabul edilmez.

## 8. Y6 — Opsiyonel sınıflandırma go/no-go

GO koşulları:

- F-16, Helikopter, Balistik Füze ve Mini/Micro İHA sınıf ID’leri gerçek inference ile doğrulanmış.
- Her sınıf için 5, 10 ve 15 m kayıt matrisi mevcut.
- Etiket kararlılığı ve latency bütçesi kabul edilmiş.
- Zorunlu Y1–Y5 iki tam provada yeşil.
- Bölüm 45 saniye altında anlatılabiliyor.

NO-GO koşulları:

- Metadata doğru ama gerçek logits/sınıf mapping belirsiz.
- 15 m’de etiket sıçrıyor.
- GPU/CPU yükü Y5 takibini bozuyor.
- Yeni model zorunlu akışın kamera veya cihaz kararlılığını etkiliyor.

NO-GO halinde Y6 videodan çıkarılır; final Aşama 3 geliştirmesi devam eder.

## 9. Çekim kanıt standardı

Her take için:

- Run ID.
- Tarih/saat.
- Commit.
- Firmware hash.
- Config/profile hash.
- Model hash veya “model yok”.
- Kamera/Pico device ID.
- CO₂/atış sayısı.
- Ham video dosya adı ve SHA-256.
- Sonuç ve başarısızlık nedeni.

Kritik olaylarda geniş fiziksel plan birincil kanıttır. UI, telemetri ve picture-in-picture açıklayıcı ikincil kanıttır.

## 10. Tam video GO kapısı

GO:

- Y1–Y5 ayrı acceptance yeşil.
- Y3 ve Y4 üçer ardışık temiz.
- Ölçülmüş 15 m başarı.
- Y5 iki eksen ve en az 10 saniye.
- Aynı ekipmanla iki tam video provası 5 dakika altında.
- Final ham içerik iki fiziksel depoda.
- YouTube linki oturum kapalı iki ortamda çalışıyor.
- KYS sorumlusu ve yedeği belli.

NO-GO:

- E-Stop tetik enerjisini kesmiyor.
- Y2 mesafesi görünür değil.
- Y5 tek eksen veya yalnız ekran.
- Yetenek sırası/numarası yanlış.
- Video 5 dakikadan uzun.
- Link erişilemiyor veya işleme 720p altı.

## 11. Teslim checklist’i

- [ ] Dosya 2–5 dakika.
- [ ] En az 720p.
- [ ] Y1–Y5 doğru sıra.
- [ ] Her yetenek numaralı.
- [ ] Y2 15 m ölçümü görünür.
- [ ] Y3/Y4 fiziksel E-Stop görünür.
- [ ] Y5 iki eksen açık.
- [ ] Açıklama zaman damgaları.
- [ ] Liste dışı link oturum kapalı çalışıyor.
- [ ] KYS’ye doğru link girildi.
- [ ] KYS gönderim kanıtı arşivlendi.
- [ ] Ham, kurgu ve final dosyaları iki yedekte.
