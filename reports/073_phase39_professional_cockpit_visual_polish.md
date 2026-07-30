# Phase 39 Professional Cockpit Visual Polish

Safety invariant: `no_physical_command_generated=true`

Phase 39 focuses on KTR/presentation readiness:
- Top bar now exposes Phase 39 / KTR demo state.
- Camera panel avoids misleading live/USB claims.
- Target labels clamp inside the frame.
- Digital twin fallback is a red/white turret-like model, not a generic cylinder.
- Bottom panels remain data-driven and represent offline hardware as controlled yellow states.
- `/cockpit?ktr_demo=1` renders without changing backend safety state.

Missing physical hardware is not treated as a phase failure:
- USB camera: `OFFLINE_EXPECTED`
- Pico: `OFFLINE_EXPECTED`
- Physical movement/fire: disabled and not tested

