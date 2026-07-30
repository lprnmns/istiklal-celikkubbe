# KTR Demo Senaryosu

Bu senaryo, İSTİKLAL C2 dijital ikiz kokpitinin hakemlere güvenli ve açıklanabilir şekilde gösterilmesi için hazırlanmıştır.

1. Operatör `/cockpit?ktr_demo=1` ekranını açar. Kokpit KTR demo modunda başlar ve üst barda `KTR DEMO`, `DISARMED`, `DRY_RUN`, `NO-FIRE`, `USB OFFLINE_EXPECTED`, `PICO OFFLINE_EXPECTED` ve `NO PHYSICAL COMMAND` etiketleri görünür.

2. Kamera HUD paneli fixture hedefini gösterir. Panelde `KTR FIXTURE - NOT LIVE` ve `evidence_truth=fixture` ibareleri bulunur. Bu ekran canlı hedef veya USB kamera kanıtı olarak sunulmaz; algılama-dijital ikiz bağlantısını açıklamak için deterministik fixture verisi kullanılır.

3. Hedef kutusu, sınıf etiketi, güven değeri, normalize hedef koordinatları ve göreli derinlik bilgisi dijital ikiz sahnesine aktarılır. Hedef kamerada sağ taraftaysa 3B FOV içinde de sağ tarafta görünür.

4. 3B dijital ikiz panelinde STL tabanlı cihaz görseli, kamera FOV konisi, kamera optik ekseni, namlu referans ekseni, hedef projeksiyon ışını ve 30 mm kamera-namlu ofseti birlikte gösterilir. Namlu referans ekseni fiziksel komut anlamına gelmez; yalnızca açıklama çizgisidir.

5. Alt operatör kartları cihaz, model/runtime, hedef/angajman, sahne planı, replay/evidence ve operatör loglarını özetler. Bu kartlar hakemlerin tek ekranda sistem durumunu okumasını sağlar.

6. Alt güvenlik şeridi `SYSTEM MODE: DRY_RUN`, `physical_command_enabled=false`, `serial_tx_enabled=false` ve `NO PHYSICAL COMMAND GENERATED` bilgilerini sürekli gösterir. Bu, demo sırasında fiziksel komut yolunun devre dışı olduğunu kanıtlar.

Aynı mimari, gerçek donanım bağlandığında USB kamera görüntüsünü ve Pico telemetrisini tüketebilir. Ancak bu geçiş ayrı hardware acceptance fazında yapılmalıdır. Phase 43 KTR paketi fiziksel hareket veya atış kontrolü içermez.
