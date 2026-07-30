# 11 — Test, Kanıt ve Jüri Planı

## 1. Ana kural

Bir görev ancak şu üçü birlikte varsa biter:

1. Kabul kriteri geçti.
2. Tekrar edilebilir test var.
3. Kanıt paketi gerçek konfigürasyona bağlı.

Kod derlenmesi, UI ekran görüntüsü veya sentetik demo fiziksel yarışma kabiliyetinin kanıtı değildir.

## 2. Test piramidi

| Katman | Amaç | Fiziksel risk |
|---|---|---|
| Static/unit | Kural, şema, pin çakışması, doğrudan write taraması | Yok |
| Replay | Tracker, IFF, association, range, mission | Yok |
| DRY_RUN E2E | UI → decision → gateway, TX yok | Yok |
| HIL | Gerçek Pico/kamera, tetik enerjisi kapalı | Düşük |
| Motion acceptance | Gerçek iki eksen, tetik kapalı | Kontrollü |
| Fire acceptance | Sınırlı gerçek atış, backstop | Yüksek; yetkili |
| Full mission | Yarışma benzeri tur ve bakım | En yüksek; checklist |

Katman atlanmaz. Güvenlik değişikliği unit/replay’den doğrudan canlı atışa çıkmaz.

## 3. Run evidence paketi

Önerilen yapı:

    evidence/runs/RUN_ID/
      manifest.json
      config_snapshot.yaml
      firmware_info.json
      model_info.json
      device_info.json
      safety_decisions.jsonl
      commands_and_acks.jsonl
      metrics.json
      operator_notes.md
      video/
      screenshots/

Manifest:

- Gereksinim/test ID.
- Tarih/saat ve operatör.
- Commit ve dirty diff hash.
- Firmware/config/model/profile hash.
- Kamera/Pico kimliği.
- E-Stop/arm durumu.
- CO₂/atış sayısı.
- Sonuç.
- Başarısızlık reason code.
- Ham dosya SHA-256.

## 4. Gereksinim izlenebilirliği

Tek matris:

| Requirement | Tasarım | Kod/firmware | Test | Son kanıt | Durum |
|---|---|---|---|---|---|
| VID-01…VID-06 | İlgili plan | Dosya/commit | Run ID | Klip/metric | R/Y/G |
| SAFE | Güç+gateway | Firmware/backend | HIL/fiziksel | Ölçüm/video | R/Y/G |
| A1 | Manuel mission | Backend/frontend | 10 tur | Skor logu | R/Y/G |
| A2 | Multi-track | Vision/mission | 3×4 tur | Track/score | R/Y/G |
| A3 | IFF/range/link | Vision/decision | 3×8 tur | Turn dossier | R/Y/G |

235 ayrı rapor yerine jüriye bu matris ve seçili kanıtlar gösterilir.

## 5. Zorunlu kabul panosu

| Kapı | Minimum |
|---|---|
| Baseline | 10 kayıtlı deneme ve geri dönüş paketi |
| Y2 | 5’te 4; çekim öncesi hedef 10’da 9 |
| Y3 | 3 ardışık |
| Y4 | 3 ardışık |
| Y5 | 3 ardışık 10–15 s |
| Video | Aynı rig ile 2 tam prova |
| A1 | Son 10 tur kriterleri |
| A2 | 3 adet dört-turluk seri, her biri 105+ |
| A3 | 3 adet sekiz-turluk seri, her biri 120+, dost vuruşu 0 |
| Setup | 3 tam kurulum, 30 dakika altı |
| Bakım | 3 pit provası, toplam 10 dakika altı |
| Soak | En az 30 dakika, kontrolsüz disk/memory büyümesi yok |

## 6. Ölçülecek metrikler

Görüntü/kontrol:

- Kamera gerçek FPS.
- Frame age.
- Inference p50/p95.
- End-to-end frame→guidance p50/p95.
- Track ID switch.
- X/Y merkezleme hatası.
- Reacquire süresi.
- Association stability.
- Range hata dağılımı.

Komut/güvenlik:

- Serial ACK p50/p95 ve timeout.
- E-Stop duruş gecikmesi/mesafesi.
- E-Stop sonrası tetik çıkışı sayısı: sıfır.
- Stale/duplicate command sayısı: sıfır.
- NO-FIRE reason dağılımı.

