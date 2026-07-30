# Faz 9: Model Management, Dataset, Session Recording ve Replay

## Scope Ayrımı

Bu fazda arayüz/backend tarafı model yönetimi, kayıt, replay, annotation review ve YOLO export akışını sağlar. Production görüntü işleme algoritması, YOLO eğitimi, accuracy iyileştirme ve nihai inference kararları görüntü işleme ekibinin sorumluluğundadır.

OpenCV circle detector yalnızca test adapter'ıdır. Production model değildir ve fiziksel aksiyon üretmez.

## Model Management Mimarisi

Backend servisleri:

- `ModelRegistryService`: model metadata registry, active model seçimi, validation.
- `ModelUploadService`: güvenli upload/metadata kayıt yüzeyi.
- `InferenceAdapterService`: ortak inference sonucu formatı.
- `OpenCVCircleDetector`: test/demo adapter.

Model dosyaları `models/uploaded/<model_id>/` altında runtime çıktısı olarak tutulur ve Git'e alınmaz. Active model seçimleri `models/active/active_models.json` ile runtime state olarak saklanır.

## Model Flow

1. Vision ekibi `.pt`, `.onnx` veya `.yaml` dosyasını ve metadata bilgilerini verir.
2. UI `Models` sekmesinden model metadata kaydı yapar.
3. Backend dosya uzantısını, metadata alanlarını ve class listesini doğrular.
4. Operatör body, balloon, combined veya test adapter slotunu aktif seçer.
5. Test inference mock/snapshot/replay kaynakları üzerinde çalıştırılır.

Gerçek Ultralytics/ONNX adapter yoksa backend controlled warning döner; sistem crash etmez.

## Inference Adapter Interface

Ortak sonuç alanları:

- `frame_id`
- `source`: `live_camera`, `snapshot`, `replay`, `mock`, `uploaded_image`
- `model_id`
- `adapter`: `ultralytics`, `onnx`, `opencv_stub`, `mock`
- `detections`
- `latency_ms`, `preprocess_ms`, `inference_ms`, `postprocess_ms`
- `warnings`, `errors`
- `no_physical_command_generated=true`

Detection formatı hem pixel hem YOLO normalized bbox içerir.

## Session Recording

Session kayıtları `data/sessions/<session_id>/` altında tutulur:

- `session.json`
- `frames/`
- `snapshots/`
- `detections.jsonl`
- `color_decisions.jsonl`
- `decisions.jsonl`
- `operator_actions.jsonl`
- `annotations.jsonl`

Minimum kayıt davranışı snapshot, frame metadata, detection event, annotation ve operator action JSONL kayıtlarını kapsar.

## Scenario Metadata

Her session şu metadata ile etiketlenir:

- hedef tipi: `f16`, `helicopter`, `ballistic_missile`, `mini_micro_uav`, `unknown`
- takım: `enemy`, `friend`, `unknown`
- mesafe: `5`, `10`, `15`, `custom`
- lane, açı, renk profili, ışık, lens profili
- kamera çözünürlüğü, YOLO image size
- aktif model id listesi

## Replay Flow

Replay geçmiş session frame/snapshot metadata’sını kaynak olarak kullanır:

- load session
- play/pause/stop/step
- speed: 0.25x, 0.5x, 1x, 2x
- `replay.*` WebSocket eventleri

Replay source advisory'dir. Fiziksel motor/fire/servo/serial komutu üretilmez.

## Annotation Schema

Annotation kaydı:

- `annotation_id`
- `session_id`
- `frame_id`
- `image_path`
- `source`: manual/model_prediction/imported_yolo/replay_review
- object listesi

Object alanları class, bbox formatı, bbox, confidence, track id, balloon flag, team label, color decision ve operator verification bilgisini içerir.

## YOLO Export Formatı

Export Ultralytics düzeninde üretilir:

```text
dataset/
  data.yaml
  images/train
  images/val
  labels/train
  labels/val
  metadata.json
```

Export modları:

- `body_multiclass`: f16, helicopter, ballistic_missile, mini_micro_uav
- `balloon_singleclass`: balloon
- `combined_body_balloon`: body sınıfları + balloon
- `target_singleclass`: tek target sınıfı

Team/friend/enemy YOLO class değildir; metadata ve color pipeline çıktısı olarak kalır.

## Dataset Validation

Validation kontrolleri:

- image dosyası var mı
- label/bbox değerleri geçerli mi
- bbox normalized değerleri 0..1 aralığında mı
- class id geçerli mi
- duplicate frame var mı
- metadata eksikleri var mı
- active model metadata export metadata’sına yazıldı mı

## WebSocket Eventleri

- `model.uploaded`, `model.validated`, `model.activated`
- `model.test_started`, `model.test_completed`, `model.test_failed`
- `session.started`, `session.stopped`, `session.snapshot_saved`, `session.event_recorded`
- `dataset.export_started`, `dataset.export_completed`, `dataset.export_failed`, `dataset.validation`
- `replay.loaded`, `replay.playing`, `replay.paused`, `replay.stopped`, `replay.frame`
- `annotation.updated`

## UI Kullanım Akışı

Data Lab sekmeleri:

- Models
- Capture
- Sessions
- Replay
- Annotation Review
- YOLO Export
- Dataset Health

Vision ekranı aktif model/adaptör özetini gösterir. Dashboard Data Collection kartı session/model/export/health durumunu özetler.

## Safety Notları

- Default sistem: `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false`.
- Model test, replay ve dataset export fiziksel aksiyona bağlanmaz.
- OpenCV circle detector test adapter'dır, production model değildir.
- Gerçek motor/fire/servo/serial komutu yoktur.

## Saha Veri Toplama Önerileri

Eksik dağılımları kapatmak için session metadata disiplinli doldurulmalı:

- 5m/10m/15m mesafe
- hedef tipi
- friend/enemy renk örnekleri
- 3.6mm/8mm/12mm lens profilleri
- indoor LED/sunlight/low light/mixed ışık
- front/side/diagonal/top_pitch/bottom_pitch/partial_occlusion açılar

## Vision Ekibinden Beklenen Teslim Formatı

- model dosyası: `.pt`, `.onnx` veya adapter bilgisi
- class listesi ve class id mapping
- input size
- önerilen confidence ve IoU threshold
- framework bilgisi
- örnek inference çıktısı
- varsa preprocessing/postprocessing notları
