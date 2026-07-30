# P1 — Generic body–balloon association sözleşmesi

Tarih: 2026-07-15. Kapsam: A2-02 için association. Bu katman fiziksel hareket veya ateş üretmez; Gateway yalnız `stable` sonucunu fiziksel aday kontrolünde okur.

## Durumlar

| Durum | Anlam | Fire etkisi |
|---|---|---|
| `tentative` | ilk/kararsız eşleme | fire adayı değildir |
| `stable` | aynı track → body eşlemesi en az üç frame | yalnız gelecekteki engagement katmanının girdisi |
| `ambiguous` | iki body benzer mesafede veya bir body için çakışan track | fail-closed, fire adayı değildir |
| `orphan` | uygun/fresh body yok | fail-closed, fire adayı değildir |

Eşleme, fresh balloon track ile body merkezleri arasında konfigüre edilmiş piksel mesafesinde yapılır. Bir body aynı frame’de yalnız bir balloon track’e bağlanabilir. Stable frame sayısı sıfırlanırsa önceki stable karar korunmaz.

## Kanıt

`backend/tests/test_phase68_body_balloon_association.py`:

- association ancak üç ardışık aynı eşleme sonrası `stable` olur;
- eşit/benzer yakınlık `ambiguous` üretir;
- body yokluğu `orphan` üretir.

HIL-06’ya ek: üç maket/balon ile çapraz geçişte stable/ambiguous/orphan durumları, track ID ve Gateway trace aynı run ID’de kaydedilir. `ambiguous`/`orphan` için Gateway reason code ve sıfır `LZR,1` ayrıca kaydedilir.
