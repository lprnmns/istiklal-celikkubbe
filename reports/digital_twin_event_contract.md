# Digital Twin Event Contract

Phase: 31/32

Safety invariant: `no_physical_command_generated=true`

The digital twin event stream is an evidence-only mirror. It is allowed to read
already-materialized runtime state and deterministic fixtures. It is not allowed
to start motors, fire, servo, GPIO, PWM, STEP/DIR, serial TX/write, or hardware
enable flows.

## Event Types

| Event | Source | Purpose | Command authority |
| --- | --- | --- | --- |
| `digital_twin.state.sampled` | `/api/digital-twin/state` | Captures the visual pose, target, tracker, camera, and safety boundary snapshot. | none |
| `digital_twin.assets.indexed` | `/api/digital-twin/assets` | Lists rig and target model slots with source hashes and conversion status. | none |
| `digital_twin.replay.fixture_generated` | `/api/digital-twin/replay/generate` | Writes deterministic replay evidence for KTR review. | none |
| `digital_twin.render.fallback` | frontend viewer | Records that WebGL failed and the UI switched to a text fallback. | none |

## Required Fields

Every digital twin event, replay export, and evidence report must include:

- `no_physical_command_generated=true`
- `digital_twin_read_only=true`
- `digital_twin_command_authority=false`
- `source`
- `timestamp_ms` or replay-local `t_ms`

## Error Semantics

Camera, Pico, model, WebGL, or fixture failures must degrade the digital twin
viewer only. Existing cockpit camera, tracker, Pico, safety, logs, and reports
behavior remains authoritative and must not be rewritten by the digital twin.

## KTR Evidence Value

The event contract is designed to support report-ready screenshots and markdown
summaries for architecture, software quality, safety, testing, and debugging
sections. It proves that the 3D layer is a live observability surface, not a
hidden command path.
