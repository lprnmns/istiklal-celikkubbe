# 06 — KTR Bölüm Taslakları: Digital Twin ve Bütünleşik Sistem Anlatımı

Bu dosyadaki metinler KTR’ye doğrudan yapıştırılacak nihai metin değildir. 30 sayfa sınırı nedeniyle seçilerek, sıkıştırılarak ve görsellerle desteklenerek kullanılmalıdır.

## 4.1 Mekanik Tasarım için taslak

Sistemin mekanik mimarisi, hedefin kamera görüntüsü üzerinde tespit edilmesinden sonra iki eksenli yönelim sağlayacak şekilde pan/tilt yapıda tasarlanmıştır. Taban modülü yatay eksende yönelimi, üst taşıyıcı modül ise dikey eksende hedef hizalamasını sağlar. Kamera ve atış ekseninin aynı mekanik referans üzerinde konumlandırılması, görüntü işleme çıktısının mekanik yönelim komutlarına daha tutarlı çevrilmesini amaçlar.

Mekanik tasarım yalnızca üretim için değil, aynı zamanda operatör arayüzündeki dijital ikiz temsilinin de temelidir. CAD model; sabit taban, yatay döner gövde, dikey taşıyıcı, kamera yuvası ve tetik/servo görsel referansı gibi alt parçalara ayrılarak yazılım arayüzünde gerçek zamanlı telemetriyle ilişkilendirilecek şekilde düzenlenmiştir. Bu sayede mekanik sistemin anlık yönelimi, operatöre 3B model üzerinde gösterilebilir.

Mekanik tasarım sürecinde servis edilebilirlik, kablo yönlendirme, kamera erişimi, motor eksenlerinin doğrulanması ve yön kalibrasyonu dikkate alınmıştır. Özellikle motor yönlerinin montaj değişikliklerinden etkilenebilmesi nedeniyle yazılım tarafında dinamik yön kalibrasyon arayüzü tasarlanmıştır. Bu yaklaşım, mekanik tolerans ve montaj farklılıklarının yazılım üzerinden izlenebilir ve doğrulanabilir hale getirilmesini sağlar.

## 4.2 Elektronik, Algoritma ve Yazılım Tasarımı için taslak

Sistemin yazılım mimarisi kamera, görüntü işleme, hedef seçimi, takip kontrolü, Pico/aktüatör haberleşmesi, güvenlik kontrolü, olay kaydı ve operatör arayüzü katmanlarından oluşur. Kamera görüntüsü görüntü işleme katmanında işlenerek hedef sınıfı, güven skoru ve görüntü düzlemindeki hedef kutusu elde edilir. Bu çıktı takip katmanında hedef merkezi ile görüntü merkezi arasındaki hata değerine çevrilir ve mekanik yönelim için takip kontrol girdisi olarak kullanılır.

Görüntü işleme tarafında mevcut testlerde balon hedefi kullanılmaktadır. Yarışma senaryosunda eğitilecek YOLO modeli, aynı arayüz kontratı üzerinden dört hedef sınıfını destekleyecek şekilde sisteme entegre edilecektir. Bu nedenle yazılımda hedef temsili sınıf-bağımsız tasarlanmıştır: her hedef `class_id`, `class_label`, `confidence`, `bbox`, `track_id` ve opsiyonel 3B görsel varlık bilgisi ile temsil edilir.

Sistemde ayrıca telemetry-driven digital twin katmanı bulunmaktadır. Bu katman motor yönelimleri, hedef tespiti, takip durumu, güvenlik kilitleri ve angajman olaylarını gerçek zamanlı olarak 3B arayüzde gösterir. Dijital ikiz fiziksel komut üretmez; mevcut kontrol ve güvenlik mantığından gelen durum bilgisini operatöre anlaşılır şekilde sunar. Böylece yazılım yalnızca hedef takip eden bir kontrol döngüsü değil, aynı zamanda kararların geriye dönük incelenebildiği kanıt üreten bir sistem haline gelir.

## 4.3 Arayüzler için taslak

Sistemin arayüzleri yalnızca kullanıcı ekranından ibaret değildir. Kamera arayüzü, görüntü işleme/yapay zekâ arayüzü, takip kontrol arayüzü, Pico/serial haberleşme arayüzü, frontend-backend arayüzü, operatör kokpiti ve rapor/evidence export arayüzü ayrı ayrı tanımlanmıştır.

Operatör kokpiti, kamera görüntüsünü ve dijital ikiz görünümünü birlikte sunar. Kamera paneli hedef tespit kutusunu, takip merkezini ve gecikme değerlerini gösterirken; dijital ikiz paneli fiziksel sistemin pan/tilt yönelimini, hedefin yaklaşık sahne temsilini, güvenlik kilitlerini ve olay zaman çizelgesini gösterir. Böylece operatör yalnızca kameranın ne gördüğünü değil, sistemin bu görüntüyü nasıl yorumladığını ve mekanik olarak nereye yöneldiğini de izleyebilir.

Backend ile frontend arasındaki digital twin state kontratı; cihaz yönelimi, kamera durumu, hedef bilgisi, takip durumu, angajman durumu ve güvenlik durumunu tek bir normalize mesaj yapısında taşır. Bu yapı sayesinde arayüz, görüntü işleme modeli balondan yarışma hedef sınıflarına geçtiğinde de değişmeden çalışabilecek şekilde tasarlanmıştır.

