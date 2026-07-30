# Ara Task 12.4 - Device Manager, Camera Source Manager ve Live Vision Runtime Settings

## Yapılanlar

- Device Manager backend servisi ve `/api/devices` endpoint seti eklendi.
- Serial, Pico candidate ve camera cihazları için envanter modeli oluşturuldu.
- Kamera runtime profile modeli ve `/api/camera/runtime/*` endpointleri eklendi.
- Vision/YOLO runtime settings modeli ve `/api/vision/runtime/*` endpointleri eklendi.
- Camera profile apply işlemi atomic/rollback davranışıyla kuruldu.
- Vision runtime ayarları model registry ile bağlandı; OpenCV circle detector test adapter açık uyarıyla kullanılabilir hale getirildi.
- Frontend’e `/devices` ekranı eklendi.
- Vision ekranına camera source/profile ve inference/YOLO runtime settings panelleri eklendi.
- Pico ekranı Device Manager Pico candidate verisini gösterecek şekilde güncellendi.
- Dashboard’a Device/Runtime kartı eklendi.
- Self-test’e device manager, camera runtime ve vision runtime step’leri eklendi.
- Topbar build bilgisi Phase 12 / build fallback formatına çekildi.

## Device Manager özeti

Device Manager şu kaynakları salt-okuma tarar:

- `serial.tools.list_ports`
- `/dev/ttyACM*`
- `/dev/ttyUSB*`
- `/dev/video*`
- `/dev/v4l/by-id/*`
- opsiyonel `v4l2-ctl`
- opsiyonel OpenCV camera probe

Her device için `device_id`, `device_path`, `stable_path`, `kind`, permission, busy/connected, candidate score, warning ve suggested action alanları döner.

Pico candidate detection aday skorudur; verified state değildir.

## Camera source/runtime özeti

Camera runtime profile şu alanları yönetir:

- source type: mock/laptop/usb/video_file/replay
- device id/path/stable path
- width/height/fps
- pixel format: auto/MJPG/YUYV
- stream size
- inference size
- lens profile
- ROI
- exposure/focus/white balance placeholder alanları

Gerçek kamera profile apply sırasında probe başarısız olursa rollback yapılır. Mock source güvenli default olarak kalır.

## YOLO runtime settings özeti

Vision runtime settings şu alanları yönetir:

- inference adapter: mock/opencv_circle_test/ultralytics_yolo
- active body/balloon model id
- device: cpu/auto/cuda
- imgsz/conf/iou/max_det
- classes filter
- half, agnostic NMS, frame skip, vid stride
- tracker ayarları
- body/balloon confidence threshold
- latency budget ve target FPS

`opencv_circle_test` sadece test adapter’dır. Production model görüntü işleme ekibi tarafından Model Registry’ye yüklenmelidir.

## Pico/device classification özeti

- Device Manager Pico candidate score üretir.
- Pico verified sadece read-only telemetry ile mümkündür.
- Gerçek Pico yoksa candidate bulunmayabilir; UI bunu warning olarak gösterir.
- Pico’ya komut gönderilmedi.

## UI ekranları özeti

- `/devices`: USB/Serial/Camera inventory, camera table, serial table, Pico candidate score, probe action.
- `/vision`: Camera source/runtime settings ve inference/YOLO runtime settings.
- `/pico`: Device Manager Pico candidate listesi ve candidate/verified ayrımı.
- `/`: Device/Runtime dashboard kartı.
- `/self-test`: yeni device/runtime hardware/vision/model step’leri.
- `/logs`: device/camera/vision runtime eventleri filtrelenebilir.

## Self-test entegrasyonu

Yeni step’ler:

- `device_manager_scan`
- `camera_source_selected`
- `camera_frame_probe`
- `camera_runtime_profile`
- `vision_runtime_settings`
- `active_model_or_adapter`
- `yolo_settings_safe`
- `pico_candidate_detection`

Acceptance run:

- Run ID: `selftest-4ab7aa7475`
- Status: `warning`
- Readiness: `demo_ready`
- Critical failures: `0`
- Warnings: `5`
- `no_physical_command_generated=true`

Warnings beklenen durumdur: gerçek Pico ve fiziksel kamera/model mevcut değil; mock/test adapter yolu güvenli kalır.

## Safety invariant kanıtı

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- `allow_physical_motion=false`
- `allow_physical_fire=false`
- Motor/servo/tetik/atış/STEP/DIR/PWM/GPIO output yok.
- Device scan, camera runtime ve vision runtime hiçbir physical command üretmez.

## Screenshot yolları

- `reports/screenshots/phase12_device_runtime_settings/01_devices_inventory.png`
- `reports/screenshots/phase12_device_runtime_settings/02_camera_source_selection.png`
- `reports/screenshots/phase12_device_runtime_settings/03_camera_runtime_profile.png`
- `reports/screenshots/phase12_device_runtime_settings/04_vision_yolo_runtime_settings.png`
- `reports/screenshots/phase12_device_runtime_settings/05_pico_candidates_from_device_manager.png`
- `reports/screenshots/phase12_device_runtime_settings/06_dashboard_device_runtime_cards.png`
- `reports/screenshots/phase12_device_runtime_settings/07_self_test_device_runtime_steps.png`
- `reports/screenshots/phase12_device_runtime_settings/08_logs_device_runtime_events.png`

## Test/build sonuçları

- Backend: `uv run pytest -q` geçti.
- Backend collection: `172 tests collected`.
- Frontend: `pnpm typecheck` geçti.
- Frontend: `pnpm build` geçti.
- Manual smoke:
  - `/` -> 200
  - `/devices` -> 200
  - `/pico` -> 200
  - `/vision` -> 200
  - `/self-test` -> 200
  - `/logs` -> 200
  - `/api/devices` -> 200
  - `/api/devices/cameras` -> 200
  - `/api/vision/runtime/status` -> 200
  - `/api/camera/runtime/status` -> 200

## Commit hashleri

- Runtime/settings commit: `feat: add device manager and live vision runtime settings` (hash final task yanitinda verildi)

## Bilinen eksikler

- Gerçek Pico yok; Pico verified acceptance tamamlanmadı.
- Gerçek kamera yoksa camera probe sadece no-camera/mock state gösterir.
- YOLO production adapter/model load görüntü işleme ekibi model tesliminden sonra gerçek runtime’da doğrulanacak.
- CUDA varsayılan olarak kapalıdır.
- v4l2 capability parse ortamda `v4l2-ctl` yoksa sınırlı fallback verir.

## Gerçek Pico geldiğinde yapılacak acceptance adımı

1. Pico 2’ye telemetry-only firmware yükle.
2. `/devices` üzerinden Pico candidate görünüyor mu kontrol et.
3. `/pico` üzerinden Connect Read-Only yap.
4. `PICO_READONLY_VERIFIED`, `telemetry_received=true`, `physical_outputs_enabled=false` doğrula.
5. Self-test çalıştır; `critical_failures=0` kalmalı.
6. Riskli komut blocker testlerini tekrar çalıştır.
