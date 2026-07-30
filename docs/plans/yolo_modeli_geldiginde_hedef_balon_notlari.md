# YOLO Modeli Geldiğinde Sorulacak Hedef–Balon Notları

Tarih: 2026-07-16

Bu dosya kullanıcının “not ettiğin şeyler neydi?” diye sorduğunda geri dönmek
üzere tutulur.

1. Yarışmadaki her fiziksel hedefin kendisine ait bir balonu olacak.
2. Balon gerçek çapı 14 cm'dir.
3. Body var ama bağlı balon yoksa nesne operasyonel angajman hedefi sayılmamalı.
4. Balon var ama bağlı body yoksa balon tek başına angajman hedefi sayılmamalı.
5. Mühendis/debug görünümü ham body-only ve orphan-balloon detections'ı göstermeli;
   operatör görünümü yalnız geçerli birleşik hedefleri vurgulamalı.
6. Balon daha kolay algılanıyorsa balon-önce candidate-region üretimi denenmeli:
   önce balon, sonra çevresindeki beklenen body bölgesi.
7. Buna rağmen body ve balon detector/tracker sonuçları bağımsız korunmalı; yalnız
   balon detector'a bağımlı tek yol kısa örtülmede hedef kimliğini kaybettirir.
8. Eşleme yalnız merkez yakınlığı olmamalı. Şunlar birlikte kullanılmalı:
   - body bbox içi veya sınıfa özel bağlantı/attachment ROI,
   - body'ye göre normalize balon konumu,
   - ortak hız ve hareket yönü,
   - optical-flow benzerliği,
   - track geçmişi/histerezis,
   - one-to-one bipartite matching.
9. Bir body–bir balon sözleşmesi ihlal edilirse association `ambiguous` olmalı ve
   fiziksel ateş engellenmeli.
10. Eğitim/validation etiketlerinde body bbox, balloon bbox, class, team ve mümkünse
    video sequence/track identity bulunmalı.
11. Zor test seti şunları içermeli:
    - 1 body/1 balloon,
    - 3 hedef çapraz geçiş,
    - body bbox overlap,
    - balon kısa örtülme,
    - body kısa örtülme,
    - balon patlama/şekil değişimi,
    - orphan balloon,
    - body-only nesne,
    - motion blur ve değişen ışık,
    - 5/10/15 m ve farklı açılar.
12. Atıştan önce bağlı body ve balloon track ID değişmez snapshot olarak kaydedilmeli.
13. Atıştan sonra `0.3–0.8 s` ana gözlem penceresi kullanılabilir; tek missing frame
    hit değildir. Çok kareli kayıp, body sürekliliği ve taze kamera şarttır.
14. Body ve balon birlikte kaybolursa hit değil `UNCONFIRMED` sonucu üretilmeli.
15. Balon görünür kalırsa `MISS_CONFIRMED`; güvenilir biçimde kaybolursa
    `HIT_CONFIRMED`; kanıt yetersizse `UNCONFIRMED` olmalı.
16. Atış sonucu ile görev sonucu ayrı tutulmalı. Bir atış ıska iken görev sonraki
    angajmanla başarılı olabilir.
17. YOLO modelinin gerçek class-name/id haritası model paket manifestinde açıkça
    tanımlanmalı; UI koduna gizli sıra varsayımı yazılmamalı.
18. Model değişince model hash, camera profile, intrinsics ve association calibration
    aynı acceptance run'ında tekrar doğrulanmalı.
