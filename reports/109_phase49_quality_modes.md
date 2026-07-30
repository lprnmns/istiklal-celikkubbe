# Phase 49 - Quality Modes

The cockpit now supports explicit render quality modes:

- `quality=high`: QUALITY HIGH / 30 FPS TARGET
- `quality=balanced`: QUALITY BALANCED / 15 FPS CAP
- `quality=low`: QUALITY LOW / 10 FPS CAP

Routes:

- `/cockpit?quality=high`
- `/cockpit?quality=balanced`
- `/cockpit?quality=low`
- `/cockpit?ktr_demo=1&quality=high`

All modes keep the real KTR GLB model visible. Low mode reduces rendering cost but does not replace the real asset with unrelated procedural geometry.

The 3D render loop remains capped, tab-hidden rendering is skipped, raw STL is not parsed in the browser, and camera/perception UI can be reduced with `perception=off`.

no_physical_command_generated=true

