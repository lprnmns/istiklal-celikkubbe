# P1 — Aşama 3 tur/skor sözleşmesi

Tarih: 2026-07-15. Kapsam: resmî sekiz tur skor/miss çekirdeği. IFF, class provenance, association, range ve SafetyDecision tamamlanmadan fiziksel fire’a bağlanmaz.

## Kanonik tur olayı

`POST /api/mission/stage3/round/complete` şu verileri alır: `enemy_class`, `enemy_hit`, `friend_hit`.

| Sınıf | Enemy hit puanı |
|---|---:|
| F-16 | 30 |
| Helikopter | 20 |
| Balistik Füze | 20 |
| Mini/Micro İHA | 10 |

Enemy miss veya friend hit bir turda en çok `-10` ceza üretir. Üç ardışık enemy miss `stage3_failed=true` yapar ve Aşama 3 skorunu sıfırlar. Sekiz turdan fazla kayıt reddedilir; ödül eşiği `>=10` görünürdür. Eski mutable stage3 sayaç API’si `STAGE3_EVENT_API_REQUIRED` ile reddedilir.

## Otomatik kanıt

`backend/tests/test_mission_operations.py`:

- F-16 hit = 30, helikopter hit + friend hit = 10 net;
- üç ardışık enemy miss = stage failed + skor 0;
- legacy mutable API reddi.

## HIL devamı

HIL-09’da sekiz turda class/IFF/link/range/safety/command/ACK/score kanıtı aynı run ID’ye yazılır. Bir friend hit, ambiguous link veya belirsiz range’de fiziki Aşama 3 fire NO-GO kalır.
