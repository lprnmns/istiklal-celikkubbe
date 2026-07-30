# Digital Twin State Mapping

Safety invariant: `no_physical_command_generated=true`

The mapper consumes existing backend/cockpit state only. It does not poll a
device for commands, start movement, write serial data, or change tracking.

| Source | Digital twin field | Source label |
| --- | --- | --- |
| Hardware telemetry pan/tilt steps | `device_pose.pan_deg`, `device_pose.tilt_deg` | `telemetry` |
| Motion/tracker estimate | `device_pose.pan_deg`, `device_pose.tilt_deg` | `tracker_estimate` |
| Deterministic fallback replay | `device_pose.*`, `target.*` | `fixture` |
| Vision latest balloon detection | `target.bbox`, `target.normalized_x/y` | live/read-only event |
| Auto tracker status | `tracker.state`, `tracker.latency_ms` | live/read-only event |
| Decision state | `engagement.fire_gate_state` | fire gate mirror only |
| Serial status | `runtime.queue_length`, `runtime.latency.serial_ack_rtt_ms` | read-only status |
| Pico telemetry | `runtime.pico_connection_state` | read-only status |

Replay data is labelled as replay and cannot be confused with live telemetry.
