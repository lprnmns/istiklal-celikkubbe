# Faz 1 Config Sozlesmesi

Ana config dosyasi:

```text
config/config.yaml
```

Faz 1 zorunlu guvenlik varsayimlari:

- `system.mode: DISARMED`
- `system.default_fire_policy: NO_FIRE`
- `system.dry_run: true`
- `system.hardware_enabled: false`
- `safety.no_fire_default: true`
- `pico.protocol: json-line`
- `camera.mock: true`
- `vision.mock: true`
- `pico.mock: true`

`pins.profile_name` su anda `pico2_placeholder_not_final` degerindedir. Bu profil dokuman paketindeki ornek pinlerden olusur ve final/onayli kablolama profili degildir.

Config validation Faz 1'de su durumlari reddeder:

- Guvensiz sistem baslangici.
- `dry_run=false`.
- `hardware_enabled=true`.
- `NO_FIRE` disinda varsayilan fire policy.
- Pin cakismasi.
- Kritik pinlerin eksikligi.
- Confidence ve threshold alanlarinin 0-1 araligi disina cikmasi.
- `json-line` disinda serial protokol.
