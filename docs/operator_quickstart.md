# ISTIKLAL C2 Operator Quickstart

## 1. Start

Windows: `start_windows.bat`

Linux: `./start_linux.sh`

Open: `http://127.0.0.1:8000`

## 2. First Run

Go to `/first-run`.

Run `Run first-run acceptance`.

Select the required readiness profile:

- `development_ready`
- `demo_ready`
- `field_dry_run_ready`
- `hardware_telemetry_ready`
- `competition_rehearsal_ready`

## 3. Select Camera

Go to `/devices`.

Refresh devices, then inspect:

- camera permission
- busy state
- stable path
- recommendation score

If no camera is available, keep mock mode and report it.

## 4. Load Model

Go to `/data-lab` for model registry or `/vision` for runtime status.

Production YOLO model must be provided by the vision team. OpenCV circle detector is test-only.

## 5. Verify Devices

Go to `/devices`.

Click:

- `Save as active field profile`
- `Verify active profile`

Resolve profile mismatch warnings before demo.

## 6. Run Self-Test

Go to `/self-test`.

Run self-test and check:

- no critical failures
- no physical command generated
- readiness profile warnings

## 7. Export Report

Go to `/reports`.

Generate:

- KTR Summary
- Demo Pack
- Readiness Pack

## Safety

This operator flow does not enable physical fire or motion.

Required invariant:

- DISARMED
- NO_FIRE
- dry_run=true
- hardware_enabled=false
- physical_command_enabled=false
