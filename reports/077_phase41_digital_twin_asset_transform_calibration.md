# Phase 41 Digital Twin Asset Transform Calibration

The Phase 40 STL model remains the selected real asset:

- selected_asset_type: `REAL_STL`
- selected_asset_path: `/assets/digital-twin/ktr1_binary.stl`
- source_cad_path: `ktr1.step`

Phase 41 adds explicit read-only transform metadata for the STL scene:

- scale: `0.82`
- rotation_deg: `x=-90`, `y=0`, `z=180`
- position: `x=0`, `y=0.12`, `z=-0.35`
- camera_mount_anchor: `x=0`, `y=1.18`, `z=0.62`
- launcher_axis_anchor: `x=0`, `y=0.98`, `z=0.42`
- camera_to_launcher_offset_z_mm: `30`

Exact semantic anchors are not encoded in the STL, so the camera and launcher anchors are explicitly marked as estimated visualization overlays. They are not fire-control coordinates.

The FOV cone opacity was reduced and the launcher axis was separated from the camera FOV. Target projection now includes camera-to-target and aim-reference-only lines.

Safety: no physical command path was added. `no_physical_command_generated=true`.
