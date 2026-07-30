# Digital Twin Telemetry Mapping

Safety invariant: `no_physical_command_generated=true`

## Mapping

`/api/digital-twin/state` now includes `telemetry_protocol`:

- `protocol_name`
- `protocol_version`
- `pico_connected`
- `telemetry_fresh`
- `last_heartbeat_age_ms`
- `pan_deg`
- `tilt_deg`
- `x_steps`
- `y_steps`
- `driver_enabled`
- `limit_state`
- `fault_state`
- `pose_source`

If Pico protocol telemetry includes pose, the digital twin labels pose as `telemetry`. If not, it keeps `tracker_estimate` or `fixture` and sets `telemetry_missing=true`.

## Boundary

The mapping is read-only. It never sends motor, fire, servo, GPIO, PWM, STEP/DIR, hardware-enable, `SPD`, `LZR`, or `STP` commands.

