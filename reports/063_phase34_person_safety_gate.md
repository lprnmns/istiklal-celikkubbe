# Phase 34 Person Safety Gate

Safety invariant: `no_physical_command_generated=true`

## Completed

- Added an additional software-only person safety gate.
- Person classes are `person`, `human`, and `insan`.
- Config fields are `person_safety.enabled`, `confidence_threshold`, `hold_ms`, and `clear_after_ms`.
- Decision/fire gate now blocks with `FIRE_BLOCKED: PERSON_DETECTED` while active.
- Cockpit engagement panel shows `PERSON SAFETY ACTIVE` and last person confidence.
- `/api/person-safety/status` exposes the read-only gate state.

## Important Boundary

This gate is an additional software safety layer. It does not replace emergency
stop, operator supervision, mechanical safety, range discipline, or existing
hardware fire interlocks. It never enables fire; it can only add a block reason.

## KTR Summary

The prototype has been validated in 5-10 m fixed and moving balloon tests using
parkour-like autonomous tracking and engagement flow. The balloon is a surrogate
integration target for camera, YOLO, tracker, motion, and fire-gate validation.
Final competition classes can be swapped through the YOLO model interface.

Human/person detection blocks engagement as `PERSON_DETECTED`, producing
report-ready layered safety evidence without generating any physical command.
