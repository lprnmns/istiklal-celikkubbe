# Phase 56 Tactical Overlay Cleanup

Implemented:
- Showcase mode no longer enables the camera FOV by default. It can still be shown through Tactical mode or `fov=1`.
- Tactical mode keeps camera FOV distinct from the launcher-to-target ray.
- Clean/Tactical modes render one primary engagement ray only when a target is explicitly selected.
- Unselected live detections remain red markers; selected target remains highlighted separately.
- Target marker radius now scales more strongly with bbox area and estimated range.

Current visual rules:
- Camera FOV: cyan transparent frustum from camera anchor.
- Primary engagement ray: amber/yellow thick ray from launcher muzzle anchor to selected target.
- Secondary detections: red balloon markers without engagement ray.
- Debug-only helper rays stay out of Clean/Tactical modes.

