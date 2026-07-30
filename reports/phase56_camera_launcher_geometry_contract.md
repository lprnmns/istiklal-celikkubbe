# Phase 56 Revision - Camera Launcher Geometry Contract

Visualization contract:
- `camera_anchor` is the origin of the camera FOV volume.
- `launcher_muzzle_anchor` is the origin of the selected-target engagement ray.
- `launcher_muzzle_anchor` is manually calibrated as `launcher_origin + launcher_forward * 0.42`.
- The selected target position is derived from detection center, FOV basis, and estimated balloon depth.
- Clean/Tactical modes must not render unrelated extra target rays.

Read-only boundary:
- This geometry is a virtual preview.
- It does not command motors.
- It does not command fire.
- It does not send Pico serial traffic.

