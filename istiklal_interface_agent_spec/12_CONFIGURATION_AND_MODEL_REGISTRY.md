# 12. Konfigürasyon ve Model Registry

## Config Yaklaşımı

Tüm ayarlar `config.yaml` üzerinden yönetilmelidir. UI config'i düzenler, backend schema ile doğrular.

## Config Örneği

```yaml
system:
  name: "ISTIKLAL Command Center"
  mode: "DISARMED"
  default_fire_policy: "NO_FIRE"

camera:
  source: 0
  width: 1920
  height: 1080
  fps: 60
  lens_profile: "8mm"
  exposure_auto: false
  white_balance_auto: false

vision:
  body_model: "models/body_yolo_v003.pt"
  balloon_model: "models/balloon_yolo_v001.pt"
  imgsz: 960
  body_conf: 0.35
  balloon_conf: 0.40
  iou: 0.5
  tracker: "bytetrack.yaml"
  stable_frames_required: 5
  max_lost_frames: 8

color:
  color_space: "HSV"
  friend_ranges:
    - h_min: 100
      h_max: 130
      s_min: 60
      v_min: 50
  enemy_ranges:
    - h_min: 0
      h_max: 12
      s_min: 60
      v_min: 50
  exclude_balloon: true
  decision_threshold: 0.55
  temporal_window: 5

pico:
  port: "/dev/ttyACM0"
  baudrate: 115200
  heartbeat_timeout_ms: 500
  protocol: "binary"

pins:
  pan_step: GP2
  pan_dir: GP3
  tilt_step: GP4
  tilt_dir: GP5
  driver_enable: GP6
  trigger_servo_pwm: GP10
  estop_in: GP14

motor:
  pan_steps_per_degree: 80.0
  tilt_steps_per_degree: 80.0
  max_speed: 1200
  acceleration: 300
  backlash_compensation_steps: 12
  deadband_px: 8

safety:
  require_armed: true
  require_estop_released: true
  require_enemy: true
  require_balloon: true
  require_valid_range: true
  require_stable_track: true
  no_fire_default: true

logging:
  path: "logs"
  jsonl: true
  save_overlay_video: false
```

## Validasyon Kuralları

- Confidence değerleri 0–1 arasında olmalı.
- `stable_frames_required >= 1`.
- Pinler çakışamaz.
- Model dosyası yoksa `SYSTEM_NOT_READY`.
- Safety `require_balloon: false` ise UI warning göstermeli.
- Pin değişiklikleri sadece `DISARMED`.

## Model Kartı

```yaml
model_name: body_yolo_v003
task: body_detection
classes:
  - f16
  - helicopter
  - ballistic_missile
  - mini_micro_uav
train_dataset: body_v003_train
val_dataset: body_v003_val
test_dataset: real_parkur_holdout
imgsz: 960
metrics:
  mAP50: 0.94
  mAP50_95: 0.78
  recall_15m: 0.86
  latency_ms_rtx4060: 11.2
known_failures:
  - extreme glare
  - partial occlusion by barrier
  - small drone at 15m under low light
created_at: "2026-05-07"
```

## UI Model Registry

- Model listesi
- Aktif model seçimi
- Metrik görüntüleme
- Known failures
- Model compare
- Rollback
- Model warm-up

## Ayar Değişiklik Logu

```json
{
  "ts": 1710000000.1,
  "user": "operator",
  "field": "vision.body_conf",
  "old": 0.35,
  "new": 0.30,
  "reason": "low light test"
}
```
