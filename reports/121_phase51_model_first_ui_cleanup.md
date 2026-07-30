# Phase 51 - Model-first UI Cleanup

The right panel was changed from telemetry-first to model-first:

- View buttons are compact and edge-aligned.
- Target and geometry labels are hidden in Clean mode.
- Tactical labels are available only in Tactical mode.
- CAD Debug is an explicit tab and not the default.
- `Full 3D World` opens the `/cockpit/world` route.

Default route behavior:
- `/cockpit`: normal cockpit with camera + 3D world panel.
- `/cockpit/world`: nearly full-screen 3D world inspection mode.
- `/cockpit/world?quality=ultra`: presentation quality world route.

no_physical_command_generated=true
