# 10. Güvenlik ve Arm/Disarm State Machine

## Temel Prensip

```text
Default policy = NO_FIRE
```

## Durumlar

```text
BOOTING
DISARMED
STANDBY
MANUAL
AUTONOMOUS
LOCKED
FIRE_READY
FIRING
FAULT
ESTOP_ACTIVE
REPLAY
CALIBRATION
```

## Geçişler

```text
BOOTING → DISARMED
DISARMED → STANDBY
STANDBY → MANUAL
STANDBY → AUTONOMOUS
AUTONOMOUS → LOCKED
LOCKED → FIRE_READY
FIRE_READY → FIRING
any → ESTOP_ACTIVE
any → FAULT
```

## Arm Koşulları

- Pico bağlı
- Heartbeat aktif
- E-stop serbest
- Kamera aktif
- Body model yüklü
- Balloon model yüklü
- Pin config geçerli
- Driver enable kontrol edilebilir
- Servo neutral
- Critical fault yok

## Fire Gate

```json
{
  "armed": true,
  "estop_released": true,
  "pico_heartbeat": true,
  "track_stable": true,
  "target_enemy": true,
  "range_valid": true,
  "balloon_detected": true,
  "aim_point_valid": true,
  "zone_valid": true,
  "operator_or_auto_permission": true
}
```

## UI Davranışı

- E-stop aktifse kırmızı global banner.
- E-stop aktifken komut gönderilmez.
- Fire request sadece gates geçince aktifleşir.
- Pin değişikliği sadece DISARMED.
- Motor testleri fire lock kapalıyken.
- Replay modda fiziksel komut yok.
- Calibration modda servo tetik disabled.

## Pico Local Safety

- E-stop input aktifse motion stop.
- PC heartbeat timeout ise driver disable.
- Limit switch aktifse ilgili yönde hareket engeli.
- Fire request için local armed flag gerekir.
- CRC hatalı paket işlenmez.

## Fault Örnekleri

```text
PICO_TIMEOUT
CAMERA_LOST
MODEL_LOAD_FAILED
SERIAL_CRC_SPIKE
PIN_CONFIG_INVALID
ESTOP_ACTIVE
LIMIT_SWITCH_STUCK
DRIVER_FAULT
FIRE_REQUEST_REJECTED
```

## Safety Checklist

```text
[✓] Camera active
[✓] Body model loaded
[✓] Balloon model loaded
[✓] Pico connected
[✓] Heartbeat OK
[✓] E-stop released
[✓] Pin config valid
[✓] Driver enabled
[✓] Track stable
[✓] Enemy confirmed
[✓] Balloon locked
[✓] Range valid
[✓] No forbidden zone
```
