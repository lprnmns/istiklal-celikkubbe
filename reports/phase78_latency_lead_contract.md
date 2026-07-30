# P1 — Ölçülmüş latency tabanlı motion lead sözleşmesi

Tarih: 2026-07-15. Kapsam: Aşama 2 hareketli hedefte, fiziksel atış yetkisini değiştirmeyen kısa vadeli aim-point kestirimi.

## Davranış

- Varsayılan `lead_enabled=false`; yapılandırma ve Motion ekranı bu durumu açıkça gösterir.
- Operatör görünür Tracking/PID panelinden lead'i açıp çarpanı (`0..3`) ve üst ufku (`0..300 ms`) değiştirir. Kaynak kodu, environment veya gizli feature flag gerekmez.
- Ufuk: `min(lead_max_horizon_ms, (VisionEvent.total_latency_ms + control_period_ms) × lead_latency_multiplier)`.
- Konum, **son taze balon ölçümünden** başlar. Kalman multi-track yalnız hız kestirimi olarak kullanılır; filtre başlangıçta ölçümün gerisinde kalırsa taret geçmiş konuma yönelmez.
- Tahmin kamera çerçevesi içinde sınırlandırılır. Lead kapalıyken hedef merkezi doğrudan son ölçümdür ve `lead_horizon_ms=0`dır.

## Otomatik kanıt

`backend/tests/test_phase78_latency_lead_contract.py` şunları doğrular:

1. Varsayılan durumda Kalman lead kullanılmaz ve hedef ölçülen merkezdir.
2. Lead açıldığında ölçülmüş latency ile sınırlı, görünür pozitif horizon oluşur.
3. Tahmin, son ölçümün gerisine düşmez ve telemetry'de `predicted_target_center_x/y` olarak görünür.
4. Operatör lead'i tekrar kapattığında bir sonraki frame tekrar ham ölçümü kullanır.

Gerçek taret/kamera ile A/B etkisi kanıtlanmadan feature varsayılanı kapalı kalır. HIL-10, fiziksel kabul kaydıdır.
