# Phase 57: Safety & Startup Command Boundaries

To guarantee field operation safety, the Mission Startup screen enforces strict boundaries.

## Enforced Restrictions
1. **No Physical Movement**: Selecting diagnostics or checking ports does not send physical yaw/pitch displacement commands to step motor controllers.
2. **No Firing (Blocked Gate)**: The hardware fire relay remains blocked. No solenoid or trigger commands are generated.
3. **Operational Modes**:
   - `no_motion` & `motion_no_fire` run as safe, dry-run configuration modes.
   - `full_active` is locked and visually disabled unless explicit hardware safety gates (`physical_command_enabled === true`) are satisfied.
4. **Diagnostic Command Isolation**: Only query/telemetry status checks are triggered during startup. Step motor driver enablement (`DRV,1`) is isolated under a manually controlled action panel with confirmation.
