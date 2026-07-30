# Phase 55 Pivot / Anchor Report

Source asset: `work/ktr1.step`

Generated kinematics metadata: `frontend/public/assets/digital-twin/ktr1_kinematics.json`

## Pivot Nodes

- `yaw_pivot`
  - Position: `[0.0, 1.20311, 0.52561]`
  - Axis: `[0, 1, 0]`
  - Method: heuristic from yaw-group and static-root bounding boxes after FreeCAD STEP import.
  - Validation status: visualization estimate, not mechanically certified.

- `pitch_pivot`
  - Position: `[0.01526, 0.90761, -0.01325]`
  - Axis: `[1, 0, 0]`
  - Method: heuristic center of front pitch/camera/launcher candidates.
  - Validation status: visualization estimate, not mechanically certified.

## Anchors

- `camera_origin`: `[0.49905, 0.73257, 1.03336]`
- `camera_axis`: `[0, 0, -1]`
- `launcher_origin`: `[-0.30522, 0.68434, 1.26404]`
- `launcher_axis`: `[0, 0, -1]`
- `target_projection_anchor`: `[0.49905, 0.73257, 0.03336]`
- `no_go_zone_anchor`: `[1.62, 0.18, -3.75]`

## Offset

The camera-to-launcher visualization offset remains `30 mm`. It is represented in `ktr1_kinematics.json` as:

```json
{
  "camera_to_launcher_mm": [30, 0, 0]
}
```

## Honesty Boundary

The installed FreeCAD import did not expose validated revolute joint definitions. The pivots and anchors above are explicitly authored as read-only visualization metadata and must be mechanically validated before being used as engineering calibration.

No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path, serial TX, or Pico command sender is added.

