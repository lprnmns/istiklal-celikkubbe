# 9. Görüntü İşleme ve Karar UI

## Amaç

UI, görüntü işleme çıktısını sadece bbox olarak değil, karar verilebilir semantik hedef nesnesi olarak göstermelidir.

## Algı Katmanları

### Body Detector

```yaml
0: f16
1: helicopter
2: ballistic_missile
3: mini_micro_uav
```

Görev:

- Hedef tipi
- Gövde bbox
- Dost/düşman renk analizi için crop

### Balloon Detector

```yaml
0: balloon
```

Görev:

- Nişan noktası
- Atış güvenlik kapısı
- Balon merkezi

### Color Classifier

Girdi:

- Body crop veya segmentation mask
- Balon dışlanmış piksel alanı
- HSV/LAB histogram

Çıktı:

```json
{
  "team": "enemy",
  "confidence": 0.87,
  "enemy_ratio": 0.72,
  "friend_ratio": 0.04,
  "unknown_ratio": 0.24
}
```

### Tracker

- Track ID
- Stable frame sayısı
- Lost/reacquire
- Velocity estimate
- Lane estimate

## Overlay Katmanları

- Body bbox
- Body class label
- Balloon bbox
- Aim point
- Track ID
- Track trail
- Color decision
- Range label
- Decision label
- Safe/no-fire zones
- ROI crop
- 5/10/15 m distance lines

## Target Card

```json
{
  "track_id": 5,
  "class": "f16",
  "class_conf": 0.93,
  "team": "enemy",
  "team_conf": 0.88,
  "balloon": "found",
  "balloon_conf": 0.94,
  "range_m": 12.1,
  "stable_frames": "5/5",
  "decision": "FIRE_READY",
  "reason": "Enemy F16 in valid range"
}
```

## Karar Kapıları

```text
NO_FIRE default

Gate 1: system armed
Gate 2: e-stop released
Gate 3: pico heartbeat OK
Gate 4: body detected
Gate 5: track stable
Gate 6: target is enemy
Gate 7: range valid for class
Gate 8: balloon detected
Gate 9: aim point valid
Gate 10: no forbidden zone violation
```

## Range Rules

```python
if cls == "f16":
    valid = 10 <= range_m <= 15
elif cls in ["helicopter", "ballistic_missile"]:
    valid = 5 <= range_m <= 15
elif cls == "mini_micro_uav":
    valid = 0 <= range_m <= 15
```

## Karar Açıklamaları

```text
NO_FIRE: target is friend
NO_FIRE: balloon not detected
WAIT: F16 detected but range is 16.2m
LOCKED: enemy helicopter, range valid, track stable
FIRE_READY: all safety gates passed
```

## Vision Ayarları

- body model path
- balloon model path
- body confidence
- balloon confidence
- IoU threshold
- tracker type
- stable frames required
- max lost frames
- ROI mode
- SAHI mode
- imgsz
- frame skip

## Replay Hata Etiketleri

- false_positive_body
- false_negative_body
- wrong_class
- balloon_missed
- wrong_team
- wrong_range
- wrong_decision
