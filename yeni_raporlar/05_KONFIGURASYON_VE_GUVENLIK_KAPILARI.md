# 05 — Konfigürasyon Sistemi ve Güvenlik Kapıları

> config.yaml yapısı, Pydantic doğrulama zincirleri, 17 güvenlik kapısı detayı.

---

## 1. config.yaml Yapısı (240 satır)

Dosya: `config/config.yaml`

### 1.1 system
```yaml
system:
  mode: DISARMED              # Sistem başlangıç modu (değiştirilemez)
  fire_policy: NO_FIRE         # Ateş politikası (değiştirilemez)
  dry_run: true                # Kuru çalışma (değiştirilemez)
  hardware_enabled: false      # Donanım devre dışı
  development_mode: true       # Geliştirme modu
```

### 1.2 hardware
```yaml
hardware:
  transport_mode: mock         # mock | real_readonly
  physical_command_enabled: false
  allow_physical_motion: false
  allow_physical_fire: false
  real_serial_enabled: false
```

### 1.3 camera
```yaml
camera:
  camera_mode: mock            # mock | image | webcam
  camera_source: mock_camera_placeholder
  stream_enabled: true
  stream_width: 640
  stream_height: 480
  stream_fps: 15
```

### 1.4 vision
```yaml
vision:
  vision_mode: mock            # mock | yolo
  body_model_path: null
  balloon_model_path: null
  body_conf_threshold: 0.4
  balloon_conf_threshold: 0.35
  model_loading_required: false
  overlay_coordinate_format: pixel
```

### 1.5 pico
```yaml
pico:
  port: null
  baudrate: 115200
  heartbeat_interval_ms: 500
  heartbeat_timeout_ms: 3000
```

### 1.6 serial
```yaml
serial:
  transport_mode: mock         # mock | real_readonly
  protocol: json
  real_serial_enabled: false
```

### 1.7 pins (GPIO Pin Profili)
```yaml
pins:
  profile_name: default_v1
  assignments:
    pan_step: GP2
    pan_dir: GP3
    tilt_step: GP4
    tilt_dir: GP5
    trigger_servo_pwm: GP6
    estop_in: GP7
    pan_limit_left: GP8
    pan_limit_right: GP9
    tilt_limit_up: GP10
    tilt_limit_down: GP11
    driver_enable: GP12
```

### 1.8 motor
```yaml
motor:
  steps_per_degree: 200
  max_speed_dps: 90.0
  acceleration_dps2: 180.0
  pan_gear_ratio: 1.0
  tilt_gear_ratio: 1.0
```

### 1.9 motion
```yaml
motion:
  dry_run: true
  real_motion_enabled: false
  pan_min_deg: -90.0
  pan_max_deg: 90.0
  tilt_min_deg: -45.0
  tilt_max_deg: 45.0
  jog_step_deg: 1.0
  tracking_gain_x: 0.05
  tracking_gain_y: 0.05
  scan_speed_dps: 15.0
  scan_range_deg: 60.0
```

### 1.10 safety
```yaml
safety:
  no_fire_default: true
  default_fire_policy: NO_FIRE
  require_operator_confirm: true
  stable_frames_required: 5
```

### 1.11 decision
```yaml
decision:
  range_rules:
    f16: { min_m: 5, max_m: 25 }
    helicopter: { min_m: 3, max_m: 15 }
    ballistic_missile: { min_m: 8, max_m: 30 }
    mini_micro_uav: { min_m: 2, max_m: 10 }
  forbidden_zones: []
```

### 1.12 color
```yaml
color:
  color_space: HSV
  enemy_hsv_ranges: [[0, 100, 100, 10, 255, 255], [170, 100, 100, 180, 255, 255]]
  friend_hsv_ranges: [[100, 100, 100, 130, 255, 255]]
  saturation_min: 80
  value_min: 80
  decision_threshold: 0.55
  balloon_mask_enabled: true
  balloon_hsv_ranges: [[0, 0, 200, 180, 30, 255]]
```

---

## 2. Pydantic Doğrulama Zincirleri

`backend/app/schemas/config.py` (441 satır) — Her alt-model `model_validator` ile güvenlik kısıtlarını zorlar.

### SystemConfig validator
```python
@model_validator(mode="after")
def validate_disarmed_default(self):
    if self.mode != "DISARMED":
        raise ValueError("System mode must be DISARMED at startup")
    if not self.dry_run:
        raise ValueError("dry_run must be true at startup")
    return self
```

### HardwareConfig validator
```python
@model_validator(mode="after")
def validate_hardware_disabled(self):
    if self.physical_command_enabled:
        raise ValueError("physical_command_enabled must be false")
    if self.allow_physical_motion:
        raise ValueError("allow_physical_motion must be false")
    if self.allow_physical_fire:
        raise ValueError("allow_physical_fire must be false")
    return self
```

### SafetyConfig validator
```python
@model_validator(mode="after")
def validate_no_fire_default(self):
    if not self.no_fire_default:
        raise ValueError("no_fire_default must be true")
    if self.default_fire_policy != "NO_FIRE":
        raise ValueError("default_fire_policy must be NO_FIRE")
    return self
```

