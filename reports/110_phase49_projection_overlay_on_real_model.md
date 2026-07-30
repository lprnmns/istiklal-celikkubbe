# Phase 49 - Projection Overlay on Real Model

The Digital Twin panel overlays tactical geometry on the real KTR GLB hero model.

Overlay semantics:

- Camera axis: cyan ray from estimated camera anchor.
- Launcher axis: yellow ray from estimated launcher/barrel anchor.
- FOV: transparent cyan frustum.
- Target: yellow/orange marker placed by bbox-to-FOV mapping.
- Offset: 30 mm camera-to-launcher bracket annotation.
- Fire gate: blocked / no TX in current safe mode.

Projection behavior:

- x_norm around 0.71-0.76 maps the target to the right side of the FOV.
- y_norm around 0.43-0.54 maps the target around mid elevation.
- bbox_area_relative around 0.018-0.031 maps to mid relative depth.

The depth is a relative estimate from bbox area, not calibrated metric range.

no_physical_command_generated=true

