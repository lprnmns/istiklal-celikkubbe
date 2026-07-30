# Dijital İkiz Kokpit Açıklaması

İSTİKLAL C2 Dijital İkiz Kokpiti, hava savunma prototipinin algılama, takip, güvenlik ve kanıt üretimi verilerini tek bir operatör ekranında birleştiren komuta-kontrol arayüzüdür. Kokpit; kamera HUD paneli, 3B dijital ikiz sahnesi, cihaz durumu, model çalışma zamanı, hedef/angajman özeti, sahne planı, tekrar/kanıt paneli, operatör logları ve güvenlik şeridinden oluşur.

Dijital ikiz katmanı, arayüz süslemesi olarak değil, açıklanabilirlik katmanı olarak eklenmiştir. Görüntü işleme hattından gelen hedef kutusu, sınıf etiketi, güven değeri ve normalize koordinatlar 3B sahneye aktarılır. Operatör, hedefin kamera görüş alanına göre nerede olduğunu, hedefin göreli derinlik bandını, kamera optik eksenini, namlu referans eksenini ve kamera-namlu ofsetini aynı anda görebilir.

Bu yapı, yalnızca kamera görüntüsüne bakan bir arayüzden daha fazla bağlam sağlar. Kamera-only arayüzde hedef kutusu görülebilir ancak sistemin hedefi 3B operasyonel sahnede nasıl yorumladığı açık değildir. Dijital ikiz kokpitinde hedef, görüş konisi ve referans eksenlerle birlikte gösterildiği için operatör hedefin sağ/sol/yukarı/aşağı konumunu ve güvenlik durumunu daha hızlı değerlendirebilir.

Uzak izleme konsepti açısından kokpit, gerçek cihazın yanında bulunmayan bir gözlemcinin sistem durumunu anlamasına yardımcı olur. Kamera kaynağı, Pico durumu, hedef tespiti, güvenlik kapıları ve kanıt dosyaları tek ekranda toplandığından saha testi sonrasında hakem veya ekip lideri sistemin hangi veriye dayanarak ne gösterdiğini izleyebilir.

Hakem değerlendirmesinde kokpit, sistem davranışını görsel ve metinsel olarak açıklama görevi görür. KTR demo modunda kullanılan fixture verisi açıkça `KTR FIXTURE - NOT LIVE` ve `evidence_truth=fixture` olarak işaretlenir. Böylece görselin canlı hedef kanıtı olmadığı, algılama-dijital ikiz bağlantısını açıklayan deterministik bir kanıt modu olduğu netleşir.

Güvenlik sınırı korunmuştur: bu kokpit fiziksel hareket veya atış komutu üretmez. KTR çıktılarında `physical_command_enabled=false`, `serial_tx_enabled=false` ve `no_physical_command_generated=true` alanları açıkça belirtilir.
