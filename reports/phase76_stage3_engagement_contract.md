# P1 — Aşama 3 kanonik angajman ve skor sözleşmesi

Tarih: 2026-07-15. Kapsam: A3 fire adayının doğru decision hedefine bağlı olması, iki dost linkinin korunması ve tur sonucunun fiziksel/visual kanıttan türemesi.

## Zincir

`DecisionEngine selected body → stable enemy body–balloon link → iki stable FRIEND link → CommandGateway LZR,1 ACK → HitConfirmation → Stage3Engagement → canonical Stage3RoundEvent`

Gateway, DecisionEngine'in seçtiği body ile tracking candidate body farklıysa `A3_DECISION_TARGET_MISMATCH` ile reddeder. Enemy candidate sınıfsız veya enemy değilse `A3_CANDIDATE_CLASS_UNRESOLVED` / `A3_CANDIDATE_NOT_ENEMY` üretir. İki stable FRIEND link yoksa `A3_FRIEND_SAFETY_EVIDENCE_INCOMPLETE` ile fire output sıfırdır.

Atış kaydı doğrudan puan değildir:

- Enemy balloon loss, linked enemy body görünürken doğrulanırsa `CONFIRMED_HIT` olur.
- İki friend balloon track'i fresh ise `friend_safety_verified=true`.
- Friend body görünürken kendi linked balloon track'i kaybolursa `A3_FRIEND_HIT_SUSPECTED`; bu güvenli kabul edilmez ve kanonik turda friend penalty uygulanır.
- Pending enemy veya friend safety kanıtı eksikse tur kapanmaz.

`POST /api/mission/stage3/round/close` yalnız bu evidence state'iyle skor yazar; canlı/competition profilinde serbest score payload endpointi `A3_ENGAGEMENT_EVENT_API_REQUIRED` ile reddedilir. Tur kapanışı güvenli `STP` ve track/association/confirmation reset yapar.

## Otomatik kanıt

`backend/tests/test_phase76_stage3_engagement_contract.py`:

1. Confirmed F16 + iki görünür friend link → 30 puan.
2. Confirmed helicopter + friend linked balloon loss → friend-hit penalty; false SAFE yok.
3. Pending enemy veya missing friend evidence → round-close red.

`backend/tests/test_phase74_stage2_physical_engagement_contract.py` ayrıca post-decision A3 gateway'in ambiguous association ve iki friend-link yokluğu için sıfır `LZR,1` ürettiğini doğrular.

## HIL-09 kaydı

Her atışta enemy/friend balloon track, body track, association state, IFF profile hash, range profile hash, `Stage3EngagementStatus`, Pico ACK ve video zaman kodu aynı run ID altında tutulur. Bir `A3_FRIEND_HIT_SUSPECTED` veya `A3_DECISION_TARGET_MISMATCH` gerçek fiziksel atışta görülürse run FAIL ve A3 NO-GO'dur.
