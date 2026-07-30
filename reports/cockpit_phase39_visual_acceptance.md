# Phase 39 Visual Acceptance

Safety invariant: `no_physical_command_generated=true`

Acceptance notes:
- Camera panel does not claim live camera without real frame evidence.
- Fixture-only overlay is labelled as not real camera evidence.
- Target labels are clamped inside the camera frame.
- Digital twin uses a manifest-backed red/white procedural fallback because no real model asset exists in the repository.
- Offline USB/Pico states are yellow controlled states, not critical errors.
- `/cockpit?ktr_demo=1` renders for stable KTR screenshots.
