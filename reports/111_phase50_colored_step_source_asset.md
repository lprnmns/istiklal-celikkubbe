# Phase 50 - Colored STEP Source Asset

Authoritative source asset: `ktr1.step` in the project root.

The file is treated as the primary KTR digital twin source for the cockpit. `ktr1_binary.stl` remains engineering evidence only and is no longer the default hero model.

Conversion output:
- Browser asset: `frontend/public/assets/digital-twin/ktr1_colored_step_hero.glb`
- Manifest: `frontend/public/assets/digital-twin/ktr1_colored_step_hero_manifest.json`
- Source: `ktr1.step`
- Fallback used: `false`
- no_physical_command_generated=true

FreeCAD imported the STEP geometry as 136 solids. Headless FreeCAD did not expose the STEP presentation colors through `ViewObject.DiffuseColor`, so the cockpit asset uses reconstructed operator materials from part labels and geometry classes.
