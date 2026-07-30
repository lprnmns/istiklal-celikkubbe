# Digital Twin Operator UI Summary

Safety invariant: `no_physical_command_generated=true`

The cockpit digital twin is now treated as a primary situational-awareness panel rather than a small debug widget.

Operator cues:
- Turret pose mirrors the read-only digital twin state.
- FOV frustum, optical axis and target projection estimates are visible.
- Target labels include ID, class, confidence and relative range band.
- Pose source is always labelled as TELEMETRY, TRACKER_ESTIMATE or FIXTURE.
- Person safety/no-go state is shown both in the camera HUD and digital twin scene.

The panel does not send commands and does not claim precise range unless calibrated telemetry exists.

