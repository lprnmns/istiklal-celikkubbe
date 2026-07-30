# Phase 41 Camera Truth and Fixture Label Fix

The KTR demo cockpit now avoids ambiguous camera claims.

Camera truth rules:

- Real laptop camera mode is labelled `LAPTOP CAMERA DEV - REAL FRAME` only when image evidence is available and KTR demo mode is not forcing a fixture view.
- KTR demo mode is labelled `KTR DEMO FIXTURE - NOT LIVE TARGET`.
- Fixture mode is labelled `FIXTURE VIEW - NOT REAL CAMERA EVIDENCE`.
- External USB camera absence remains `USB OFFLINE_EXPECTED`.

The camera panel metadata strip shows source, selected device, backend, resolution, frame age and `evidence_truth`.

Target labels remain clamped inside the camera panel using bounded label coordinates and SVG text compression.

Safety: no physical command path was added. `no_physical_command_generated=true`.
