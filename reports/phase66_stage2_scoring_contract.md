# P1 — Aşama 2 tur/skor sözleşmesi

Tarih: 2026-07-15. Kapsam: A2-06 resmî skor çekirdeği; henüz tracker, association ve hit-confirmation yerine geçmez.

## Kanonik tur olayı

`POST /api/mission/stage2/round/complete` yalnız aktif Aşama 2’de 0–3 `confirmed_hits` kabul eder.

| Onaylı hedef | Tur puanı |
|---:|---:|
| 0 | -5 |
| 1 | 5 |
| 2 | 15 |
| 3 | 30 |

Her tur `stage2_round_events` içine round, hit, puan ve zero-hit streak ile yazılır. Üç ardışık sıfır-hit, `stage2_failed=true` yapar ve Aşama 2 skorunu sıfırlar. Dört tur sonrası başka tur tamamlanamaz. Geçiş göstergesi `stage2_score >= 20`dir.

Eski `stage2_hits` / `stage2_round` genel güncellemesi `STAGE2_EVENT_API_REQUIRED` ile reddedilir; böylece UI veya eski bir endpoint resmî skoru serbestçe değiştiremez.

## Kanıt

`backend/tests/test_mission_operations.py`:

- `3,3,3,2` tur dizisi = `30+30+30+15 = 105`;
- üç ardışık `0` hit = Aşama 2 başarısız ve skor `0`;
- eski mutable API reddi;
- KTR raporuna tur sonucunun girişi.

`MissionModesView` turu 0/1/2/3 hit olarak açıkça onaylatır ve 0-hit serisi/20 puan geçiş durumunu gösterir.
