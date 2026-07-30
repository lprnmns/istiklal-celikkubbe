# Phase 31/32 Digital Twin Foundation

Safety invariant: `no_physical_command_generated=true`

## Scope Completed

- Phase 31 state contract was added at `reports/digital_twin_state_contract.json`.
- Phase 31 event contract was added at `reports/digital_twin_event_contract.md`.
- Phase 31 target model inventory was added at `reports/target_model_asset_inventory.md`.
- Phase 32 read-only backend API was added under `/api/digital-twin/*`.
- Phase 32 optional cockpit viewer was added as an isolated digital twin panel.
- Phase 32 deterministic fixture/replay data was added for device-unavailable development.
- Phase 32 model path convention was added under `frontend/public/models/...`.

## Safety Boundary

The digital twin service reads existing runtime state and deterministic fixtures.
It does not start the camera, run YOLO, open Pico/serial, send motor commands,
move a servo, fire, write GPIO/PWM, pulse STEP/DIR, or enable hardware. The API
state and replay outputs include `no_physical_command_generated=true`.

## KTR Value

The new layer gives jurors a live, report-ready visual explanation of camera,
target, tracker, actuator pose, and safety boundary state. It supports:

- Architecture evidence: camera to decision to Pico to actuator mirror.
- Software quality evidence: explicit schema, fixture replay, and tests.
- Safety evidence: read-only UI and command-authority false invariant.
- Debug evidence: camera/source/target/tracker/fire-block status in one panel.

## Phase Stop

Implementation stops before Phase 33. This means no class-specific 3D target
binding, no projection calibration, and no competition target semantic mapping
were implemented in this pass.
