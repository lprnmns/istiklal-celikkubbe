# Phase 12 - Device Manager, Camera Source Manager and Vision Runtime Settings

## Neden Device Manager Gerekli?

Saha ortamında laptop kamerası, USB kamera, Pico 2, USB-serial dönüştürücü ve sanal serial portlar aynı anda görünebilir. Device Manager bu cihazları tek envanterde gösterir ve operatörün kamera ile Pico adayını karıştırmasını engeller.

Device Manager salt-okuma çalışır. Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya physical command output üretmez.

## Kamera mı Pico mu Ayrımı

Pico adaylığı sadece aday skorudur; doğrulama değildir.

- Serial kaynaklar: `serial.tools.list_ports`, `/dev/ttyACM*`, `/dev/ttyUSB*`
- Kamera kaynakları: `/dev/video*`, `/dev/v4l/by-id/*`, opsiyonel `v4l2-ctl`, opsiyonel OpenCV probe
- Pico candidate score: VID/PID, manufacturer, description, hwid ve device path üzerinden hesaplanır.
- Pico verified: sadece read-only telemetry içinde `device=pico2`, `firmware_version=telemetry-only-*` ve `physical_outputs_enabled=false` geldiğinde true olur.

## Stable Device Path / by-id Mantığı

`/dev/video0` ve `/dev/ttyACM0` reboot veya farklı takma sırası sonrası değişebilir. Bu yüzden UI mümkünse `/dev/v4l/by-id/*` ve `/dev/serial/by-id/*` stable path bilgisini gösterir.

## Kamera Seçimi

Camera Runtime Manager şu kaynakları destekler:

- `mock`
- `laptop`
- `usb`
- `video_file`
- `replay`

Gerçek kamera seçildiğinde backend camera probe çalıştırır. Kamera açılamazsa apply işlemi rollback yapar ve eski çalışan profile korunur.

## Kamera Çözünürlük/FPS/Format Ayarları

Runtime profile içinde:

- width / height / fps
- pixel format: `auto`, `MJPG`, `YUYV`
- stream width/height
- inference width/height
- lens profile
- ROI
- exposure/focus/white balance placeholder alanları

Bu ayarlar gerçek kamera için probe ile doğrulanır; mock profile her zaman güvenli kabul edilir.

## YOLO Runtime Ayarları

Vision Runtime Settings şunları yönetir:

- inference adapter: `mock`, `opencv_circle_test`, `ultralytics_yolo`
- active body/balloon model id
- device: `cpu`, `auto`, `cuda`
- imgsz, conf, iou, max_det
- classes filter
- half, agnostic NMS, frame skip, vid stride
- tracker settings
- body/balloon confidence thresholds
- latency budget ve target FPS

`cuda` varsayılan olarak kapalıdır. `ultralytics_yolo` seçimi için vision team tarafından model yüklenmiş olmalıdır.

## Görüntü İşleme Ekibi Model Yükleme Akışı

1. Data Lab > Models içinde model dosyası ve metadata eklenir.
2. Model validation çalıştırılır.
3. Active body/balloon/combined model slotu seçilir.
4. Vision Runtime Settings içinde adapter `ultralytics_yolo` yapılır.
5. `imgsz`, `conf`, `iou`, `max_det` gibi parametreler uygulanır.
6. Warmup/benchmark ile runtime uyumluluğu kontrol edilir.

Bu arayüz YOLO eğitimi veya production detection algoritması geliştirmez.

## OpenCV Test Adapter Sınırı

`opencv_circle_test` sadece UI ve replay/model-test akışını doğrulamak içindir. Production YOLO modeli yerine geçmez. UI’da açıkça “OpenCV circle detector is a test adapter only. Production model must be loaded by the vision team.” uyarısı gösterilir.

## Troubleshooting

- Permission denied: kullanıcı `video` veya `dialout` grubunda olmayabilir.
- `/dev/video` busy: kamera başka uygulama tarafından açık olabilir.
- Wrong camera selected: stable by-id path kullanılmalı.
- Pico candidate not found: USB kablo, BOOTSEL/firmware durumu ve `dmesg` kontrol edilmeli.
- Telemetry not received: telemetry-only firmware `main.py` yüklü olmayabilir.
- Model file missing: Model Registry metadata var ama dosya yoktur; UI warning gösterir.
- CPU FPS düşük: imgsz, frame_skip, vid_stride ve target FPS düşürülmelidir.
- CUDA unavailable: Phase 12 config içinde `allow_cuda=false`; CPU veya auto kullanılmalıdır.

## Safety Notları

- `hardware_enabled=false`
- `physical_command_enabled=false`
- `allow_physical_motion=false`
- `allow_physical_fire=false`
- Vision/model/camera ayarları fiziksel aksiyona bağlı değildir.
- Device scan ve runtime settings hiçbir physical command üretmez.
