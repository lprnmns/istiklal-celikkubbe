# Phase 49 - YOLO Toggle and Camera Performance

The camera HUD now exposes a perception toggle:

- `YOLO ON` - detection/tracking UI remains active.
- `YOLO OFF` - camera-only cockpit mode; live target detection is not claimed.

The toggle is controlled by the URL query parameter:

- `/cockpit?perception=off`
- `/cockpit?ktr_demo=1&perception=off&quality=high`

In normal cockpit mode, YOLO OFF hides live detection overlays and labels the view as camera-only. In KTR demo mode, fixture target projection remains allowed because the UI truth mode explicitly says fixture/not live target.

This toggle is perception/UI-only. It does not affect motor, fire, servo, serial TX, GPIO, PWM, STEP/DIR or hardware-enable behavior.

Safety invariants:

- physical_command_enabled=false
- serial_tx_enabled=false
- no_physical_command_generated=true

