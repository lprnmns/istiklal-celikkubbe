# Phase 33 Digital Twin Live-State Mapping

Safety invariant: `no_physical_command_generated=true`

## Completed

- Digital twin state now maps the cockpit/backend read-only state stream.
- Pose is labelled with `pose_source`: `telemetry`, `tracker_estimate`, or `fixture`.
- The panel shows live vs replay vs fixture/estimated sources explicitly.
- Runtime state includes queue length, camera mode, Pico connection state, selected target id, and latency metrics.
- Replay mode loads `/api/digital-twin/replay/latest` and animates target/turret motion as non-live evidence.

## Mapping Summary

| Digital twin field | Source | Safety note |
| --- | --- | --- |
| `device_pose.pan_deg`, `tilt_deg` | read-only hardware telemetry if available; otherwise tracker/motion estimate | never sends motor commands |
| `device_pose.pose_source` | mapper classification | prevents fixture/estimate being presented as telemetry |
| `target.bbox`, `normalized_x`, `normalized_y` | latest vision event already held by backend | does not run inference from digital twin |
| `tracker.state` | auto tracker read-only status | tracker behavior is not rewritten |
| `engagement.fire_gate_state` | latest decision/person safety state | digital twin has no fire authority |
| `runtime.queue_length` | serial status read-only queue depth | no serial TX/write |
| `runtime.pico_connection_state` | Pico telemetry read-only mirror | no Pico command path |
| `runtime.latency` | latest event/tracking/serial timing values | diagnostic only |

## Logs Added

- `digital_twin.state_stream_mapped`
- `digital_twin.replay_loaded`
- `digital_twin.panel_rendered`

Every log uses the canonical wording that no physical command is generated.

## Boundary

The digital twin remains an optional cockpit evidence layer. Disabling the panel
does not affect camera streaming, YOLO/tracker state, Pico state, safety gates,
logs, reports, motor control, or fire request behavior.
