# Faz 6 Decision Engine ve Safety Gates

## Decision State Machine

Decision state degerleri:

- `NO_TARGET`
- `TRACKING`
- `WAIT`
- `LOCKED`
- `FIRE_READY`
- `NO_FIRE`
- `FAULT`

Varsayilan fire policy:

```text
NO_FIRE_DEFAULT
```

Sistem hala varsayilan olarak:

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`

## Safety Gates

Gate modeli:

```json
{
  "name": "range_valid_gate",
  "status": "pass",
  "severity": "info",
  "reason": "helicopter range 8.7m is valid.",
  "updated_at": 1710000000.0
}
```

Gate listesi:

- `system_disarmed_gate`
- `system_armed_gate`
- `dry_run_gate`
- `hardware_enabled_gate`
- `estop_gate`
- `pico_connected_gate`
- `pico_heartbeat_gate`
- `serial_ok_gate`
- `vision_running_gate`
- `body_detected_gate`
- `balloon_detected_gate`
- `team_classified_gate`
- `enemy_target_gate`
- `friend_rejection_gate`
- `range_valid_gate`
- `stable_track_gate`
- `forbidden_zone_gate`
- `operator_confirm_gate`

## Range Rules

Default config:

```yaml
decision:
  range_rules:
    f16: {min_m: 10.0, max_m: 15.0}
    helicopter: {min_m: 5.0, max_m: 15.0}
    ballistic_missile: {min_m: 5.0, max_m: 15.0}
    mini_micro_uav: {min_m: 0.0, max_m: 15.0}
```

`unknown` veya rule bulunmayan siniflar fire icin forbidden kabul edilir.

## Team Logic

Team degerleri:

- `enemy`
- `friend`
- `unknown`

Kurallar:

- `friend` ise kesin `NO_FIRE`.
- `unknown` ise `WAIT`; `FIRE_READY` olamaz.
- `enemy` degilse `FIRE_READY` olamaz.
- Friend target blocking reason: `target_is_friend`.

## Balloon ve Stability Logic

- Balloon yoksa `FIRE_READY` olamaz.
- Balloon confidence threshold config'ten gelir.
- Aim point sadece telemetry/decision object icinde tutulur.
- `stable_frames_required` default 5.
- `stable_frames < required` ise gate fail olur.

## Forbidden Zone Placeholder

```yaml
forbidden_zone_check_enabled: false
```

Bu fazda zone editor yoktur. Gate `not_applicable` doner.

## Fire Request Rejection Model

`POST /api/safety/fire-request` decision engine sonucunu dondurur.

Bu fazda:

- Gercek fire komutu yok.
- Mock serial'a bile fire gonderilmez.
- `hardware_enabled=false` oldugu icin request reject edilir.
- Response gate listesi, blocking reasons ve reason icerir.

## Dry-run Behavior

Arm islemi dry-run evaluation icindir. Hardware yetkisi vermez.

DISARM her zaman accepted doner.

## WebSocket Eventleri

- `decision.updated`
- `safety.gates`
- `safety.armed`
- `safety.disarmed`
- `safety.fire_request_rejected`
- `safety.fire_request_accepted_dry_run`
- `safety.fault`

## UI Kullanim Akisi

Safety sayfasi:

- Current decision state.
- Fire policy.
- Arm/disarm controls.
- Fire request dry-run evaluation button.
- Safety gates matrix.
- Blocking reasons.
- Active target summary.
- Range rules.
- Latest decision events.

UI uyarisi:

```text
No physical fire command is generated in Phase 6.
```

## Bilincli Olarak Yapilmayanlar

- Motor/taret kontrol paneli yok.
- Dataset/replay yok.
- Self-test wizard yok.
- Gercek hardware komutu yok.
- Fire request serial/motor/servo komutuna baglanmadi.
- Vision output fiziksel aksiyona baglanmadi.
