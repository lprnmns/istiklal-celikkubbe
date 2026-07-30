# Phase 47 CAD Reference vs Operator Twin

The project keeps `/assets/digital-twin/ktr1_binary.stl` as CAD/STL evidence. Phase 47 does not use that raw mesh as the primary cockpit visual because it reduced operator readability and made the scene look toy-like.

The cockpit now uses:

- Main view: CAD-referenced tactical engagement geometry.
- Evidence layer: STL/CAD asset preserved and reported.
- Operator explanation: camera FOV, launcher axis, target projection and offset are shown directly.

This is an honest visualization choice: the main panel is an operator explainability view, not an exact CAD simulation.

