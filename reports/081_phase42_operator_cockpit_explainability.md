# Phase 42 Operator Cockpit Explainability

The cockpit is organized for KTR review and operator interpretation:

- `Cihaz Yöneticisi`: camera source, USB status, Pico status, STL-derived asset status and physical command status.
- `Model / Runtime`: active detector, class profile, tracker/projection source, confidence threshold and data source truth.
- `Hedef / Angajman`: selected target, class, confidence, direction, relative depth and fire gate result.
- `Scene Summary / Plan View`: FOV cone, target plan view and the 2D Detection to 3D Digital Twin Mapping micro-panel.
- `Replay & Evidence`: KTR demo mode, screenshot folder, asset manifest, camera truth contract and projection contract.
- `Operator Log`: fixture selection, USB/Pico offline expected state, STL asset decision, person safety state and no-TX evidence.

The operator reads the target state from confidence, normalized bbox center, direction and relative depth. Referee review is supported by the screenshot folder and report contracts generated in this phase.

`no_physical_command_generated=true`
