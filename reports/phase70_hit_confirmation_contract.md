# P1 — Aşama 2 hit-confirmation sözleşmesi

Tarih: 2026-07-15. Kapsam: A2-05 atış sonrası durum makinesi. Gateway'in A2/A3'te kabul ettiği fiziksel atış burada `PENDING_CONFIRMATION` olarak kaydedilir; hit sayılmaz.

## Durum makinesi

`register_shot(track, linked_body)` her atışı `PENDING_CONFIRMATION` olarak başlatır; atış hiçbir zaman doğrudan imha/hit değildir.

- Linked body görünür kalırken balloon track kaybolursa: `CONFIRMED_HIT` (`LINKED_BODY_VISIBLE_BALLOON_LOST`).
- Bu kanıt gelmeden confirmation penceresi biterse: `REENGAGE` (`CONFIRMATION_TIMEOUT_REENGAGE`).
- Body de kaybolduğunda sistem false-hit üretmez.

## Otomatik kanıt

`backend/tests/test_phase70_hit_confirmation.py` pending → visual-loss confirmed hit ve pending → timeout reengage zincirlerini doğrular.

## HIL devamı

HIL-08’de kontrollü hit/miss için shot ACK, association, balloon track, body track, confirmation state, CO₂/atış sayısı ve video aynı run ID’de tutulur. Pending durumunda aynı track için ikinci `LZR,1` oluşmaz (`A2_HIT_CONFIRMATION_PENDING`). HIL-08 güvenilir olmadan Aşama 2 skoruna otomatik hit yazılmaz.
