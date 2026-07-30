# Digital Twin Replay Evidence

Safety invariant: `no_physical_command_generated=true`

Phase 33 replay mode loads `/api/digital-twin/replay/latest` and animates target
and turret pose in the Three.js panel. The UI labels this as `REPLAY`, not live
telemetry.

Replay is for jury evidence, debugging, and deterministic development when the
physical prototype is not attached. It does not generate motor, fire, servo,
GPIO, PWM, STEP/DIR, hardware enable, or serial TX/write commands.

Current replay fixture:

- Run: `phase32_fixture_balloon_tracking_001`
- Source: `fixture_deterministic_mock`
- Mode: `replay`
- Pose source: `fixture`
- Fire state: `REPLAY_NO_FIRE`
