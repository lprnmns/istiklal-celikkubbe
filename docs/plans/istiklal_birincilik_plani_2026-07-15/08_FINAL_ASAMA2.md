# 08 — Final Aşama 2: Sürü Saldırısı ve 105–120 Puan

## 1. Resmî görev

- Otonom görev.
- Dört tur.
- Her tur üç kolda üç hedef A’dan B’ye gider ve geri döner.
- Hedefler parkurdan çıkmadan imha edilmeli.
- 1 hedef 5, 2 hedef 15, 3 hedef 30 puan.
- Tur başına hiç hedef vuramama eksi 5.
- Üç tur boyunca hedef vuramama halinde aşama başarısız ve sıfır.
- Sınıflandırma beklenmez.
- Aşama 3’e geçmek için en az 20.

Birincilik tabanı:

- Üç tur 3/3 ve bir tur 2/3 = cezasız 105.
- Üst hedef dört tur 3/3 = 120.

## 2. Neden mevcut “en yakın balon” yaklaşımı yetmez

Üç eşzamanlı hedefte yalnız en yakını seçmek:

- Parkurdan önce çıkacak hedefi kaçırabilir.
- Aynı hedefe gereksiz tekrar atış yapabilir.
- Kısa kayıpta kimliği değiştirebilir.
- Balonu yanlış maketle eşleyebilir.
- Üçüncü hedefin yüksek marjinal puanını kaybettirir.

Gerekli çekirdek: kalıcı çoklu iz + doğru hedef/balon bağlantısı + çıkışa kalan süre önceliği + hit confirmation + yeniden angajman.

## 3. Aşama 2 algı sözleşmesi

Sınıflandırma zorunlu değildir. Sistem aşağıdakileri ister:

- Generic target body veya hedef taşıyıcı tespiti.
- Balon tespiti.
- Her body ve balon için kalıcı track ID.
- Body–balloon association.
- Hareket yönü, hız ve parkur ilerleme kestirimi.
- Görüşten çıkışa kalan süre.

Model Aşama 3 sınıflandırmasını sağlayabiliyorsa bilgi loglanabilir; Aşama 2 angajmanını bloklamaz.

## 4. Çoklu takip

Her iz:

- track_id.
- age ve hits/misses.
- pozisyon/hız/ivme kestirimi.
- confidence ve freshness.
- kısa occlusion durumu.
- body/balloon link.
- engagement state.
- last shot ve hit confirmation.
- tahmini parkur çıkış zamanı.

Tracker, tek frame en yakın kutu seçimi değil temporal kimlik üretmelidir. ByteTrack/Kalman veya ölçümle daha iyi olduğu kanıtlanan eşdeğer kullanılabilir.

## 5. Hedef öncelik fonksiyonu

Başlangıç bileşenleri:

- Parkurdan çıkışa kalan süre.
- Ateş çözüm kalitesi ve merkezleme süresi.
- Association confidence.
- Menzil/zone uygunluğu.
- Daha önce ateş edilip edilmediği.
- Hit confirmation.
- Taretin hedefe dönüş maliyeti.
- Yeniden angajman için kalan fırsat.

Öncelik ağırlıkları replay ve fiziksel denemeyle ayarlanır. Kural yalnız “en yakın” veya yalnız “en yüksek confidence” olmaz.

## 6. Lead ve kontrol

- Frame→guidance latency ölçülür.
- Track hızından kısa vadeli aim point kestirimi.
- Pan/tilt hız ve ivme sınırları.
- Backlash ve paralaks telafisi.
- Hedef değişiminde hysteresis; gereksiz ping-pong yok.
- Mekanik limite yaklaşan çözüm reddedilir veya yeniden planlanır.

Gelişmiş balistik çözüm ancak ölçümle fayda gösterirse eklenir; önce stabil merkezleme ve düşük latency.

## 7. Atış, hit confirmation ve yeniden angajman

Atıştan sonra iz hemen “imha” sayılmaz. Kanıt seçenekleri:

- Balonun ani kaybı/şekil değişimi.
- Patlama olayı.
- Body ile bağlı balonun kaybolması.
- Varsa fiziksel atış/çıkış sensörü.

Belirli doğrulama penceresinde hit yoksa:

- Aynı hedef yeniden aday olur.
- Shot cooldown ve maksimum deneme bütçesi uygulanır.
- Parkurdan çıkacak diğer hedeflerin puanı korunur.

Orphan veya ambiguous balona ateş yoktur.

## 8. Tur durum makinesi

    PREPARED
    → ACQUIRE_THREE
    → ENGAGE
    → CONFIRM / REENGAGE
    → TURN_COMPLETE
    → SAFE_RESET

Tur başında:

- Track geçmişi temizlenir.
- Sistem 0° başlangıç ve preflight doğrular.
- E-Stop/arm/zone aktif profile bağlıdır.

Tur sonunda:

- Hit sayısı ve puan.
- Kaçan hedef ve neden.
- Atış sayısı/CO₂.
- p50/p95 latency ve hata.
- Sonraki tur için otomatik değil, operatör onaylı reset.

## 9. Kabul testleri

### Replay

- Üç hedef farklı hız/yol.
- Kesişen kutular.
- Kısa occlusion.
- Bir hedef erken çıkış.
- İlk atış miss.
- Balonlar birbirine yakın.
- Kamera frame drop.

Beklenti:

- ID switch oranı tanımlı düşük eşik altında.
- Orphan/ambiguous ateş sıfır.
- En erken çıkış riski doğru önceliklenir.

### HIL

- Tetik enerjisi kapalı dört tam tur.
- Pan/tilt gerçek hareket.
- Disconnect/E-Stop ara senaryoları.

### Fiziksel

En az üç adet dört-turluk seri:

- Her seride en az 105 simüle puan.
- En az bir seride 120.
- Hiçbir tur 0 hedef değil.
- Son 12 turun en az 10’unda 3/3.
- Güvenlik bypass, kontrolsüz tarama ve yanlış balon angajmanı yok.
- Atış bütçesi final bakım planıyla uyumlu.

## 10. Muhtemel kod alanları

- backend/app/services/auto_tracker_service.py
- backend/app/services/kalman_tracker.py
- backend/app/services/vision_pipeline.py
- backend/app/services/mission_service.py
- backend/app/services/decision_engine.py
- backend/app/services/command_gateway.py — yeni
- backend/app/schemas/tracking.py
- backend/app/schemas/mission.py
- frontend/src/components/cockpit/EngagementPanel.vue
- frontend/src/components/cockpit/EngagementSummaryPanel.vue
- frontend/src/stores/missionStore.ts
- yeni Aşama 2 replay/HIL testleri

## 11. Geri dönüş koşulu

Gelişmiş lead veya yeni tracker:

- ID switch’i artırırsa,
- p95 latency’yi kontrol bütçesi dışına çıkarırsa,
- Y5 baseline’ını bozarsa,
- hedefler arasında osilasyon oluşturursa

özellik bayrağıyla kapatılır ve son kanıtlı kalıcı tracker/merkezleme profiline dönülür. Tek hedefli eski auto-fire canlı geri dönüş olarak kullanılmaz.
