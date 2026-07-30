# Phase 47 BBox to FOV Projection Visual

The cockpit uses a deterministic frontend mapping function:

`mapDetectionToEngagementGeometry(input)`

Inputs:
- x_norm, y_norm
- bbox_area_relative
- fov_horizontal_deg, fov_vertical_deg
- camera_to_launcher_offset_z_mm

Outputs:
- target_scene_x
- target_scene_y
- target_scene_depth
- target_inside_fov
- launcher_axis_error_x
- launcher_axis_error_y
- engagement_status

For the KTR fixture example, x_norm=0.76 and y_norm=0.54 place the target to the right side of the camera FOV and slightly below/near center. BBox area controls relative depth: larger area appears nearer, smaller area appears farther. This is a relative display estimate, not calibrated metric range.

no_physical_command_generated=true.

