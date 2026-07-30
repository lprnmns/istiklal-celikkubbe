# Phase 30.3 USB Camera Selection Fix

## Decisions

- Internal laptop camera acceptance: partial
- External USB camera acceptance: passed
- Selected camera device: /dev/video2
- Backend USB frame capture: passed
- Browser external observation: observed_by_operator
- Capture method: ffmpeg
- Frame path: /home/alperen/teknofest/exports/camera_host/camera_frame_20260515_133810_8621de.jpg
- Frame SHA256: 0ac3c8f7b86903388ed27d8cbee755e4798b16f7b4cdd83173d24a3f2e260c3e
- Motor/hardware command readiness: not_started
- Competition readiness: false

## Camera Inventory

```json
[
  {
    "camera_kind": "internal_laptop_camera",
    "name": "HP HD Camera",
    "paths": [
      "/dev/video0",
      "/dev/video1"
    ],
    "preferred_capture_path": "/dev/video0",
    "evidence_status": "not_evaluated",
    "frame_captured": false,
    "advisory_only": true,
    "physical_command_enabled": false,
    "no_physical_command_generated": true
  },
  {
    "camera_kind": "external_usb_camera",
    "name": "HD USB Camera",
    "paths": [
      "/dev/video2",
      "/dev/video3"
    ],
    "preferred_capture_path": "/dev/video2",
    "evidence_status": "not_evaluated",
    "frame_captured": false,
    "advisory_only": true,
    "physical_command_enabled": false,
    "no_physical_command_generated": true
  }
]
```

## Data Lab / Reports

- Data Lab export: data_lab_export_20260515_133811_e1328a
- Reports export: ktr_summary-20260515-133812-e31198
- USB evidence files: usb_camera_capture_evidence.json, usb_camera_acceptance_summary.md, real_camera_acceptance_result.json

## Safety Boundary

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added.

- advisory_only=true
- physical_command_enabled=false
- no_physical_command_generated=true

## Validation

- uv run pytest -q: passed
- pnpm --dir frontend typecheck: passed
- pnpm --dir frontend build: passed
- python3 scripts/check_release.py: passed
- bash -n release/linux/start_istiklal_c2.sh: passed
- bash -n start_linux.sh: passed
- Manual smoke: /vision, /data-lab, /reports, /logs and real-camera/camera-host endpoints returned HTTP 200