Görev:

- Hit/shot.
- Time-to-first-track.
- Time-to-engage.
- A1 süre/puan.
- A2 hedef/tur ve puan.
- A3 sınıf, IFF, menzil, dost/düşman sonucu.
- CO₂ atış sayısı ve basınç/başarı ilişkisi.

E-Stop ve kontrol için kesin sayısal limit, ilk fiziksel ölçüm ve güvenlik sahibi onayıyla kilitlenir; ölçülmemiş bir sayı plan gereğiymiş gibi uydurulmaz.

## 7. Failure review

Her başarısız fiziksel run için 15 dakikalık kısa inceleme:

- Beklenen neydi?
- İlk sapma hangi timestamp?
- SafetyDecision ne dedi?
- Komut/ACK ne oldu?
- Fiziksel sistem ne yaptı?
- Kök neden kanıtı var mı?
- Tekrarı engelleyen değişiklik/test nedir?

Kanıtsız “muhtemelen” ile fiziksel hata kapatılmaz.

## 8. KTR → gerçek sistem fark matrisi

Final sunumundan önce:

| KTR’de hedeflenen | Gerçekte uygulanan | Değişiklik nedeni | Ölçülen sonuç | Kanıt |
|---|---|---|---|---|
| Ana hedef modeli |  |  |  |  |
| Balon modeli |  |  |  |  |
| ByteTrack/Kalman |  |  |  |  |
| Fire Gate |  |  |  |  |
| JSON-line protokol |  |  |  |  |
| Limit/home |  |  |  |  |
| Kapalı çevrim atış |  |  |  |  |
| Setup/operatör UI |  |  |  |  |

Uygulanmayan özellik saklanmaz. Jüriye problem, mühendislik kararı ve ölçülmüş iyileşme anlatılır.

## 9. Final sunumu için 10 slaytlık omurga

1. Yarışma görevi ve İSTİKLAL’in tek cümle çözümü.
2. Gerçek sistem ve özgün mekanik mimari.
3. KTR sonrası en kritik üç problem.
4. SafetyDecision + CommandGateway + fiziksel E-Stop.
5. Algı zinciri ve açıklanabilir hedef–balon bağlantısı.
6. Aşama 1 sonuçları.
7. Aşama 2 sonuçları.
8. Aşama 3 sonuçları ve sıfır dost vuruşu.
9. Güvenilirlik: kurulum, bakım, CO₂, recovery.
10. Ölçülmüş sonuç, öğrenilenler ve kapanış.

Her iddia tek sayı ve tek kanıtla desteklenir. Mimari şema, jüriye çalışan zinciri anlatmak için kullanılır; ayrıntılı klasör ağacı gösterilmez.

## 10. Teknik mülakat

Danışman olmadan takım cevap verebilmelidir:

- Neden bu tracker/model?
- E-Stop gerçek enerjiyi nasıl kesiyor?
- Tek bir hatalı frame neden ateş üretemiyor?
- Dost/düşman rengi değişirse ne yapılır?
- Balon doğru makete nasıl bağlanıyor?
- Menzil nasıl ölçülüyor ve hata nedir?
- USB/kamera koparsa ne olur?
- Üç ardışık miss nasıl önlenir?
- 30 atış/CO₂ ve 10 dakika bakım nasıl yönetilir?
- KTR’den ne değişti ve neden?

Her alanın birincil ve yedek konuşmacısı; iki çapraz sorgu provası yapılır.

## 11. Jüri evidence dossier

Tek klasör:

- Bir sayfa gereksinim/sonuç matrisi.
- Bir sayfa as-built sistem ve pin/power şeması.
- Video Y1–Y5 teslim kanıtı.
- E-Stop ölçüm özeti.
- A1/A2/A3 son kabul tabloları.
- Model/IFF/association/range confusion ve hata özetleri.
- Kurulum/bakım/CO₂ prova sonucu.
- KTR delta matrisi.
- Seçili 5–10 kısa kanıt klibi.
- Release manifest ve sürüm hash’leri.

UI/dijital ikiz, fiziksel sonuçları açıklamak için kullanılır; fiziksel sonuçların yerine sunulmaz.
