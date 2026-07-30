# Legacy to ISTIKLAL Migration Plan

This is an audit and migration plan only. No legacy code was ported into the new runtime.

- no_physical_command_generated=true
- Safety invariant remains: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false

## Migration Map

| Legacy kaynak | Eski değer | Yeni sistemde hedef modül | Risk | Taşıma kararı |
| --- | --- | --- | --- | --- |
| python/settings.json camera_index | 1 | Vision real camera config / Device profile | dusuk | tasinabilir; manual operator confirmation |
| python/settings.json resolution | 640x480 | Camera Runtime profile | dusuk | tasinabilir |
| python/settings.json fps | 60 | Camera Runtime requested FPS | dusuk | tasinabilir |
| python/threaded_camera.py MJPG/buffer | MJPG, buffer=1, fps=60 | Camera Runtime low-latency preset | dusuk | recommended next patch |
| python/yolo_detector.py HSV ranges | red/pink dual HSV ranges | Vision OpenCV surrogate settings | dusuk | tasinabilir as preset |
| python/color_settings_export.py presets | strict/sensitive/balanced/bright/dim | Vision Settings preset library | dusuk | tasinabilir |
| python/yolo_detector.py target selection | closest_to_center/largest | Vision/Data Lab advisory tracking metadata | dusuk-orta | tasinabilir as advisory only |
| python/kalman_filter.py | x,y,vx,vy constant velocity | Vision advisory tracker/replay metadata | dusuk | tasinabilir, no hardware coupling |
| python/pid_settings.json KP_X | 20.0 | future bench-control config only | yuksek | otomatik tasima yok |
| python/pid_settings.json KP_Y | 20.0 | future bench-control config only | yuksek | otomatik tasima yok |
| serial_comm.py SPD | SPD,x,y | physical command boundary | kritik | do not auto-port |
| serial_comm.py LZR | LZR,0/1 | fire/trigger boundary | kritik | do not auto-port |
| pico_arduino optimized TMC | current/microstep/SpreadCycle/CoolStep | future bench-test documentation | yuksek | manual review required |
| pico_arduino JOY telemetry | JOY,x_raw,y_raw,speed_x,speed_y | Pico read-only telemetry parser candidate | orta | read-only candidate only |
| TMC_STATUS | TMC_X/TMC_Y mode and current scale | Serial/Pico telemetry page | orta | read-only candidate only |

## Safe Migration Candidates

1. Camera source/profile values may become optional Camera Runtime presets after operator confirmation.
2. HSV/color threshold values may become OpenCV surrogate presets and Data Lab annotation helpers.
3. Target selection and Kalman prediction may become advisory tracking metadata only.
4. Serial baud/status/JOY/TMC_STATUS formats may become read-only telemetry parsers only.
5. Legacy YOLO paths must not become production models unless repackaged with metadata/classes/thresholds through the new model package workflow.

## Do Not Auto-port

- Motor movement commands: SPD,x,y.
- Laser/servo/fire/trigger commands: LZR,0/1 and servo trigger paths.
- GPIO/PWM/STEP/DIR pin initialization and pulse generation.
- TMC_CURRENT or driver-current commands.
- Hardware enable behavior.
- Any automatic connection that writes to a physical serial device.

## Recommended Next Patch

A future safe patch can add an import-preview screen that reads these JSON files and proposes camera/HSV presets without applying them. It must keep `no_physical_command_generated=true` and must not import serial command writers.
