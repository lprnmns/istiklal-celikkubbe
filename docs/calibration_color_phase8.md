# Faz 8 Kamera Kalibrasyon ve Renk Ayarları

## Amaç

Bu faz kamera/lens kalibrasyonu, FOV tabanlı piksel tahmini ve HSV tabanlı dost/düşman renk ayarı için backend servisleri ile frontend ekranlarını ekler. Çıktılar advisory metadata niteliğindedir.

Güvenlik sınırı değişmedi:

- Sistem varsayılanı `DISARMED + NO_FIRE + dry_run=true`.
- Renk kararı fiziksel motor, servo veya fire komutuna bağlanmaz.
- Vision/color çıktısı karar motoruna sadece konservatif metadata olarak okunabilir.

## Kamera/Lens Kalibrasyon Modeli

Kalibrasyon profili şu alanları taşır:

- `camera_id`, `camera_name`
- `lens_profile`: `3.6mm`, `8mm`, `12mm`, `varifocal_custom`, `unknown`
- `resolution_width`, `resolution_height`, `fps`
- `camera_height_cm`, `target_height_cm`, `table_height_cm`
- `hfov_deg`, opsiyonel `vfov_deg`
- `distortion_enabled`, `homography_enabled`
- `calibration_status`: `not_started`, `partial`, `valid`, `invalid`

Varsayılan değerler placeholder’dır. UI’da field calibration required uyarısı gösterilir.

## Parkur Mesafeleri

Yarışma referans mesafeleri:

- 5 m
- 10 m
- 15 m

Varsayılan fiziksel referanslar:

- hedef yüksekliği: 130 cm
- sistem masa yüksekliği: 60 cm
- kamera yüksekliği: 60 cm

Kalibrasyon point modeli world/image eşlemesi tutar:

- `world_x_m`, `world_y_m`
- `image_x_px`, `image_y_px`

Bu fazda homography hesaplama güvenli placeholder seviyesindedir. En az 4 nokta varsa ve `homography_enabled=true` ise identity matrix döndürülür; gerçek geometrik homography optimizasyonu sonraki faza bırakılmıştır.

## FOV/Piksel Tahmin Mantığı

Endpoint:

- `POST /api/calibration/fov-estimate`

Formül:

```text
visible_width_m = 2 * distance_m * tan(hfov_deg / 2)
object_width_px = object_width_m / visible_width_m * image_width_px
```

Threshold:

- `>= 120 px`: `good`
- `60-119 px`: `marginal`
- `< 60 px`: `poor`

Bu panel lens seçimi ve saha doğrulaması için yardımcıdır.

## Renk Sınıflandırıcı

Varsayılan color space `HSV`’dir. LAB ayarları bu fazda placeholder/toggle olarak tutulur.

Config alanları:

- enemy/friend HSV aralıkları
- `saturation_min`
- `value_min`
- `min_body_pixels`
- `decision_threshold`
- `temporal_window`
- `required_consistent_frames`
- `balloon_mask_enabled`
- balloon HSV aralıkları
- `morphology_kernel`

Team değerleri:

- `enemy`
- `friend`
- `unknown`

## Kırmızı Balon Maskesi

Kritik kural: balon rengi dost/düşman kararına dahil edilmez.

Davranış:

- `balloon_mask_enabled=true` default.
- Balloon bbox varsa body crop içindeki balon alanı maskelenmiş kabul edilir.
- Balloon bbox yoksa bu fazda HSV tabanlı opsiyonel mask sadece mock/preview seviyesinde temsil edilir.
- Mask uygulanmazsa sonuç `balloon_mask_not_applied` warning’i üretir.

## Color Decision Schema

Renk sonucu şu alanları taşır:

- `frame_id`
- `detection_id`
- `body_crop_bbox`
- `balloon_mask_applied`
- `body_pixel_count`
- `enemy_pixel_ratio`
- `friend_pixel_ratio`
- `unknown_pixel_ratio`
- `decision`
- `confidence`
- `blocking_warnings`
- `debug_masks_available`
- `updated_at`

## API Endpointleri

Calibration:

- `GET /api/calibration/status`
- `GET /api/calibration/config`
- `PUT /api/calibration/config`
- `POST /api/calibration/points`
- `DELETE /api/calibration/points/{id}`
- `POST /api/calibration/compute`
- `POST /api/calibration/fov-estimate`
- `POST /api/calibration/reset`

Color:

- `GET /api/color/config`
- `PUT /api/color/config`
- `POST /api/color/classify-sample`
- `GET /api/color/latest`
- `POST /api/color/reset`
- `POST /api/color/preview-mask`

## WebSocket Eventleri

- `calibration.status`
- `calibration.updated`
- `calibration.warning`
- `color.config_updated`
- `color.classification`
- `color.warning`
- `color.mask_preview`

## UI Kullanım Akışı

`/calibration`:

- kamera/lens profilini gör
- çözünürlük, FPS, yükseklik ve HFOV değerlerini düzenle
- 5m/10m/15m piksel tahminlerini incele
- kalibrasyon noktası ekle/sil
- homography status ve warning panelini kontrol et

`/color`:

- enemy/friend HSV hue aralıklarını slider ile ayarla
- saturation/value/min pixel/threshold değerlerini düzenle
- balon maskesini aç/kapat
- mock enemy/friend/unknown sample çalıştır
- mask preview ve warning durumunu kontrol et

Vision sayfasında body detection tablosuna advisory color decision alanı eklenmiştir.

## Safety Notları

- Renk kararı fire veya motion komutu üretmez.
- Friend kararı decision engine tarafından `NO_FIRE` olarak okunabilir.
- Unknown kararı `FIRE_READY` için yeterli değildir.
- Hardware command path bu fazda değişmedi.

## Bilinçli Olarak Yapılmayanlar

- Gerçek OpenCV crop/mask pipeline tam uygulanmadı.
- Gerçek homography çözümü yapılmadı.
- Dataset/replay entegrasyonu yapılmadı.
- Kalibrasyon profilleri kalıcı profile registry’ye yazılmadı.
- Renk kararı fiziksel aksiyona bağlanmadı.
