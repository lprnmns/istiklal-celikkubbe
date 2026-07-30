# Phase 12 - Safe Hardware Discovery and Read-Only Pico Telemetry

## Safety Boundary

Phase 12 only discovers serial ports, opens a Pico serial port in read-only mode when explicitly enabled, parses incoming telemetry and displays connection state in the UI.

Phase 12 does not:

- move motors
- generate STEP/DIR pulses
- generate PWM
- command servo or trigger output
- send fire requests to hardware
- send motion jog/go-to/home/scan commands to hardware
- automatically send DISARM to a physical Pico
- enable hardware command authority

Default safety remains:

- DISARMED
- NO_FIRE
- dry_run=true
- hardware_enabled=false
- physical_command_enabled=false

## Transport Modes

- `mock`: default development transport.
- `real_readonly`: physical serial port may be opened for incoming telemetry only.
- `real_command_disabled`: reserved status label for future phases; physical commands remain disabled.

Only `mock` and `real_readonly` are supported in Phase 12.

## Config Flags

```yaml
hardware:
  hardware_discovery_enabled: false
  physical_command_enabled: false
  allow_real_serial_readonly: false
  allow_physical_motion: false
  allow_physical_fire: false

serial:
  transport_mode: "mock"
  real_serial_enabled: false
  real_serial_readonly: true
  port: null
  auto_connect: false
  baudrate: 115200
  heartbeat_timeout_ms: 1000
```

Validation rules:

- `physical_command_enabled=true` is rejected.
- `allow_physical_motion=true` is rejected.
- `allow_physical_fire=true` is rejected.
- `transport_mode=real_readonly` requires `hardware.allow_real_serial_readonly=true`.
- `auto_connect=true` is rejected in Phase 12.

## Read-Only Serial Discovery

Endpoint list:

- `GET /api/hardware/serial/ports`
- `GET /api/hardware/status`
- `POST /api/hardware/connect-readonly`
- `POST /api/hardware/disconnect`
- `GET /api/hardware/telemetry`
- `GET /api/hardware/capabilities`

Port scan returns:

- device
- description
- hwid
- manufacturer
- is_candidate_pico
- warning

## Telemetry JSON Format

Expected Pico-to-PC JSON-line telemetry:

```json
{
  "type": "telemetry",
  "seq": 10,
  "device": "pico2",
  "firmware_version": "dev",
  "estop_state": false,
  "driver_enabled": false,
  "pan_position_steps": 0,
  "tilt_position_steps": 0,
  "limits": {
    "pan_left": false,
    "pan_right": false,
    "tilt_up": false,
    "tilt_down": false
  },
  "safe_state": true
}
```

If the port opens but no telemetry arrives, the system reports `OPEN_NO_TELEMETRY` and shows a warning. The backend does not crash.

## Parser Behavior

- Valid `telemetry` and `heartbeat` messages update read-only telemetry state.
- Invalid JSON emits a `hardware.error` event and records a parse error.
- Unknown message type emits a `hardware.warning` event.
- Last raw message is retained for operator inspection.

## Risky Command Blocker

The following command types are always rejected in real read-only mode:

- `fire_request`
- `jog_motor`
- `set_motor_target`
- `set_servo_position`
- `set_servo`
- `enable_driver`
- `set_pin`
- `pwm_write`
- `step_pulse`

Response reason:

`physical_commands_disabled_in_phase12_readonly`

Every rejection carries `no_physical_command_generated=true`.

## UI Flow

Pico screen:

1. Open Pico page.
2. Review Real Hardware Discovery panel.
3. Refresh serial ports.
4. Select candidate Pico port.
5. Connect Read-Only only when config explicitly allows it.
6. Inspect firmware version, safe state, heartbeat age, raw message and parse errors.

Serial screen:

- Shows `MOCK` or `REAL READ-ONLY`.
- Disables TX form while real read-only is active.
- Shows physical commands disabled badge.

Dashboard:

- Shows Physical Pico state.
- Shows Mock Pico active/inactive.
- Shows Physical commands disabled.
- Shows telemetry age and safe state.

Self-Test:

- Checks hardware discovery config.
- Checks real serial read-only state.
- Checks physical command disabled invariant.
- Checks telemetry if connected.
- Checks risky command blocker.

## Before Hardware Bring-Up

- Confirm Pico firmware is telemetry-only.
- Confirm no motor driver enable pin is toggled.
- Confirm no PWM/STEP/DIR outputs are configured.
- Validate E-stop wiring physically.
- Validate limit switch wiring physically.
- Review Pico local safety model.
- Add explicit operator-controlled hardware enable procedure in a future phase.

## Intentionally Not Done

- No physical motor command.
- No servo command.
- No trigger/fire command.
- No STEP/DIR/PWM output.
- No automatic DISARM transmission to real Pico.
- No hardware enable flow.
