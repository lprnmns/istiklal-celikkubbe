# Dijital İkiz Kokpit Yönetici Özeti

İSTİKLAL C2 kokpiti, kamera görüntüsü, hedef tespiti, 3B dijital ikiz, güvenlik durumu ve kanıt panellerini tek bir operatör ekranında birleştiren komuta-kontrol arayüzüdür. Sistem, yalnızca kamera görüntüsü gösteren klasik bir arayüzden farklı olarak algılama çıktısını operatörün yorumlayabileceği mekansal bir sahneye dönüştürür.

Kamera tabanlı arayüzlerde operatör genellikle sadece hedef kutusunu ve güven değerini görür. Dijital ikiz katmanı ise aynı tespiti 3B sahne içinde kamera görüş konisi, kamera optik ekseni, namlu referans ekseni, hedef projeksiyon ışını ve 30 mm kamera-namlu ofseti ile birlikte gösterir. Böylece sistemin hedefi nerede gördüğü, hedefin görüş alanına göre konumu ve güvenlik kapılarının durumu daha anlaşılır hale gelir.

Bu fazdaki KTR demo modu, canlı hedef kanıtı değildir; `fixture` verisiyle çalışan deterministik bir açıklanabilirlik modudur. Amaç, hakemlere ve ekip üyelerine algılama bilgisinin dijital ikize nasıl aktarıldığını, operatörün hangi göstergelerle karar verdiğini ve sistemin fiziksel komut üretmeden nasıl güvenli şekilde doğrulanabildiğini göstermektir.

Dijital ikiz altyapısı, ileride gerçek USB kamera görüntüsü ve Pico telemetrisi bağlandığında aynı kokpit içinde canlı durumu gösterecek şekilde tasarlanmıştır. Bu entegrasyon yolu hazır tutulurken mevcut güvenlik sınırı korunur: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`.

KTR açısından değer önerisi; yazılım mimarisi, operatör ergonomisi, test kanıtı, güvenlik mimarisi ve özgün arayüz tasarımının tek bir açıklanabilir kokpit üzerinde birleştirilmesidir.
