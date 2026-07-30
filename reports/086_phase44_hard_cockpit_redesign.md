# Phase 44 Hard Cockpit Redesign

Phase 44 replaces the Phase 43 cockpit presentation instead of continuing incremental polish. The live `/cockpit` route now uses a reference-grade C2 layout: a compact full-width command header, a 50/50 hero area for Camera HUD and 3D Digital Twin, compact mission cards, and one global safety strip.

## Phase 43 Issue

- Header was badge-heavy and read like a developer dashboard.
- Main panels did not dominate the viewport.
- Bottom cards repeated low-level status strings and looked like debug boxes.
- Safety wording appeared in too many places instead of one authoritative strip.

## Phase 44 Fix

- Header badges were converted into compact C2 status cards: profile, system, safety, camera, Pico, model, and performance.
- The cockpit route now bypasses the general AppShell sidebar/header so `/cockpit` renders as a dedicated full-screen operator console.
- The main grid is now two equal operational panels with fixed screenshot-stable height.
- Bottom mission cards are constrained to short operator summaries.
- The global safety strip remains the only prominent command-boundary statement.

## Evidence

Screenshot evidence is generated under:

`reports/screenshots/phase44_hard_cockpit_redesign/`

Safety invariant: `no_physical_command_generated=true`. This phase is UI/UX/performance only and does not add motor, fire, servo, GPIO, PWM, STEP/DIR, hardware-enable, or serial TX paths.
