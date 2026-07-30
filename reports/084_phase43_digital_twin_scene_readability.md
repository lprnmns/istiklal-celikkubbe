# Phase 43 Digital Twin Scene Readability

The 3D digital twin panel was adjusted to communicate a clearer operator scene rather than a small debug widget.

Scene readability changes:

- The camera view was moved to a front-right/top perspective.
- The simplified turret representation was enlarged so it occupies a more readable portion of the panel.
- In KTR demo mode, the cockpit truthfully uses a polished `STL-derived simplified digital twin` visual while preserving the real STL asset evidence separately.
- FOV opacity was reduced and boundary lines were softened so the FOV no longer dominates or hides the turret body.
- Ground grid, horizon line and range rings were added as lightweight depth cues.
- Camera optical axis, launcher/namlu reference axis, target projection ray and 30 mm camera-to-launcher offset remain visible.
- Target marker size continues to follow relative depth band: near targets appear larger, far targets smaller.

Truth boundary:

- Relative depth remains a visual estimate derived from bbox scale unless calibrated range telemetry exists.
- Launcher/namlu reference axis is explicitly visual-only and does not create a physical command.
- Pose source is still labelled as telemetry, tracker estimate, replay fixture or fixture according to the available state.

Safety boundary preserved: `no_physical_command_generated=true`.
