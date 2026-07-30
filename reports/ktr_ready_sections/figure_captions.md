# KTR Şekil Altyazıları

**Şekil 1. İSTİKLAL C2 dijital ikiz kokpiti.** Kamera HUD çıktısı, hedef tespit kutusu, 3B dijital ikiz projeksiyonu, güvenlik durumu ve operatör kanıt panelleri tek ekranda sunulmaktadır. Görsel KTR demo fixture modundadır; fiziksel komut üretilmemiştir.

**Şekil 2. KTR demo modu truth etiketleri.** Kokpit ekranı fixture hedef kullandığını `KTR FIXTURE - NOT LIVE` ve `evidence_truth=fixture` alanlarıyla açıkça belirtir. Bu mod canlı hedef veya USB kamera kanıtı değildir.

**Şekil 3. 3B dijital ikiz sahnesi.** STL türevi dijital ikiz, kamera FOV konisi, kamera optik ekseni, namlu referans ekseni, 30 mm kamera-namlu ofseti ve hedef projeksiyon ışını aynı sahnede gösterilmektedir.

**Şekil 4. Kamera HUD fixture görünümü.** Hedef kutusu, hedef merkezi, normalize hedef koordinatları, güven değeri ve kaynak doğruluğu bilgisi kamera HUD katmanında gösterilir. Görsel, gerçek kamera kanıtı olarak sunulmaz.

**Şekil 5. Operatör kanıt kartları.** Cihaz durumu, model/runtime bilgisi, hedef/angajman özeti, sahne planı, replay/evidence bağlantıları ve operatör logları kısa kartlar halinde sunulur.

**Şekil 6. 2B tespit bilgisinin 3B dijital ikize aktarımı.** Bbox merkezi, bbox alan oranı, göreli derinlik, poz kaynağı ve 30 mm ofset bilgileri açıklanabilirlik kartında özetlenir. Bu gösterim fiziksel atış çözümü değil, read-only durum farkındalığı katmanıdır.

Tüm şekiller için güvenlik notu: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`.
