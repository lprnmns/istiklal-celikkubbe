# 6. Backend API ve WebSocket Spesifikasyonu

## Yaklaşım

- REST endpointleri: config, komut, dosya ve senaryo işlemleri.
- WebSocket: gerçek zamanlı telemetry, detection, log ve karar olayları.

## REST Endpoint Taslağı

### Health

```http
GET /api/health
```

```json
{
  "ok": true,
  "version": "0.1.0",
  "uptime_s": 421.3
}
```

### System

```http
GET /api/system/state
POST /api/system/mode
POST /api/system/arm
POST /api/system/disarm
```

### Camera

```http
GET /api/camera/devices
POST /api/camera/start
POST /api/camera/stop
POST /api/camera/settings
```

### Vision

```http
GET /api/vision/models
POST /api/vision/body-model
POST /api/vision/balloon-model
POST /api/vision/settings
```

### Pico

```http
GET /api/pico/ports
POST /api/pico/connect
POST /api/pico/disconnect
GET /api/pico/telemetry
POST /api/pico/pin-config
POST /api/pico/self-test
```

### Motor

```http
POST /api/motor/jog
POST /api/motor/home
POST /api/motor/stop
POST /api/motor/settings
```

### Safety

```http
GET /api/safety/gates
POST /api/safety/zone
POST /api/safety/fire-request
```

### Dataset / Replay

```http
POST /api/dataset/record/start
POST /api/dataset/record/stop
POST /api/dataset/capture-frame
POST /api/dataset/export-yolo
POST /api/replay/load
POST /api/replay/start
POST /api/replay/pause
POST /api/replay/seek
POST /api/replay/tag-error
```

## WebSocket Formatı

Tek endpoint önerisi:

```text
/ws
```

Ortak mesaj:

```json
{
  "type": "vision.targets",
  "ts": 1710000000.123,
  "seq": 42,
  "payload": {}
}
```

## Mesaj Tipleri

### `system.state`

```json
{
  "mode": "FRIEND_ENEMY_STAGE_3",
  "armed": false,
  "estop": false,
  "ready": false,
  "blocking_reasons": ["body_model_not_loaded"]
}
```

### `vision.frame_stats`

```json
{
  "fps": 42.1,
  "capture_latency_ms": 8.2,
  "inference_latency_ms": 18.4,
  "tracking_latency_ms": 1.2,
  "decision_latency_ms": 0.7
}
```

### `vision.targets`

```json
{
  "targets": [
    {
      "track_id": 7,
      "body_class": "helicopter",
      "body_conf": 0.91,
      "bbox": [120, 80, 340, 220],
      "team": "enemy",
      "team_conf": 0.87,
      "balloon_found": true,
      "balloon_bbox": [240, 230, 290, 280],
      "aim_point": [265, 255],
      "range_m": 8.4,
      "stable_frames": 5,
      "decision": "LOCKED",
      "reason": "enemy target, balloon locked, range valid"
    }
  ]
}
```

### `decision.gates`

```json
{
  "track_id": 7,
  "decision": "NO_FIRE",
  "gates": {
    "armed": true,
    "estop_released": true,
    "pico_heartbeat": true,
    "track_stable": true,
    "target_enemy": false,
    "balloon_detected": true,
    "range_valid": true,
    "zone_valid": true
  },
  "blocking_reason": "target_friend"
}
```

### `pico.telemetry`

```json
{
  "connected": true,
  "seq": 180,
  "state": "STANDBY",
  "pan_steps": 1200,
  "tilt_steps": -240,
  "driver_enabled": false,
  "estop": false,
  "limit_left": false,
  "limit_right": false,
  "limit_up": false,
  "limit_down": false,
  "trigger_ready": false,
  "last_error": null
}
```

### `log.event`

```json
{
  "level": "WARN",
  "subsystem": "SAFETY",
  "message": "Fire request rejected",
  "details": {
    "reason": "balloon_not_detected",
    "track_id": 12
  }
}
```

## Pydantic Model Önerileri

- `SystemState`
- `CameraSettings`
- `VisionSettings`
- `Detection`
- `TrackedTarget`
- `DecisionGateState`
- `PicoTelemetry`
- `PinAssignment`
- `SerialPacket`
- `LogEvent`
- `ScenarioMetadata`

## Hata Formatı

```json
{
  "error": {
    "code": "PIN_CONFLICT",
    "message": "GP2 cannot be assigned to both PAN_STEP and TILT_STEP.",
    "details": {
      "pin": "GP2",
      "functions": ["PAN_STEP", "TILT_STEP"]
    }
  }
}
```
