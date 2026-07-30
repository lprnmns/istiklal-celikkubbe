# Phase 30.1 Camera Frame Acceptance Hotfix

## Decision

- Camera tooling status: partial
- Host camera acceptance status: partial
- Real camera frame evidence: partial
- Frame captured: False
- Device path: not_available
- v4l2 available: False
- ffmpeg available: True
- user_in_video_group: False
- Blocker reason: opencv_not_available

## Manual Host Recommendations

If tooling is missing:

```bash
sudo apt update
sudo apt install -y v4l-utils ffmpeg
```

If user is not in video group:

```bash
sudo usermod -aG video $USER
```

Group change requires logout/login or reboot.

## Competition Readiness

Competition readiness remains false unless production YOLO, accepted real camera frame evidence, Pico telemetry acceptance and current self-test are all satisfied.

## Safety

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added.

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
