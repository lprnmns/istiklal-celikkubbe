# Digital Twin Safety Boundary

Safety invariant: `no_physical_command_generated=true`

The digital twin is not a control surface. It is an optional read-only
observability and evidence layer.

Allowed:

- Read existing runtime state.
- Render pose, target, tracker, fire gate, camera mode, Pico state, queue depth,
  and latency diagnostics.
- Load deterministic replay JSON and label it as replay.
- Export KTR evidence.

Forbidden:

- Motor movement.
- Servo trigger.
- Fire command generation.
- GPIO, PWM, STEP/DIR writes.
- Hardware enable.
- Serial TX/write.
- Replacing the existing tracker/camera/Pico/safety/log/report behavior.

If live pose is unavailable, the panel must display `tracker_estimate` or
`fixture`. Fixture data must never be labelled as telemetry.
