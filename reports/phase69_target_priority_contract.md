# P1 — Aşama 2 hedef önceliği sözleşmesi

Tarih: 2026-07-15. Kapsam: A2-03 priority sıralaması. Servis physical command üretmez; Gateway yalnız telemetrideki seçili track ile tracking adayının aynı olduğunu doğrular.

## Kurallar

- Sadece `stable` body–balloon association ve fresh balloon track aday olabilir.
- `ambiguous`, `orphan`, `tentative` veya predicted track doğrudan `excluded_track_ids`e gider.
- Sıra; frame’den çıkışa kalan tahmini süre, çözüm kalitesi (confidence + aim yakınlığı), taret dönüş maliyeti ve seçili hedef hysteresis’iyle üretilir.
- Eşit skorda düşük track ID deterministik olarak öndedir.

Öncelik `TargetPriorityStatus` olarak `/api/motion/tracking/priority`den ve Motion ekranında görünür. Gateway yalnız stable association ve pending-shot kontrolüyle birlikte bu seçimi kullanır.

## Otomatik kanıt

`backend/tests/test_phase69_target_priority.py`:

- parkurdan daha erken çıkacak stable hedef önceliklenir;
- ambiguous/orphan track’ler listeden tamamen dışlanır.

## HIL devamı

HIL-06/07’de hedeflerin farklı hızda çıkışı, occlusion ve cross-over için öncelik sırası aynı run ID’de kaydedilir. Seçili olmayan track için `A2_PRIORITY_TARGET_MISMATCH` ve sıfır fire kabul kriteridir.
