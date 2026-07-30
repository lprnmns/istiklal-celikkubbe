# KTR Autonomous Balloon Test Summary

Safety invariant: `no_physical_command_generated=true`

The physical prototype is known to work in 5-10 m fixed and moving balloon
tests, including parkour-like autonomous tracking and engagement validation.
No new physical fire, motor, servo, GPIO, PWM, STEP/DIR, hardware-enable, or
serial-write test was performed for Phase 33/34.

The balloon is a surrogate target for integration tests. It validates the
camera, YOLO model interface, tracker, cockpit state, fire gate, and evidence
pipeline. Final competition classes can be swapped through the YOLO model
interface without changing the digital twin or person safety gate contract.

Person detection adds a layered software safety block:

`FIRE_BLOCKED: PERSON_DETECTED`

This improves KTR safety evidence while preserving the already-working tracker.
