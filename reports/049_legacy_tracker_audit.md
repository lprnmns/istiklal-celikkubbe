# Ara Task 24.5 + 24.6 - Legacy Stable Tracker Audit

This report audits `/home/alperen/teknofest/eski_sistem_arayüz` and produces a safe migration plan for `/home/alperen/teknofest`.

No physical command was executed. This is analysis only.

- no_physical_command_generated=true
- Safety invariant remains: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false
- New ISTIKLAL C2 Console runtime code was not changed.

## Folder Inventory

- `arduino/`: Arduino motor-control firmware. Contains STEP/DIR and laser paths. Do not auto-port.
- `pico/`: MicroPython Pico 2 motor/TMC prototypes and wiring docs. Do not auto-port actuator code.
- `pico_arduino/`: Arduino IDE Pico firmware, including TMC2209 optimized variants and joystick telemetry. Read-only telemetry ideas only; actuator code blocked.
- `python/`: Legacy desktop GUI, camera, YOLO/OpenCV detection, PID, serial bridge and safety manager. Mixed: perception may be mined, serial/control blocked.
- `models/`: Legacy `.pt` files. Must not be treated as production model packages until metadata/classes/thresholds are provided.
- `settings.json`, `python/settings.json`, `python/pid_settings.json`, `python/camera_settings.json`: legacy runtime settings.

## Important File Inventory

- `python/config.py`: Core constants for camera, detection, PID, serial, hardware pins, limits Risk: `mixed`
- `python/main.py`: Legacy runtime loop: camera read, detector queue, target selection, PID, serial motor/laser TX Risk: `critical_actuation_paths_present`
- `python/yolo_detector.py`: YOLO detector plus OpenCV HSV red/pink contour fallback Risk: `perception_safe_if_decoupled`
- `python/threaded_camera.py`: Low-latency threaded OpenCV camera reader Risk: `perception_safe`
- `python/threaded_pipeline.py`: Detection thread and serial command thread Risk: `mixed; serial thread is do_not_auto_port`
- `python/pid_controller.py`: Dual-axis PID with anti-windup and output clamp Risk: `control_config_only_do_not_auto_port_to_hardware`
- `python/kalman_filter.py`: OpenCV constant velocity Kalman filter for target loss/prediction Risk: `perception_tracking_safe`
- `python/serial_comm.py`: NO-ACK serial command sender using SPD/LZR/STP/HOM Risk: `critical_do_not_auto_port`
- `python/safety_manager.py`: Legacy angle limit, forbidden fire zone, emergency stop, laser timeout logic Risk: `document_only; not sufficient for new safety`
- `pico_arduino/motor_control_pico/motor_control_pico.ino`: Pico 2 Arduino firmware: TMC2209 UART, STEP/DIR, laser, serial status Risk: `critical_do_not_auto_port`
- `pico_arduino/motor_control_v2_optimized/motor_control_v2_optimized.ino`: Optimized Pico 2 firmware: TMC, servo trigger, joystick, STEP/DIR, telemetry-like status Risk: `critical_do_not_auto_port`
- `arduino/motor_control/motor_control.ino`: High-performance Arduino motor firmware with STEP/DIR and laser serial commands Risk: `critical_do_not_auto_port`
- `CAMERA_IMAGE_ADJUSTMENT_GUIDE.md`: Camera brightness/contrast/saturation/preprocess notes Risk: `perception_safe`
- `COLOR_TUNING_GUIDE.md`: HSV color tuning and fallback detector tuning Risk: `perception_safe`
- `CONFIG_PY_NOTES_TMC_UART.md`: TMC microstepping vs config synchronization notes Risk: `document_only_for_future_bench`
- `HARDWARE_CONFIG.md`: Legacy hardware, camera, YOLO, PID, Kalman, safety constants Risk: `mixed`
- `MICROSTEPPING_SETUP.md`: Microstepping and steps/degree calibration notes Risk: `document_only_for_future_bench`
- `PID_TUNING_GUIDE.md`: PID stabilization guidance: KP/KD/KI tuning, lost target persistence Risk: `document_only_for_control`
- `PID_TUNING_OPTIMAL.md`: Candidate PID presets Risk: `document_only_for_control`
- `PID_X_8_Y_32_TUNING.md`: PID notes for X 1/8 and Y 1/32 microstepping Risk: `document_only_for_control`
- `TMC2209_OPTIMIZATION_GUIDE.md`: TMC current, CoolStep, interpolation, SpreadCycle/StealthChop guidance Risk: `document_only_do_not_auto_port`

## Camera Source Findings

- Primary legacy runtime settings: `python/settings.json` uses camera index `1`, resolution `640x480`, FPS `60`, stabilization `Normal`.
- Root `settings.json` variant uses camera index `1`, resolution `1280x720`, FPS `50`.
- `python/main.py` can use `ThreadedCamera` and normal OpenCV `cv2.VideoCapture` fallback.
- `python/threaded_camera.py` uses `cv2.CAP_DSHOW`, fallback default backend, `MJPG`, requested 60 FPS, buffer size 1, autofocus off, auto exposure 0.25, exposure -3, brightness 150 and 10-frame warmup.
- `python/main.py` normal mode tries DSHOW then default backend, sets width/height/FPS, buffer size 1, autofocus/auto exposure/auto white balance, brightness/contrast/saturation/gamma, and flushes 30 frames.

## Vision and Detection Findings

