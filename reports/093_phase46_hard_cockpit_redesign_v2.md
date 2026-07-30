# Phase 46 Hard Cockpit Redesign v2

Phase 46 is a hard visual redesign of the accepted Phase 45 cockpit. The main change is to stop presenting the raw STL-derived visual as the primary command scene. The STL remains engineering evidence, while the cockpit now shows a tactical simplified digital twin designed for operator readability.

## What Changed

- Main `/cockpit` and `/cockpit?ktr_demo=1` routes remain the real cockpit routes; no screenshot-only page was created.
- Header and mission cards use short presentation labels instead of raw internal values.
- Camera HUD hides raw device/backend strings from the main image area.
- Digital twin panel uses `STL-derived tactical twin` / CAD-reference wording and tactical simplified geometry.
- Scene text boxes were reduced and moved away from the turret/target.

## Safety Boundary

Frontend/UI/visualization only. No tracking, detection, motor, fire, servo, GPIO, PWM, STEP/DIR, hardware-enable, or serial TX path was changed or added.

`no_physical_command_generated=true`
