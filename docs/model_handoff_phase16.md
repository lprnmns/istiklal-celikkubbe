# Faz 16 - Vision Model Handoff

Bu fazın amacı, görüntü işleme ekibinden gelen model paketinin kod değişmeden sisteme alınması, doğrulanması, active model yapılması ve dry-run test/benchmark akışına bağlanmasıdır. Görüntü işleme algoritması, model eğitimi veya production inference kararı bu fazın kapsamı değildir.

## Model Paketi Sözleşmesi

Beklenen klasör yapısı:

```text
models/incoming/<model_package_name>/
  model.pt veya model.onnx
  metadata.json
  classes.yaml veya classes.json
  thresholds.json
  README.md
  sample_inputs/
  sample_outputs/
```

`metadata.json` model kimliğini, formatını, beklenen sınıfları, `class_id_to_name` eşlemesini, önerilen `imgsz/conf/iou` değerlerini ve `safety_note: advisory_only` bilgisini taşır.

`thresholds.json` default `conf`, `iou`, `max_det`, opsiyonel sınıf bazlı thresholdlar ve önerilen runtime preset bilgisini taşır.

## Doğrulama Kuralları

- Model dosyası yoksa paket active model yapılamaz.
- Metadata veya threshold eksikse import/doğrulama kontrollü hata üretir.
- Class mapping eksikse competition rehearsal readiness blocked kalır.
- Aynı `model_id/version` tekrar import edilirse kullanıcıya warning gösterilir.
- Her paketin SHA-256 checksum değeri hesaplanır.
- Model import/test/benchmark hiçbir fiziksel komut endpointine dokunmaz.

## UI Akışı

`/models` ekranı:

- Model Package Inventory
- Import Model Package
- Active Model
- Class Mapping Review
- Runtime Compatibility
- Safety Evidence

Vision ekranındaki Active Model Panel bu paket sistemiyle beslenir. Production model yoksa açık uyarı görünür:

`Production YOLO modeli yüklü değil. OpenCV daire algılayıcı yalnızca test adaptörüdür; yarışma modeli değildir.`

## Runtime Önerileri

Model metadata içindeki önerilen `imgsz/conf/iou/max_det` değerleri UI’da gösterilir. `Apply recommended settings` yalnızca vision runtime ayarlarını değiştirir; safety state, fire policy, hardware state veya physical command flags değişmez.

## KTR Arayüz Metni

KTR 4.3 export içine “Görüntü İşleme Model Paketi Arayüzü” bölümü eklenmiştir. Temel sınır:

Görüntü işleme modeli, komuta kontrol yazılımına yalnızca sınıf, güven skoru, konum ve zaman bilgisi içeren algılama metadatası sağlar; bu metadata tek başına fiziksel atış veya hareket komutu üretmez.

## Bilinçli Olarak Yapılmayanlar

- Production YOLO eğitimi yapılmadı.
- Yeni görüntü işleme algoritması geliştirilmedi.
- Motor, servo, tetik, STEP/DIR/PWM, GPIO veya fiziksel serial komut yolu eklenmedi.
- Model çıktısı decision/motion/fire fiziksel komutuna bağlanmadı.
