# Phase 56 Kinematic Preview Simulation

This validates only browser-side digital twin preview math. It does not command hardware.

- Yaw pivot: `[0.02299, 0.0, 0.02735]`
- Pitch pivot: `[0.0, 0.52293, 0.63688]`
- Baseline camera-launcher distance: `0.838087`
- Max distance error under preview poses: `0.0`
- Camera/launcher rigid under preview: `True`

## Poses

| Pose | Yaw | Pitch | Camera | Launcher | Distance error |
|---|---:|---:|---|---|---:|
| neutral | 0 | 0 | `[0.49905, 0.73257, 1.03336]` | `[-0.30522, 0.68434, 1.26404]` | 0.0 |
| yaw_left | -30 | 0 | `[-0.06773, 0.73257, 1.13661]` | `[-0.87959, 0.68434, 0.93425]` | 0.0 |
| yaw_right | 30 | 0 | `[0.93828, 0.73257, 0.66055]` | `[0.3571, 0.68434, 1.26246]` | 0.0 |
| pitch_down | 0 | -10 | `[0.49905, 0.79823, 0.99093]` | `[-0.30522, 0.79079, 1.22648]` | 0.0 |
| pitch_up | 0 | 35 | `[0.49905, 0.46725, 1.0819]` | `[-0.30522, 0.29543, 1.2432]` | 0.0 |
| combined | 25 | 25 | `[0.90135, 0.54537, 0.78454]` | `[0.25217, 0.40417, 1.29545]` | 0.0 |

## Safety

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
