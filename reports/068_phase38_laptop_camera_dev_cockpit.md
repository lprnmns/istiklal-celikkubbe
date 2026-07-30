# Phase 38 Laptop-Camera Development Cockpit

Safety invariant: `no_physical_command_generated=true`

Phase 38 supports cockpit development when the physical air-defense prototype is not present.

Expected hardware state for this phase:
- External USB camera: `OFFLINE_EXPECTED / DEVICE_NOT_PRESENT`
- Pico: `OFFLINE_EXPECTED / DEVICE_NOT_PRESENT`
- Pan/tilt/fire actuators: unavailable in offline development mode

Camera source decision:
- If `/dev/video2` or another external USB camera is not present, the cockpit may use `/dev/video0` or `/dev/video1` as a laptop/internal development camera.
- Laptop camera frames are valid for UI/cockpit development only.
- Laptop camera frames are not external USB camera acceptance evidence.
- Mock/surrogate frames remain clearly labelled as not real camera evidence.

The cockpit remains usable without the real device and does not mark expected missing hardware as a Phase 38 failure.

