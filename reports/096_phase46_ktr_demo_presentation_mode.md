# Phase 46 KTR Demo Presentation Mode

`/cockpit?ktr_demo=1` is the referee-facing presentation cockpit.

## KTR Demo Rules

- Uses deterministic fixture target visualization.
- Does not show live target claims.
- Shows truth mode clearly.
- Shows tactical digital twin, FOV, target projection, no-go reference and safety strip.
- Keeps Pico and external USB camera absence as controlled offline/expected states.

## Safety

The global strip remains visible:

- `SYSTEM MODE: DRY_RUN`
- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `NO PHYSICAL COMMAND GENERATED`