- Detector factory supports `YOLO` if ultralytics is installed and model loads; otherwise falls back to OpenCV ColorDetector.
- YOLO settings in `python/config.py`: model path `models/yolo2/best.pt`, confidence 0.30, IoU 0.25, image size 416, red class 0, blue class 1.
- OpenCV ColorDetector uses HSV dual red/pink ranges: `[0,50,30]-[20,255,255]` and `[160,50,30]-[180,255,255]`, Gaussian blur `(11,11)`, elliptical morphology kernel `(5,5)`, close 2, open 1, min area 300, aspect ratio 0.3 to 3.0.
- `color_settings_export.py` and `color_tuner.py` provide strict/sensitive/balanced/bright/dim HSV presets; these are safe candidates for Vision Runtime presets.
- Target coordinate is bounding-box center `x + w/2`, `y + h/2`.
- Multiple target selection: AUTO/AUTONOMOUS uses closest target to crosshair; MANUAL selects largest blue target when present.

## Tracking Findings

- Crosshair is image center: width/2, height/2.
- Error is target center minus crosshair for X/Y.
- Dead zone: `DEAD_ZONE=12`, `DEAD_ZONE_STOP=4` in `python/config.py`.
- Kalman filter: OpenCV constant velocity state `[x, y, vx, vy]`, default dt 1/30, process noise 0.03, measurement noise 1.0.
- Target persistence: lost target is held up to 10 frames using Kalman prediction, then target resets.
- Output smoothing: exponential smoothing with alpha 0.5 in `compute_control()`.
- Adaptive near-target thresholds use target radius `min(w,h)/4`, lock threshold `0.85*radius`, slow threshold `1.8*radius`, medium threshold `2.8*radius`.

## PID / Control Findings

- `python/pid_controller.py` implements P/I/D with integral clamp and output clamp.
- `python/pid_settings.json` currently contains `{'KP_X': 20.0, 'KI_X': 0.01, 'KD_X': 0.0, 'KP_Y': 20.0, 'KI_Y': 0.01, 'KD_Y': 1.0}`.
- `python/config.py` contains duplicated class defaults; final class assignments are effectively X KP 8.0, KI 0.01, KD 0.50; Y KP 4.0, KI 0.002, KD 0.30; output clamp +/-1000; min move speed 35; integral max 25000.
- `PID_TUNING_OPTIMAL.md`, `PID_TUNING_GUIDE.md`, and `PID_X_8_Y_32_TUNING.md` contain useful tuning notes, but these are actuator-control settings and must not be applied automatically.

## Motor / Driver Findings

- Multiple firmware variants generate real STEP/DIR pulses and configure TMC2209. They are documentation-only for future bench-control.
- `pico_arduino/motor_control_v2_optimized/motor_control_v2_optimized.ino` documents optimized TMC settings: X run/hold current 1400/400 mA, X microsteps 1/8 with interpolation, SpreadCycle; Y run/hold 1000/300 mA, Y microsteps 1/8 with interpolation, hybrid mode, CoolStep/chopper settings.
- `pico_arduino/motor_control_pico/motor_control_pico.ino` uses 460800 USB serial, TMC UART 115200, STEP X GPIO14, DIR X GPIO12, STEP Y GPIO15, DIR Y GPIO13, ENABLE GPIO10, LASER GPIO11, E-STOP GPIO18.
- `arduino/motor_control/motor_control.ino` and MicroPython Pico files include direct GPIO output and step pulses. Do not auto-port.

## Pico / Arduino / Serial Findings

- Legacy Python serial bridge uses 460800 baud in the main path and NO-ACK fire-and-forget command sending.
- Core command format: `SPD,x,y`, `LZR,0/1`, `STP`, `HOM`, `PING`, plus `MODE`, `TMC_STATUS`, `TMC_CURRENT` in variants.
- Status/telemetry-like lines: `OK,PICO_READY`, `OK,PICO_READY_V2`, `STS,READY`, `STS,MOVING`, `JOY,x_raw,y_raw,speed_x,speed_y`, `TMC_X,...`, `TMC_Y,...`.
- Only status/JOY/TMC status line formats are candidates for read-only parser work. Command TX remains blocked.

## Critical Findings

1. Legacy perception and tracking logic has reusable knowledge: camera profiles, HSV presets, target selection, Kalman, latency metrics.
2. Legacy control loop directly converts detection into physical serial `SPD` commands. This must not be ported into ISTIKLAL C2 runtime.
3. Legacy fire/laser/servo paths exist (`LZR`, `tetikServo.write(155)`, `laser_on`). These are critical do-not-auto-port paths.
4. Legacy firmware enables drivers and emits STEP/DIR pulses. It is future bench-test documentation only.
5. Legacy YOLO model files are not valid new production packages without metadata/classes/thresholds/checksum and competition validation.

## Output Files

- `reports/legacy_tracker_config_inventory.json`
- `reports/legacy_perception_candidates.json`
- `reports/legacy_serial_telemetry_candidates.json`
- `reports/legacy_to_istiklal_migration_plan.md`
- `reports/legacy_safety_boundary_review.md`

## Verification

- `find eski_sistem_arayüz -maxdepth 3 -type f`: completed for inventory.
- Static keyword audit for motor/fire/GPIO/PWM/STEP/DIR/serial/write paths: completed.
- `settings.json`, `python/settings.json`, `python/pid_settings.json`, `python/camera_settings.json`: parsed.
- Markdown guides for camera/color/PID/TMC/hardware/performance: reviewed and summarized.
- `uv run pytest -q`: passed.
- `pnpm typecheck`: passed.
- `pnpm build`: passed.
- `python3 scripts/check_release.py`: passed.
- `bash -n release/linux/start_istiklal_c2.sh`: passed.
- `bash -n start_linux.sh`: passed.

## Commit Scope

Only analysis reports and JSON inventories were created. No ISTIKLAL C2 runtime source file was changed.

no_physical_command_generated=true
