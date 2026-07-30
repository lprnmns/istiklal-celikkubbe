# P1 — Aşama 2 kalıcı çoklu-track sözleşmesi

Tarih: 2026-07-15. Kapsam: A2-01 için üç eşzamanlı balon track telemetrisi. Track katmanı fiziksel write yapmaz; tamamlanan association/priority/hit-confirmation ile yalnız Gateway aday doğrulamasına veri sağlar.

## Uygulanan yol

`MultiTargetTrackerService`, her balloon detection için constant-velocity `KalmanTracker` kullanır. Frame’ler arasında tahmin–ölçüm eşlemesi deterministik greedy nearest-neighbour ile yapılır; eşleme eşiği aşılırsa yeni track açılır. Kısa occlusion’da track `predicted=true` olarak kalır, miss bütçesi aşılırsa silinir.

`AutoTrackerService.update` bu katmanı yalnız telemetri için çağırır. Eski tek-hedef PID kontrolü ve CommandGateway fiziksel yoluna yeni bir bypass eklenmemiştir. `TrackingStatus.multi_target_tracker` ve Motion ekranı aktif track, hit/miss ve predicted/fresh gerçekliğini gösterir.

## Otomatik kanıt

`backend/tests/test_phase67_multi_target_tracker.py`:

- aynı üç hedefin detection dizisi değişse bile track ID’leri korunur;
- tek-frame occlusion Kalman prediction üretir;
- miss bütçesi aşılınca track temizlenir.

## Donanım/HIL’ye eklenecek kabul

Pico/taret geldiğinde HIL-06 eklenir: üç fiziksel balon/maket, kısa occlusion, çapraz geçiş ve farklı hızda parkur çıkışı ile track ID, hit/miss, FPS/p95 latency, Tracker → Gateway command trace’i aynı run ID’de kaydedilir. Bu telemetri tek başına yeterli değildir: stable association, selected priority ve pending-shot red testi HIL-07/08 ile birlikte PASS olmalıdır.
