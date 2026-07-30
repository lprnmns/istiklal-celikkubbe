# Güvenlik Katmanları ve Komut Sınırı

İSTİKLAL C2 arayüzünde güvenlik, yalnızca tek bir yazılım kontrolüne bırakılmamıştır. Kokpit, güvenlik durumunu görünür hale getiren ve geliştirme/test aşamasında fiziksel komut üretimini engelleyen çok katmanlı bir yaklaşım kullanır.

Mevcut KTR evidence modunda sistem `DISARMED`, `DRY_RUN` ve `NO_FIRE` durumundadır. Bu durum, arayüzdeki hedef ve angajman görsellerinin yalnızca açıklama ve kanıt amaçlı olduğunu belirtir. Fiziksel hareket veya atış komutu üretilmez.

Temel güvenlik invariantları şunlardır:

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

Bu alanlar raporlarda, contract dosyalarında, API çıktılarında ve ekran görüntülerinde korunur. Phase 43 kapsamında motor, servo, tetik, GPIO, PWM, STEP/DIR veya hardware-enable yolu eklenmemiştir.

Person safety gate, insan/person sınıfı algılandığında angajman durumunu bloke eden ek bir yazılım güvenlik katmanıdır. Bu katman acil stop, operatör gözetimi veya mekanik güvenlik önlemlerinin yerine geçmez; bunlara ek bir yazılım kontrolüdür.

Kamera kanıtı da açık şekilde ayrılır. Fixture modundaki görüntüler canlı kamera kanıtı değildir ve `evidence_truth=fixture` olarak işaretlenir. Laptop kamera geliştirme görüntüleri USB kamera kabul testi yerine geçmez. USB kamera bağlı değilse `OFFLINE_EXPECTED`, Pico bağlı değilse `PICO OFFLINE_EXPECTED` olarak gösterilir.

Bu yaklaşım güvenli geliştirme sağlar. Donanım her zaman bağlı olmak zorunda olmadan arayüz, dijital ikiz, kanıt ve güvenlik davranışları doğrulanabilir. Hakem açısından ise sistemin hangi veriyi gerçek, hangi veriyi fixture veya replay olarak sunduğu açıkça görüldüğü için güven ve izlenebilirlik artar.
