# Phase 45 Truth Mode and Safety Labels

Phase 45 adds explicit truth-mode presentation in the cockpit.

## Truth Modes

- `KTR_DEMO_FIXTURE`: deterministic KTR view, labelled `KTR Fixture - Not Live Target`, truth=`fixture`.
- `DEV_REAL_CAMERA`: laptop/internal camera can show a real development frame, labelled `Laptop Camera Dev - Real Frame`, truth=`real_frame_dev`.
- `LIVE_SYSTEM`: only displayed when external USB camera and Pico telemetry are actually available.
- `OFFLINE_FIXTURE`: controlled offline/fixture state when hardware is not present.

## Person Safety Label Rule

The cockpit no longer claims person safety is clear when the classifier status is unavailable. It displays:

- `Person Blocked` when a person/human class is active.
- `No-Fire Ready` only when the software gate is enabled and returns clear.
- `Person Check N/A` when detector availability cannot justify a clear claim.

Fire remains blocked/no-fire in development and KTR fixture modes.
