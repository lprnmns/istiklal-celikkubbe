# Phase 53 - 3D First Cockpit Layout Priority

Phase 53 changes the cockpit hierarchy so the REAL KTR 3D DIGITAL TWIN WORLD is the primary hero section after the status header.

- `/cockpit` no longer forces camera HUD and 3D viewer into a 50/50 top dashboard row.
- The 3D world is full width with `min-height: 720px` and preferred `height: 82vh`.
- Camera HUD and mission cards are moved below the 3D hero.
- Bottom cards no longer reduce or squeeze the 3D canvas.
- Page-level vertical scrolling is intentionally enabled.

Safety remains read-only: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`.
