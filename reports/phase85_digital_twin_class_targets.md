# Phase 85 — Sınıf Bazlı 3B Hedef ve 14 cm Balon Sözleşmesi

Durum: yazılım/asset sözleşmesi tamamlandı; fiziksel kalibrasyon bekliyor.

## Kaynak ve browser varlıkları

`work/competition_target_sources/Modeller_Kil6t.zip` içindeki `Modeller.3mf`
doğrudan kaynak olarak saklandı. Bambu 3MF metadata'sındaki isimler kanonik
yarışma sınıflarıyla açıkça eşlendi; geometri üzerinden sınıf tahmini yapılmadı.

| Sınıf | Kaynak | Ölçülen referans span | Browser LOD üçgeni |
|---|---|---:|---:|
| `ballistic_missile` | `object_18.model` / Füze | 500 mm | 3,480 |
| `helicopter` | `object_19.model` / Helikopter | 583 mm | 6,350 |
| `f16` | `object_20.model` / F-16 | 500 mm | 14,780 |
| `mini_micro_uav` | `object_21.model` / Drone | 375 mm | 17,894 |

Çıktılar `frontend/public/assets/targets/` altındadır. Orijinal hedefler
yaklaşık 0.6–0.7 milyon üçgen olduğu için çoklu canlı hedef görüntüsünde CPU/GPU
darboğazı oluşturmamak adına deterministik vertex-cluster LOD kullanıldı.

## Konum ve menzil gerçeği

- Balon referans çapı `digital_twin.balloon_diameter_mm = 140.0` olarak
  kanonik config'e alındı.
- Her sınıf, bbox'un büyük kenarı ve kamera FOV'undan türetilen pinhole
  görsel mesafe tahmini kullanır.
- Bu değer `estimated_range_m`, `range_uncertainty_m` ve
  `range_source=class_bbox_pinhole_estimate` olarak yayınlanır.
- Değer kalibre edilmiş metrik menzil veya atış çözümü değildir. Hedef yönü,
  lens intrinsics ve 5/10/15 m saha kalibrasyonu tamamlanana kadar yalnız
  dijital ikiz görünümü içindir.

## Dijital ikiz davranışı

- Body detections artık Cockpit'ten dijital ikize gider.
- Sınıfa ait GLB hazır olduğunda yüklenir; yükleme sırasında sınıfa özgü proxy
  görünür.
- Kamera FOV'u kalibre edilmiş kamera anchor'ından çıkar; namlu rayı ayrı
  anchor'dan çıkar. Yaw/pitch dönüşümü hem model, hem FOV, hem hedef ışını için
  ortak kinematik bazdadır.
- Bu dilim salt-okunurdur: fiziksel komut, seri write veya fire yetkisi eklenmedi.

## HIL-15 öncesi yazılım doğrulaması

- Frontend typecheck ve production build geçti.
- Phase 31/32, 35, 38, 45, 47, 54, 55, 56, 83, 84, 85 kontrat testleri geçti.
- Tam fiziksel kabul, Pico telemetri, gerçek kamera intrinsics ve 5/10/15 m
  saha referansları gelmeden iddia edilmez.
