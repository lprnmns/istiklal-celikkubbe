# Phase 48 Camera to 3D Projection Consistency

Phase 48 reuses the Phase 47 mapping function:

`frontend/src/utils/engagementGeometry.ts::mapDetectionToEngagementGeometry`

Mapping behavior:
- x_norm < 0.5 maps target to the left side of camera HUD and 3D FOV.
- x_norm > 0.5 maps target to the right side of camera HUD and 3D FOV.
- y_norm controls vertical placement.
- bbox_area_relative controls relative depth.

For the fixture case, x_norm around 0.71-0.76 appears right of FOV center, y_norm around 0.43-0.54 appears near mid elevation, and the target appears around mid/10 m range band.

This is not a calibrated metric range solution.

