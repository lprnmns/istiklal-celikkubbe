# Phase 28.1 - Hardware Bring-up Pause Gate and Acceptance Checklist

## Amaç

Faz 28 sonunda sistem Pico/Arduino read-only discovery ve telemetry evidence seviyesine geldi. Ancak gerçek Pico/Arduino ve gerçek kamera donanımı mevcut olmadığı için real hardware acceptance tamamlanamaz. Bu rapor, Faz 29’a geçmeden önce sistemi güvenli pause gate durumunda dondurur ve donanım geldiğinde izlenecek acceptance checklist’i tanımlar.

Bu task runtime koda fiziksel komut, motor, servo, GPIO, PWM, STEP/DIR, serial TX/write, hardware enable veya fire/trigger yolu eklemez.

## Mevcut Durum

- Faz 27: Motion direction semantics simulator advisory-only olarak tamamlandı.
- Faz 28: Pico/Arduino read-only discovery ve RX-only telemetry evidence endpointleri eklendi.
- Gerçek Pico/Arduino bağlı olmadığı durumda sistem controlled `not_available` evidence üretebilir.
- Gerçek kamera olmadan real camera evidence acceptance tamamlanamaz.
- Production hardware acceptance henüz yapılmadı.

## Safety Invariant

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Canonical proof:

`no_physical_command_generated=true`

## Faz 29’a Geçmeme Nedeni

Faz 29 veya sonraki hardware-dependent acceptance aşamaları, gerçek Pico/Arduino ve gerçek kamera olmadan anlamlı şekilde tamamlanamaz. Mevcut hostta yapılabilen doğrulamalar yalnızca API, UI, export, logs ve not_available evidence seviyesindedir. Bu yüzden sistem şu anda hardware bring-up pause gate durumundadır.

## Donanım Geldiğinde Acceptance Akışı

Detay checklist:

- `reports/hardware_bringup_acceptance_checklist.md`
- `reports/hardware_required_next_steps.json`
- `reports/phase28_1_safety_boundary_check.md`

Özet:

1. Pico/Arduino takılmadan önce invariant doğrulanır.
2. Pico/Arduino takıldığında yalnızca read-only discovery ve RX telemetry kontrol edilir.
3. Kamera takıldığında real camera evidence ve mock-vs-real ayrımı doğrulanır.
4. Motor testinden önce direction calibration profile, E-stop ve ayrı bench micro-jog safety gate zorunlu tutulur.

## Kesin Yasaklar

- serial write
- Pico command TX
- motor jog
- step pulse
- DIR pin change
- PWM/GPIO output
- TMC current write
- hardware enable
- fire/trigger/shoot
- `physical_command_enabled=true`

## Doğrulama Sonuçları

- `uv run pytest -q`: geçti
- `pnpm --dir frontend typecheck`: geçti
- `pnpm --dir frontend build`: geçti
- `python3 scripts/check_release.py`: geçti
- `bash -n release/linux/start_istiklal_c2.sh`: geçti
- `bash -n start_linux.sh`: geçti

## Bilinen Eksikler

- Gerçek Pico/Arduino telemetry acceptance beklemede.
- Gerçek kamera evidence acceptance beklemede.
- Direction calibration fiziksel gözlemle henüz doğrulanmadı.
- Motor micro-jog veya hareket testi bu fazda yapılmadı ve yapılmayacak.

No physical command was executed. This is a pause gate and acceptance planning task only.

`no_physical_command_generated=true`
