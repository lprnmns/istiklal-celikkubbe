# Phase 55 Kinematic Grouping

This report defines the visualization-only kinematic digital twin grouping for `work/ktr1.step`.

Important honesty note: the installed FreeCAD import preserved many named parts but did not expose a validated mechanical joint hierarchy. The groups below are derived from labels, bounding boxes and geometry roles, then used only for browser preview. They are not hardware commands.

- Generated GLB: `/assets/digital-twin/ktr1_kinematic_world_phase55.glb`
- Kinematics JSON: `/assets/digital-twin/ktr1_kinematics.json`
- Exact STEP hierarchy preserved: `False`

## Groups

- `static_root`: 2 nodes. `alt gövde`, `tabla`
- `yaw_group`: 105 nodes. `608zz rulman v1`, `608zz rulman v001`, `608zz rulman v002`, `608zz rulman v003`, `608zz rulman v004`, `608zz rulman v005`, `608zz rulman v006`, `608zz rulman v007`, `608zz rulman v008`, `608zz rulman v010`, `608zz rulman v011`, `608zz rulman v012`, `608zz rulman v013`, `608zz rulman v014`, `608zz rulman v015`, `608zz rulman v016`, `608zz rulman v017`, `608zz rulman v018`
- `pitch_group`: 29 nodes. `üst sol`, `üst dişli kutusu`, `üst sonsuz dişl`, `üst dişli 20`, `608zz rulman v090`, `608zz rulman v091`, `608zz rulman v092`, `608zz rulman v093`, `608zz rulman v094`, `608zz rulman v095`, `608zz rulman v096`, `608zz rulman v097`, `608zz rulman v098`, `608zz rulman v100`, `608zz rulman v101`, `608zz rulman v102`, `608zz rulman v103`, `608zz rulman v104`
- `camera_group`: 1 nodes. `kamera v3`
- `launcher_group`: 1 nodes. `Bileşen13`
- `decorative_static_covers`: 0 nodes. 

## Pivots

- `yaw_pivot`: position `[0.0, 1.20311, 0.52561]`, axis `[0, 1, 0]`, source `phase55_audit_bbox_heuristic`
- `pitch_pivot`: position `[0.01526, 0.90761, -0.01325]`, axis `[1, 0, 0]`, source `phase55_audit_front_group_bbox_heuristic`

## Anchors

- `camera_origin`: `{'position': [0.49905, 0.73257, 1.03336], 'direction': [0, 0, 1], 'source': 'camera label or manual fallback'}`
- `camera_axis`: `{'originNode': 'camera_origin', 'direction': [0, 0, 1]}`
- `launcher_origin`: `{'position': [-0.30522, 0.68434, 1.26404], 'direction': [0, 0, 1], 'source': 'launcher label/long-forward geometry or manual fallback'}`
- `launcher_axis`: `{'originNode': 'launcher_origin', 'direction': [0, 0, 1]}`
- `target_projection_anchor`: `{'position': [0.49905, 0.73257, 0.03336], 'source': 'camera origin forward projection'}`
- `no_go_zone_anchor`: `{'position': [1.62, 0.18, -3.75], 'source': 'existing visualization no-go volume anchor'}`

## Runtime Behavior

- Three.js loads the flat GLB node list, reparents nodes into runtime `static_root`, `yaw_pivot`, `yaw_group`, `pitch_pivot`, and `pitch_group` containers, then applies visualization-only preview rotations.
- Camera and launcher anchors remain in the pitch group, so the 30 mm offset, FOV, and target projection move rigidly during preview.
- Yaw/pitch sliders do not call backend APIs and do not send Pico, motor, fire, servo, GPIO, PWM, STEP/DIR, serial TX, or hardware-enable commands.

## Safety

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
