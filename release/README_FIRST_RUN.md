# ISTIKLAL C2 First Run

1. Start the console with `start_linux.sh` or `start_windows.bat`.
2. Open `http://127.0.0.1:8000`.
3. Go to `First Run`.
4. Select `release_candidate_ready` and run the acceptance check.
5. Fix dependency, writable folder, camera, model adapter or device discovery warnings.
6. Run `Self-Test`.
7. Generate the readiness/report pack from `Reports`.

Release candidate can run without Pico hardware or a production YOLO model. Competition rehearsal requires production model and verified Pico telemetry.

Safety invariant remains enforced during first run:

- DISARMED startup
- NO_FIRE policy
- dry_run=true
- hardware_enabled=false
- physical_command_enabled=false

First-run acceptance does not enable physical fire, motion, servo, STEP/DIR, PWM or GPIO output.