### DecisionConfig validator
```python
@model_validator(mode="after")
def validate_range_rules(self):
    required = {"f16", "helicopter", "ballistic_missile", "mini_micro_uav"}
    if not required.issubset(set(self.range_rules.keys())):
        raise ValueError(f"range_rules must include: {required}")
    return self
```

Bu validator'lar sayesinde **config.yaml'da güvenlik değerleri değiştirilse bile uygulama başlamaz**.

---

## 3. 17 Güvenlik Kapısı Detayı

`backend/app/services/decision_engine.py` → `evaluate()` metodu.

### Sistem Kapıları (5)

| # | Kapı | Koşul | Fail Durumu |
|---|------|-------|-------------|
| 1 | `system_armed` | `runtime.force_armed == True` | Sistem arm edilmemiş |
| 2 | `dry_run` | `config.system.dry_run == True` | Dry-run kapalı → tehlike |
| 3 | `hardware_enabled` | `config.system.hardware_enabled == True` | Donanım etkin değil |
| 4 | `estop_released` | `pico.telemetry.estop_state != PRESSED` | E-stop basılı |
| 5 | `pico_heartbeat` | `pico.heartbeat_age_ms < timeout` | Pico iletişim yok |

### Seri/Donanım Kapıları (2)

| # | Kapı | Koşul | Fail Durumu |
|---|------|-------|-------------|
| 6 | `serial_ok` | `serial.status.connection_state != FAULT` | Seri hata |
| 7 | `pico_connected` | `pico.connection_status == CONNECTED` | Pico bağlı değil |

### Hareket Kapıları (5)

| # | Kapı | Koşul | Fail Durumu |
|---|------|-------|-------------|
| 8 | `motion_soft_limits` | pozisyon soft limit içinde | Limit aşımı |
| 9 | `motion_estop` | hareket e-stop yok | E-stop aktif |
| 10 | `motion_fault_clear` | motion_state != FAULT | Motor hatası |
| 11 | `motion_driver` | driver_enabled == True | Sürücü kapalı |
| 12 | `motion_dry_run` | motion.dry_run == True | Gerçek hareket |

### Algılama Kapıları (5)

| # | Kapı | Koşul | Fail Durumu |
|---|------|-------|-------------|
| 13 | `vision_running` | vision pipeline çalışıyor | Vision kapalı |
| 14 | `body_detected` | en az 1 body detection var | Hedef yok |
| 15 | `balloon_detected` | en az 1 balloon detection var | Balon yok |
| 16 | `enemy_target` | renk=enemy + conf > threshold | Dost/belirsiz |
| 17 | `range_valid` | mesafe min-max aralığında | Menzil dışı |

### Ek Kapılar (logic-only, gate listesinde yok)

| Kapı | Koşul |
|------|-------|
| `stable_track` | stable_frames ≥ 5 |
| `forbidden_zone` | hedef yasak alanda değil |
| `operator_confirm` | operatör onayı var |
| `friend_rejection` | friend ise otomatik red |

### Karar Durumu Belirleme

```
Tüm kapılar PASS → FIRE_READY
hardware_enabled=false → NO_FIRE (en sık durum)
dry_run=true → LOCKED
body yok → NO_TARGET
balloon yok veya enemy değil → WAIT
```

---

## 4. Karar Akış Diyagramı

```
evaluate() çağrılır
    │
    ├─ body detection var mı?
    │   └─ Hayır → NO_TARGET
    │
    ├─ balloon detection var mı?
    │   └─ Hayır → WAIT
    │
    ├─ renk = enemy mi?
    │   ├─ friend → WAIT (friend_rejection)
    │   └─ unknown → WAIT
    │
    ├─ range valid mi?
    │   └─ Hayır → WAIT
    │
    ├─ stable_frames ≥ 5?
    │   └─ Hayır → WAIT
    │
    ├─ system armed mi?
    │   └─ Hayır → NO_FIRE
    │
    ├─ dry_run = true?
    │   └─ Evet → LOCKED (simülasyon)
    │
    ├─ hardware_enabled?
    │   └─ Hayır → NO_FIRE
    │
    ├─ operator onayı var mı?
    │   └─ Hayır → NO_FIRE
    │
    └─ Tümü geçti → FIRE_READY
```

---

## 5. Config Değiştirme Rehberi

### Güvenli Değiştirilebilir Ayarlar
- `camera.*` — Kamera çözünürlüğü, FPS
- `vision.body_conf_threshold` — Detection eşiği
- `color.*` — HSV aralıkları
- `motion.jog_step_deg` — Jog adım boyutu
- `motion.*_min/max_deg` — Soft limitler
- `decision.range_rules.*` — Menzil kuralları

### DEĞİŞTİRİLEMEZ Ayarlar (validator engeller)
- `system.mode` → her zaman DISARMED
- `system.dry_run` → her zaman true
- `system.fire_policy` → her zaman NO_FIRE
- `hardware.physical_command_enabled` → her zaman false
- `safety.no_fire_default` → her zaman true

Bu ayarları değiştirmek için `config.py`'deki validator'ları devre dışı bırakmak gerekir — **bu kasıtlı bir güvenlik bariyeridir.**
