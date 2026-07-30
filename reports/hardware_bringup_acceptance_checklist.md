# Hardware Bring-up Acceptance Checklist

This checklist freezes the system at the Phase 28 boundary. Hardware-dependent acceptance cannot be completed until real Pico/Arduino and camera hardware are available.

Canonical proof: `no_physical_command_generated=true`

## 1. Before Pico/Arduino Is Connected

- Confirm system mode is `DISARMED`.
- Confirm fire policy is `NO_FIRE`.
- Confirm `dry_run=true`.
- Confirm `hardware_enabled=false`.
- Confirm `physical_command_enabled=false`.
- Confirm the operator understands this is read-only discovery and telemetry evidence only.
- Confirm no motor, servo, GPIO, PWM, STEP/DIR, TMC current, serial TX/write or fire path is enabled.

Required invariant:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

## 2. When Pico/Arduino Is Connected

- Run `GET /api/pico/discovery/ports`.
- Confirm the expected serial port is visible.
- Confirm port metadata is shown when available: path, description, VID, PID, serial number and manufacturer.
- Run `GET /api/pico/read-only/status`.
- Confirm `rx_only=true`.
- Confirm `tx_disabled=true`.
- Confirm `physical_command_enabled=false`.
- Confirm `no_physical_command_generated=true`.
- Use `POST /api/pico/read-only/connect` only with `read_only=true`.
- Confirm no startup command is sent.
- Confirm serial write/TX is not called.
- Run `GET /api/pico/read-only/latest-telemetry`.
- Confirm heartbeat or telemetry is parsed if the device publishes it by itself.
- Run `POST /api/pico/read-only/capture-evidence`.
- Confirm evidence is `recorded` when telemetry exists, or controlled `not_available` when it does not.
- Export Data Lab/KTR evidence and confirm Pico read-only files are present.

## 3. When Camera Is Connected

- Confirm camera source is explicitly `real_camera` or a concrete device path, not mock.
- Confirm requested vs actual camera values are visible.
- Capture real camera evidence.
- Confirm evidence includes frame metadata, device path when available and timestamp.
- Confirm mock/surrogate evidence is not presented as real camera proof.
- Confirm production YOLO is still not claimed unless a validated production model is loaded.
- Confirm `no_physical_command_generated=true`.

## 4. Before Any Future Motor Test

No motor test is allowed in the current phase. Before a future bench micro-jog safety gate:

- Confirm direction calibration profile exists.
- Confirm `x_axis_multiplier` is verified by operator observation.
- Confirm `y_axis_multiplier` is verified by operator observation.
- Confirm `axis_swap=false` or explicitly resolved.
- Confirm E-stop and physical safety area are ready.
- Confirm limit switch and fault telemetry are available or documented as absent.
- Confirm a separate low-speed micro-jog safety gate has been approved.
- Confirm timeout, kill-switch, current limit and operator stop behavior are defined.
- Do not enable movement until that separate gate exists.

## Explicitly Not Allowed In This Checklist

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

No physical command was executed. This is a pause gate and acceptance checklist only.

`no_physical_command_generated=true`
