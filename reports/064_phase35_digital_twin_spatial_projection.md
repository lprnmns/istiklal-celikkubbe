# Phase 35 Digital Twin Spatial Projection

Safety invariant: `no_physical_command_generated=true`

## Completed

- The cockpit digital twin now renders a read-only pan/tilt turret pose, optical axis, and camera FOV frustum.
- Vision detections are projected into the 3D situational awareness scene through a deterministic bbox-to-scene mapper.
- The projection contract exposes FOV, camera-to-launcher calibration offsets, projection source, depth source, and read-only safety fields.
- The practical mechanical camera/firing-axis vertical offset is represented as `camera_to_launcher_offset_z_mm=30`.
- Lateral offset remains configurable as `camera_to_launcher_offset_y_mm`, defaulting to `0`.
- Target markers include id, class, confidence, selected state, and relative depth band.
- Live, fixture, and replay sources remain visibly labelled; fixture and replay data are not presented as telemetry.
- Person safety/no-go state is rendered as a red blocked overlay when active.

## KTR Value

The digital twin mirrors live turret state for operator situational awareness and remote monitoring. Camera detections are projected into a 3D operational scene, so the operator can understand where an observed target lies in the camera frustum.

Relative depth is estimated from bbox scale unless calibrated range data exists. Larger bboxes are shown closer; smaller bboxes are shown farther. This is an estimate for visualization and evidence, not a physical fire solution.

The 3 cm camera/launcher mechanical offset is represented as a calibration parameter instead of being hard-coded in rendering logic. This supports later mechanical recalibration without rewriting the visualization.

## Safety Boundary

This phase adds no motor, fire, servo, GPIO, PWM, STEP/DIR, serial TX/write, or hardware-enable path. The digital twin remains read-only and optional. It can be disabled without affecting balloon tracking, camera streaming, Pico state, safety gates, logs, or reports.

Canonical proof fields:

- `no_physical_command_generated=true`
- `physical_command_enabled=false`
- `digital_twin_command_authority=false`
- `projection_is_calibrated=false`
- `depth_source=bbox_area_relative_estimate`

## Validation

- `uv run pytest -q`: passed
- `pnpm --dir frontend typecheck`: passed
- `pnpm --dir frontend build`: passed
- `python3 scripts/check_release.py`: passed
- `bash -n release/linux/start_istiklal_c2.sh`: passed
- `bash -n start_linux.sh`: passed

Manual smoke:

- `/cockpit`: HTTP 200
- `/debug`: HTTP 200
- `/evidence`: HTTP 200
- `/api/digital-twin/state`: HTTP 200, `schema_version=phase35.1`, `no_physical_command_generated=true`
- `/api/digital-twin/replay/latest`: HTTP 200, `no_physical_command_generated=true`
- `/api/person-safety/status`: HTTP 200, `no_physical_command_generated=true`
