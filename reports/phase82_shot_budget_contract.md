# P1 — ACK tabanlı atış bütçesi ve CO₂ saha ledgerı

Tarih: 2026-07-15. Kapsam: OPS-02 için atış sayacının UI tıklamasından değil, kanonik fiziksel komut sonucu olan Pico ACK'ten türemesi.

## Kanonik yol

`CommandGateway.fire_* → SerialService.gateway_exchange("LZR,1") → Pico ACK → shot_budget.active.json`

- Sadece `LZR,1` ACK alındığında `magazine_remaining` azalır ve `acknowledged_shot_count` artar.
- Sayım `config/runtime/shot_budget.active.json` altında kalıcıdır; restart sonrası kalan bütçe korunur.
- Sayaç boşsa Gateway fire kapısı `MAGAZINE_EMPTY` verir ve Pico'ya yazmaz.
- Ledger okunamazsa fail-closed: `magazine_remaining=0`, `SHOT_BUDGET_STATE_INVALID`.
- Operatör kapasiteyi yenileme/CO₂ değişiminde görünür UI eylemiyle sıfırlar. Bu eylem fiziksel tüp varlığını ispatlamaz; HIL-14 run kaydı gerekli kanıttır.

## Otomatik kanıt

`backend/tests/test_phase82_shot_budget_contract.py` mock Pico ile iki ACK'in iki bütçe tükettiğini, üçüncü fire'ın `MAGAZINE_EMPTY` ile sıfır `LZR,1` ürettiğini, state'in yeniden başlatmada korunduğunu ve bozuk state'in fail-closed kaldığını doğrular.

Gerçek CO₂ basınç/hız/isabet eğrisi ancak HIL-14 saha serisiyle elde edilir.