## 4.4 Sistem İşleyiş Senaryoları için taslak

Sistem başlatıldığında önce kamera, Pico bağlantısı, güvenlik kapıları ve yazılım servisleri kontrol edilir. Kamera görüntüsü alındıktan sonra görüntü işleme modeli hedef adaylarını üretir. Hedef seçimi yapıldığında takip durumu aktif hale gelir ve hedef merkezi ile görüntü merkezi arasındaki hata değeri takip kontrol katmanına aktarılır. Sistem hedefi merkezlemeye çalışırken operatör kokpitinde hem kamera görüntüsü hem de 3B dijital ikiz eş zamanlı güncellenir.

Angajman kararı yalnızca hedefin tespit edilmesine bağlı değildir. Fire gate, E-stop, donanım hazır durumu, takip kararlılığı ve sistem modu birlikte değerlendirilir. Koşullar sağlanmadığında sistem angajmanı bloklar ve arayüzde bloklama sebebi gösterilir. Koşullar sağlandığında ise angajman olayı zaman damgası ile kaydedilir ve replay sistemine aktarılır.

Hata durumlarında sistem güvenli duruma geçer. Kamera kaybı, Pico bağlantı hatası, hedef kaybı, yüksek gecikme, komut kuyruğu birikmesi veya acil stop durumunda angajman engellenir. Bu olaylar hem anlık kokpitte hem de rapor/evidence exportlarında görünür hale getirilir.

## 5 Test için taslak

Sistem testleri üç seviyede yürütülür: yazılım-fixture testleri, donanım bağlantı testleri ve canlı görev testleri. Yazılım-fixture testlerinde gerçek cihaz olmadan digital twin state kontratı, replay timeline, hedef projection ve arayüz fallback davranışları doğrulanır. Donanım bağlantı testlerinde USB kamera seçimi, gerçek frame capture, Pico port discovery ve telemetry okuma test edilir. Canlı görev testlerinde ise hedef tespit, takip, yönelim, güvenlik kapıları ve angajman olayları uçtan uca değerlendirilir.

Digital twin replay özelliği test sürecinde önemli bir kanıt mekanizmasıdır. Bir görev koşusunda oluşan hedef tespiti, takip, yönelim, güvenlik ve angajman olayları kaydedilerek daha sonra aynı sırayla tekrar oynatılabilir. Bu sayede test sonuçları yalnızca sözlü açıklama veya tek ekran görüntüsü ile değil, zaman damgalı olay dizisiyle desteklenir.

## 6 Güvenlik için taslak

Sistemde güvenlik çok katmanlı olarak ele alınmıştır. Acil stop, fire gate, hardware enable, sistem modu, takip kararlılığı ve cihaz bağlantı durumu birlikte değerlendirilir. Herhangi bir kritik koşul sağlanmadığında sistem angajmanı engeller ve bloklama sebebini operatör arayüzünde gösterir.

Dijital ikiz katmanı fiziksel komut üretmeyen salt-okunur bir gözlem katmanı olarak tasarlanmıştır. Bu katman motor, servo, GPIO, PWM veya fire komutu göndermez; yalnızca mevcut kontrol yazılımı ve telemetri katmanından gelen durum bilgisini görselleştirir. Böylece operatörün durum farkındalığı artarken fiziksel komut yetkisi dağılmaz.

## 7 Tecrübe için taslak

Geliştirme sürecinde kamera aygıt seçimi, Pico erişim izinleri, gerçek kamera ile test görüntüsü ayrımı ve motor yön kalibrasyonu gibi problemlerle karşılaşılmıştır. Bu sorunlar, sistemin daha sağlam hale gelmesini sağlayacak şekilde ayrı teşhis ve acceptance adımlarına dönüştürülmüştür. Örneğin USB kamera ile dahili kamera ayrımı netleştirilmiş, direction calibration simulator ile motor yönlerinin montaj sonrası operatör gözlemiyle doğrulanabileceği bir yapı hazırlanmıştır.

## 8 Zaman, Bütçe ve Risk için taslak

Başlıca teknik riskler; YOLO modelinin yarışma sınıflarında yeterli doğruluğa ulaşmaması, kamera cihaz seçim hatası, mekanik eksen tersliği, Pico bağlantı/izin problemleri, takip gecikmesi ve güvenlik kapılarının yanlış konfigürasyonudur. Bu riskler için fixture test, clean-room verification, direction calibration, hardware acceptance ve replay evidence mekanizmaları planlanmıştır.

## 9 Özgünlük için taslak

Sistemin özgün tarafı yalnızca mekanik gövdenin takım tarafından tasarlanması değildir. Sistem; gerçek zamanlı telemetriye bağlı dijital ikiz kokpiti, hedef sınıfından bağımsız 3B varlık gösterimi, olay tabanlı replay kanıtı, dinamik motor yön kalibrasyonu ve güvenlik durumunu görünür kılan evidence-first arayüz yaklaşımıyla öne çıkmaktadır.

Dijital ikiz arayüzü, operatöre kameranın gördüğü hedefi, mekanik sistemin yönelimini, takip durumunu, güvenlik kilitlerini ve angajman olaylarını tek bir bütünleşik ekranda sunar. Bu yaklaşım, sistemin yalnızca çalışmasını değil, neden ve hangi durumda çalıştığını da görünür kılar.
