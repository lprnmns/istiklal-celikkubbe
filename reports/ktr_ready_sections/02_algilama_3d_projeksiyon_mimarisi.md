# Algılama - 3B Projeksiyon Mimarisi

Algılama hattı, kamera görüntüsündeki hedefleri 2B kutu bilgisiyle temsil eder. Her tespit için temel veriler şunlardır: hedef sınıfı, güven değeri, hedef kutusu (`bbox`), kutu merkezi, kutu alan oranı ve opsiyonel takip kimliği. Bu veriler dijital ikiz kokpitinde operatörün okuyabileceği 3B sahne göstergelerine dönüştürülür.

2B görüntüdeki hedef merkezi normalize edilerek `x_norm` ve `y_norm` değerleri hesaplanır. `x_norm` hedefin görüntünün sol/sağ tarafındaki konumunu, `y_norm` ise yukarı/aşağı konumunu belirtir. Bu değerler 3B sahnede hedef marker konumunu belirlemek için kullanılır. Hedef kamera görüntüsünün sağındaysa dijital ikiz görüş hacminde de sağ tarafta, yukarıdaysa optik eksenin üst tarafında gösterilir.

Derinlik bu fazda metrik mesafe olarak iddia edilmez. Kalibre edilmiş stereo, lidar veya gerçek menzil ölçümü olmadığı durumda kutu alan oranı göreli derinlik ipucu olarak kullanılır. Büyük kutu alanı hedefin daha yakın, küçük kutu alanı hedefin daha uzak olduğu anlamına gelen `near`, `mid`, `far` bantlarına dönüştürülür. Bu değer, operatör açıklaması için göreli derinliktir; kesin metre hesabı değildir.

3B dijital ikiz sahnesinde kamera görüş alanı yarı saydam bir FOV konisi/frustumu ile gösterilir. Kamera optik ekseni ayrı bir referans çizgisiyle, namlu/launcher referans ekseni ise ayrı bir çizgiyle gösterilir. Bu ayrım önemlidir; namlu referans ekseni yalnızca görsel hizalama açıklamasıdır ve fiziksel komut üretmez.

Mekanik revizyondan sonra kamera ile namlu/fırlatıcı ekseni arasındaki pratik düşey ofset yaklaşık 30 mm olarak temsil edilir. Bu değer `camera_to_launcher_offset_z_mm=30` kalibrasyon parametresiyle sahnede açıklanır. Ofset, mevcut fazda yalnızca görselleştirme ve raporlama kanıtıdır; fiziksel atış çözümü veya servo/motor komutu üretiminde kullanılmaz.

Kokpit, poz kaynağını yanıltmadan gösterir. Olası kaynaklar `telemetry`, `tracker_estimate`, `replay_fixture` ve `fixture` olarak ayrılır. Pico telemetrisi yoksa sistem bunu gerçek telemetri gibi sunmaz; `tracker_estimate` veya fixture tabanlı poz olarak gösterir.

Bu mimari hata ayıklamayı güçlendirir. Operatör ve geliştirici; hedef kutusunun, güven değerinin, göreli derinliğin, görüş konisinin, optik eksenin ve güvenlik kapılarının aynı sahnede nasıl hizalandığını görebilir. Bu sayede yanlış kamera seçimi, hedef konum hatası, eksen hizalama problemi veya güvenlik blokajı daha hızlı anlaşılır.
