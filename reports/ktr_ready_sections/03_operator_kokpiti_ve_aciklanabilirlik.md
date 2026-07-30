# Operatör Kokpiti ve Açıklanabilirlik

İSTİKLAL C2 kokpiti, operatörün sistemi tek ekranda anlaması için tasarlanmıştır. Her panel belirli bir operasyonel soruya cevap verir.

`Camera HUD` paneli, kamera görüntüsü veya KTR fixture görünümü üzerinde hedef kutusunu, hedef merkezini, nişangah referansını, normalize koordinatları, güven değerini ve veri kaynağını gösterir. KTR demo modunda panel açıkça `KTR FIXTURE - NOT LIVE` ve `evidence_truth=fixture` olarak etiketlenir.

`3D Digital Twin` paneli, hedef tespit bilgisini 3B operasyonel sahneye aktarır. STL tabanlı dijital ikiz, kamera FOV konisi, kamera optik ekseni, namlu referans ekseni, 30 mm kamera-namlu ofseti ve hedef projeksiyon ışını birlikte gösterilir. Bu panel hedefin yalnızca görüntüde değil, sistem referansları içinde nasıl yorumlandığını açıklar.

`Cihaz Yöneticisi` paneli kamera kaynağını, USB kamera durumunu, Pico bağlantısını, dijital ikiz asset durumunu ve fiziksel komut durumunu özetler. Donanım bağlı değilse bu durum `OFFLINE_EXPECTED` olarak gösterilir; geliştirme ortamında kritik hata gibi sunulmaz.

`Model / Runtime` paneli aktif algılayıcıyı, sınıf profilini, güven eşiğini, takip/projeksiyon yaklaşımını ve veri kaynağı modunu gösterir. Bu panel, balon hedefleriyle yapılan entegrasyonun ileride yarışma sınıflarına aynı arayüz kontratıyla taşınabileceğini açıklar.

`Hedef / Angajman` paneli seçili hedef kimliği, sınıfı, güven değeri, yönü, göreli derinliği ve fire gate sonucunu gösterir. KTR demo ve güvenli geliştirme modlarında sonuç `NO PHYSICAL COMMAND` veya `FIRE_BLOCKED` olarak kalır.

`Scene Plan` paneli üstten görünümde FOV, hedef konumu ve güvenlik/no-go alanını özetler. İçindeki `2D Detection -> 3D Digital Twin Mapping` kartı, bbox merkezini, alan oranını, göreli derinliği, poz kaynağını ve 30 mm ofseti kısa şekilde açıklar.

`Replay & Evidence` paneli ekran görüntüsü klasörü, asset manifesti, kamera truth contractı ve projeksiyon contractı gibi kanıt çıktılarına bağlanır. Bu yapı test sonrası incelemeyi kolaylaştırır.

`Operator Log` paneli kamera kaynağı kararı, fixture seçimi, USB/Pico offline beklenen durumu, STL asset kararı, person safety durumu ve seri TX üretilmediği bilgisini sıralar.

Alt güvenlik şeridi sistem modunu kalıcı olarak gösterir: `DRY_RUN`, `physical_command_enabled=false`, `serial_tx_enabled=false`, `NO PHYSICAL COMMAND GENERATED`. Böylece operatör, sunum veya test sırasında arayüzün fiziksel komut üretmediğini sürekli görür.
