# Legacy Safety Boundary Review

No physical command was executed. This is analysis only.

- no_physical_command_generated=true
- New system safety invariant remains: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false

## Critical Do-not-auto-port Paths

| Source | Physical path detected | Why blocked |
| --- | --- | --- |
| python/serial_comm.py | `ser.write()` sends `SPD,x,y`, `LZR,0/1`, `STP`, `HOM` | Physical serial command TX path. |
| python/threaded_pipeline.py | SerialThread calls `set_speed`, `laser_on`, `laser_off`, `home` | Background physical command sender. |
| python/main.py | `send_to_arduino`, `fire_laser`, manual WASD/space/home | Converts tracking/PID/manual input into motor and trigger commands. |
| python/donanim_test.py | Sends `SPD,*` and `LZR,*` test commands | Hardware test script, never run automatically. |
| arduino/motor_control/motor_control.ino | STEP/DIR pin output, ENABLE low, LZR command | Physical stepper and laser firmware. |
| pico/motor_control_pico.py | MicroPython Pin.OUT STEP/DIR/MS/ENABLE/LASER, `step_motor()` | Physical GPIO/STEP pulse generation. |
| pico/motor_control_pico_v2_tmc_uart.py | TMC init, ENABLE low, STEP pulses, LZR | Physical motor/laser driver path. |
| pico_arduino/motor_control_pico/motor_control_pico.ino | TMC UART config, STEP/DIR, LZR, STP/HOM | Physical actuator firmware. |
| pico_arduino/motor_control_v2_optimized/motor_control_v2_optimized.ino | TMC current, STEP/DIR, servo trigger `tetikServo.write(155)` | Physical motor/trigger firmware. |

## Serial Commands Found

- `SPD,x,y`: motor movement, critical, do not auto-port.
- `LZR,0/1`: laser/servo/trigger path, critical, do not auto-port.
- `STP`: physical controller stop, safe intent but still physical TX, do not auto-send in current phases.
- `HOM`: home/motion boundary, do not auto-port.
- `TMC_CURRENT,n`: changes driver current/hardware state, do not auto-port.
- `MODE,MANUAL/AUTO`: changes physical controller behavior, do not auto-port.
- `PING`, `STS,READY`, `STS,MOVING`, `JOY,*`, `TMC_STATUS`: may be documented as read-only telemetry/diagnostic candidates only; do not send to a physical device automatically in current safety mode.

## Safety Bypass Notes

- Legacy `SerialComm.send_command()` is NO-ACK fire-and-forget and returns success after write; this is incompatible with the new safety boundary.
- Legacy firmware enables motor drivers at setup in several variants; this must never be replicated in the portable console without a future bench-test phase and explicit hardware safety gate.
- Legacy state machine includes `AUTO_FIRING`; new console must keep this as documentation only until authorized phases.

## Required Migration Boundary

Perception settings can be proposed as presets. Actuator paths must remain documentation only.

no_physical_command_generated=true
