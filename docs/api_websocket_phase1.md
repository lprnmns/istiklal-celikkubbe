# Faz 1 API ve WebSocket Sozlesmesi

Bu dokuman Faz 1 backend safety cekirdegi icin gecerli ilk sozlesmeyi tanimlar.

## REST

### `GET /api/health`

Backend saglik durumunu dondurur.

```json
{
  "ok": true,
  "version": "0.1.0",
  "uptime_s": 0.123
}
```

### `GET /api/system/state`

Varsayilan sistem state'i guvenli baslar.

```json
{
  "mode": "DISARMED",
  "armed": false,
  "fire_policy": "NO_FIRE",
  "dry_run": true,
  "hardware_enabled": false,
  "ready": false,
  "reason": "System starts disarmed with NO_FIRE policy.",
  "blocking_reasons": [
    "system_disarmed",
    "no_fire_policy_active",
    "dry_run_enabled",
    "hardware_disabled"
  ]
}
```

### `GET /api/safety/gates`

Safety gate durumunu dondurur. Faz 1'de karar varsayilan olarak `NO_FIRE` olur.

### `POST /api/safety/fire-request`

Faz 1'de her zaman reddedilir. Gercek atesleme veya servo komutu uretmez.

### `POST /api/motor/jog`

Faz 1'de her zaman reddedilir. Gercek motor komutu uretmez.

## WebSocket

### `/ws`

Ortak envelope:

```json
{
  "type": "system.state",
  "ts": 1710000000.123,
  "seq": 1,
  "payload": {}
}
```

Faz 1 mesaj tipleri:

- `system.state`
- `pico.telemetry`
- `vision.frame_stats`
- `vision.targets`
- `decision.gates`

Pico ve vision mesajlari mock placeholder servislerinden gelir. Gercek Pico serial baglantisi veya gercek kamera gerektirmez.

