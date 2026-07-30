# Digital Twin BBox to Scene Mapping

Safety invariant: `no_physical_command_generated=true`

## Pure Function

Implementation: `backend/app/services/digital_twin_projection.py`

Function: `project_bbox_to_scene(...)`

Input forms supported:

- Pixel bbox: `x`, `y`, `w`, `h`
- Corner bbox: `x1`, `y1`, `x2`, `y2`
- Normalized center bbox: `normalized_center_x`, `normalized_center_y`, `normalized_width`, `normalized_height`
- Center/size bbox: `center_x`, `center_y`, `width`, `height`

## Mapping Rules

- Frame center maps to the optical axis.
- A bbox center on the right side of the camera frame maps to positive scene X.
- A bbox center on the left side maps to negative scene X.
- A bbox above frame center maps above the optical axis.
- A bbox below frame center maps below the optical axis.
- `azimuth_deg` is derived from horizontal FOV and signed normalized X.
- `elevation_deg` is derived from vertical FOV and signed normalized Y.
- Bbox area ratio is used as an inverse-depth cue.
- Larger bbox area maps closer.
- Smaller bbox area maps farther.

## Depth Semantics

`relative_depth` is display-only:

- `0.0` means visually near.
- `1.0` means visually far.
- `estimated_range_band` is one of `near`, `mid`, or `far`.

The system does not claim precise metric distance unless a future calibrated range method is added. Current depth source is `bbox_area_relative_estimate`.

## Calibration Parameters

- `camera_fov_horizontal_deg`
- `camera_fov_vertical_deg`
- `camera_to_launcher_offset_z_mm`
- `camera_to_launcher_offset_y_mm`

The Phase 35 mechanical revision sets `camera_to_launcher_offset_z_mm=30`, representing the practical 3 cm camera/firing-axis offset for visualization and evidence only.

