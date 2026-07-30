# KTR Scoring Alignment Matrix

| KTR satırı | Mevcut kanıt | Dijital ikiz katkısı | Güvenlik/kanıt katkısı | Eksik / doğrulanacak | Önerilen şekil/tablo |
| --- | --- | --- | --- | --- | --- |
| Project Summary | Phase 42 screenshotları, executive summary | Sistemi kamera-only arayüzden açıklanabilir C2 kokpitine taşır | `NO PHYSICAL COMMAND GENERATED` görünür | Final saha test sonuçları | Kokpit tam ekran görseli |
| System Block Diagram | Phase 31-36 raporları, protocol contract | Kamera -> algılama -> dijital ikiz -> operatör akışını gösterir | Read-only state ve telemetry-first yaklaşım | Canlı telemetry acceptance | Veri akış diyagramı |
| Mechanical Design | STL asset raporları, 30 mm ofset | CAD/STL model arayüzde kullanılır | Ofset görseldir, komut üretmez | Kamera/namlu anchor ölçüm doğrulaması | STL-derived twin ve ofset figürü |
| Hardware Design | Pico protocol v1, offline expected state | Pico telemetrisi bağlandığında pozu gösterecek yapı hazır | Serial TX kapalı | Gerçek Pico telemetry acceptance | Telemetry status tablosu |
| Software Design | Digital twin state, projection contracts, cockpit UI | 2B bbox -> 3B sahne mapping ve operatör panelleri | Fixture/live ayrımı, person safety gate | Production competition model validation | Projection mapping tablosu |
| Method | Spatial projection raporları, KTR demo senaryosu | Hedef konumu, FOV, eksenler ve göreli derinlik açıklanır | Metrik menzil overclaim yok | Kalibre menzil veya saha ölçüm datası | Bbox-to-scene açıklama kartı |
| Time/Budget/Risk | Safety boundary, offline hardware notes | Donanım yokken geliştirme ve kanıt üretimi mümkün | Offline expected, dry-run, no-TX | Gerçek donanım test planı tarihleri | Risk ve acceptance checklist |
| Organization and References | Evidence index, figure captions | Hakem ve ekip için izlenebilir kanıt paketi | Her kanıtta truth/safety notu | Final video/log arşivi | Evidence index tablosu |

Genel not: Bu Phase 43 paketi sunum ve rapor kanıtıdır. Fiziksel hareket/atış kabulü ayrı saha prosedürüyle doğrulanmalıdır.
