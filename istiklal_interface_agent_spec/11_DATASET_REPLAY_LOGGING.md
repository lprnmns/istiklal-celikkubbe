# 11. Dataset, Replay ve Loglama

## Amaç

Arayüz aynı zamanda veri fabrikası olmalıdır. Model hataları sahadan toplanmalı, replay ile incelenmeli ve yeni dataset versiyonlarına eklenmelidir.

## Kayıt Metadata

```yaml
scenario_id: s001
target_type: helicopter
team: enemy
distance_m: 10
angle: side
lighting: indoor_led
camera: 8mm
resolution: 1920x1080
fps: 60
operator: Alperen
model_version: body_yolo_v003
notes: "10m side pass, red balloon"
```

## Kayıt Türleri

- Raw video
- Overlay video
- Single frame
- Detection snapshot
- Hard negative snapshot
- Telemetry synchronized log
- Decision timeline

## Dosya Yapısı

```text
data/
  raw/
    videos/
    frames/
  sessions/
    2026-05-xx_s001/
      raw.mp4
      overlay.mp4
      metadata.yaml
      telemetry.jsonl
      decisions.jsonl
      detections.jsonl
      errors.jsonl
  datasets/
    body_v001/
    balloon_v001/
    hard_negative_v001/
```

## Frame Extraction UI

Ayarlar:

- output FPS
- min blur score
- duplicate removal
- include negative frames
- split by scenario

Kritik kural:

```text
Train/val/test ayrımı frame bazlı değil, video/senaryo bazlı yapılmalıdır.
```

## Replay Modu

- Eski video aç.
- Seçilen modelle inference yap.
- Overlay göster.
- Hata işaretle.
- Yeni model ile eski modeli karşılaştır.
- Hatalı frame'leri dataset kuyruğuna gönder.

## Hata Etiketleri

```text
false_positive_body
false_negative_body
wrong_body_class
false_positive_balloon
false_negative_balloon
wrong_friend_enemy
wrong_range
wrong_decision
tracker_id_switch
aim_point_wrong
```

## Log Tipleri

### Vision

```json
{"ts": 1.23, "frame": 120, "body_count": 2, "balloon_count": 1, "latency_ms": 18.4}
```

### Decision

```json
{"ts": 1.24, "track_id": 7, "decision": "NO_FIRE", "reason": "target_friend"}
```

### Pico

```json
{"ts": 1.25, "seq": 44, "telemetry": {"pan_steps": 123, "estop": false}}
```

### Operator action

```json
{"ts": 1.30, "action": "ARM_REQUEST", "user": "operator"}
```

## Model Karşılaştırma

UI iki modeli karşılaştırabilmeli:

- detection count
- missed targets
- false positives
- latency
- class confusion
- balloon center error

## Export

- YOLO detection dataset
- Ultralytics dataset YAML
- CSV metrics
- JSONL logs
- MP4 overlay video
- KTR-ready markdown report
