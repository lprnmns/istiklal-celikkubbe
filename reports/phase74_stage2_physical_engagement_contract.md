# P1 — Aşama 2 CommandGateway angajman sözleşmesi

Tarih: 2026-07-15. Kapsam: A2 telemetry → Gateway fiziksel tetik aday zinciri.

## Çağrı zinciri

`VisionEvent → MultiTargetTracker → stable Body–Balloon Association → TargetPriority → TrackingLoop fire candidate → CommandGateway → Pico LZR,1 → HitConfirmation(PENDING_CONFIRMATION)`

Tracking/association/priority/hit-confirmation hiçbiri seri porta yazmaz. `LZR,1` yalnız CommandGateway'in son çağrısıdır.

`CONFIRMED_HIT` kaydı `Stage2EngagementService` içinde tutulur. Operatör tur sonunda yalnız “doğrulanmış sonuçla turu kapat” eylemi yapar; puan bu kayıtlardan türetilir. Canlı/competition profilinde serbest `confirmed_hits` sayısı API ile yazılamaz (`A2_ENGAGEMENT_EVENT_API_REQUIRED`); pending bir atış varken tur kapanmaz (`A2_ROUND_CONFIRMATION_PENDING`).

Tur kapanışı `STP` ile güvenli ara duruma geçer ve balloon track, body–balloon association, priority, hit-confirmation ile seçili hedef durumunu sıfırlar; sonraki tur önceki hareket/atış bağlamını devralmaz.

## A2 ve A3 candidate kapıları

1. `balloon_track_id` çözümlenir ve fresh olmalıdır.
2. Tracking aktif olmalıdır.
3. Candidate, `TargetPriority.selected_track_id` ile aynı olmalıdır.
4. Body–balloon association `stable` ve güncel body id ile uyumlu olmalıdır.
5. Aynı balloon track `PENDING_CONFIRMATION` ise yeni atış yoktur.
6. Ardından ortak Gateway preflight: Pico/heartbeat, E-Stop, arm, kamera freshness, limit/zone.
7. A3 ayrıca DecisionEngine'in class + real IFF + range + safety kapılarını geçer.

| Red durumu | UI reason code |
|---|---|
| Track id yok | `A2_TRACK_ID_UNRESOLVED` / `A3_TRACK_ID_UNRESOLVED` |
| Track stale | `A2_TRACK_STALE` / `A3_TRACK_STALE` |
| Seçili aday değil | `A2_PRIORITY_TARGET_MISMATCH` / `A3_PRIORITY_TARGET_MISMATCH` |
| Link tentative/ambiguous/orphan | `A2_ASSOCIATION_NOT_STABLE` / `A3_ASSOCIATION_NOT_STABLE` |
| Link body uyuşmaz | `A2_ASSOCIATION_TARGET_MISMATCH` / `A3_ASSOCIATION_TARGET_MISMATCH` |
| Önceki atış doğrulanıyor | `A2_HIT_CONFIRMATION_PENDING` / `A3_HIT_CONFIRMATION_PENDING` |

## Otomatik kanıt

`backend/tests/test_phase74_stage2_physical_engagement_contract.py` mock Pico ile:

- üç frame stable association + selected priority adayında `LZR,1` ACK ve `PENDING_CONFIRMATION` kaydını;
- aynı track'in duplicate atışının `A2_HIT_CONFIRMATION_PENDING` ile reddini;
- ambiguous linkte `A2_ASSOCIATION_NOT_STABLE` ve sıfır `LZR,1`i;
- hit confirmation'ın frame-local body id yerine persistent `body_track_id` kullandığını doğrular.
- live competition round sonucunun operatör sayısı yerine confirmed-hit kaydından türediğini doğrular.

Gerçek backstop/HIL-06…08 PASS olmadan A2 saha performans iddiası veya otomatik round-score kabulü yapılmaz.
