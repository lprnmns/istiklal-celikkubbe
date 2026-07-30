# Phase 28 - Pico Read-Only Hardware Discovery and Telemetry Evidence

## Yapılanlar

- Pico/Arduino seri port keşfi için `GET /api/pico/discovery/ports` endpointi eklendi.
- RX-only bağlantı, disconnect, status, latest telemetry, evidence capture ve latest evidence endpointleri eklendi.
- Serial path yalnızca `readline()` ile telemetry okur; startup command, command TX veya serial write çağrısı yapılmaz.
- Pico ekranına Read-Only Hardware Discovery, Read-Only Connection Status, Latest Telemetry, Hardware Risk Notes ve Capture Evidence panelleri eklendi.
- Data Lab export içine Pico read-only status, latest telemetry, port inventory, evidence summary ve safety boundary dosyaları eklendi.
- KTR/report export içine Pico Read-Only Hardware Discovery Interface ve evidence dosyaları eklendi.
- Logs tarafında `pico.readonly_*` eventleri canonical `no_physical_command_generated=true` summary formatı ile görünür hale getirildi.

## Read-Only Endpoint Özeti

- `GET /api/pico/discovery/ports`
- `POST /api/pico/read-only/connect`
- `POST /api/pico/read-only/disconnect`
- `GET /api/pico/read-only/status`
- `GET /api/pico/read-only/latest-telemetry`
- `POST /api/pico/read-only/capture-evidence`
- `GET /api/pico/read-only/latest-evidence`

Tüm endpoint çıktılarında `physical_command_enabled=false` ve `no_physical_command_generated=true` korunur.

## UI Özeti

Pico ekranı artık serial inventory, candidate metadata, RX-only connection state, raw telemetry sample, parse error count, DTR/RTS reset risk note ve read-only evidence capture sonucunu tek yerde gösterir. Cihaz yoksa controlled `not_available` evidence üretilir.

## Data Lab / KTR Export

Yeni export dosyaları:

- `pico_readonly_status.json`
- `pico_readonly_latest_telemetry.json`
- `pico_readonly_evidence_summary.md`
- `pico_readonly_port_inventory.json`
- `pico_readonly_safety_boundary.md`

KTR 4.3 metnine “Pico Read-Only Hardware Discovery Interface” bölümü eklendi.

## Safety Boundary

- serial write yok
- Pico command TX yok
- motor jog yok
- STEP/DIR/PWM/GPIO output yok
- TMC current write yok
- hardware enable yok
- fire/trigger/shoot yok
- physical_command_enabled=false
- no_physical_command_generated=true

Safety invariant:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

## Test / Build Sonuçları

- `uv run pytest -q`: geçti
- `pnpm --dir frontend typecheck`: geçti
- `pnpm --dir frontend build`: geçti
- `python3 scripts/check_release.py`: geçti
- `bash -n release/linux/start_istiklal_c2.sh`: geçti
- `bash -n start_linux.sh`: geçti

Manual smoke:

- `/pico`: HTTP 200
- `/devices`: HTTP 200
- `/data-lab`: HTTP 200
- `/reports`: HTTP 200
- `/logs`: HTTP 200
- `/api/pico/discovery/ports`: HTTP 200
- `/api/pico/read-only/status`: HTTP 200
- `/api/pico/read-only/latest-telemetry`: HTTP 200
- `/api/pico/read-only/latest-evidence`: HTTP 200

## Screenshot Klasörü

`reports/screenshots/phase28_pico_readonly_discovery/`

## Bilinen Eksikler

- Gerçek Pico/Arduino bağlı olmadığı hostlarda telemetry evidence `not_available` olarak üretilir.
- DTR/RTS reset davranışı adapter/microcontroller bağımlıdır; bu fazda sadece risk notu olarak raporlanır.
- Bu faz production hardware acceptance değildir; yalnızca read-only discovery ve telemetry evidence katmanıdır.
