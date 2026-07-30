# Phase 25/26 Safety Boundary Check

- Generated at: 2026-05-14T19:23:56
- Source commit: 29e8507
- Safety invariant: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false
- canonical safety field: no_physical_command_generated=true
- physical_command_enabled=false
- advisory_only=true

## Forbidden Runtime Migration Guard

The following legacy physical/control tokens were audited only and were not migrated as runtime command fields:

- `SPD`: do not auto-port / manual safety gate required
- `STP`: do not auto-port / manual safety gate required
- `HOM`: do not auto-port / manual safety gate required
- `LZR`: do not auto-port / manual safety gate required
- `TMC_CURRENT`: do not auto-port / manual safety gate required
- `STEP`: do not auto-port / manual safety gate required
- `DIR`: do not auto-port / manual safety gate required
- `PWM`: do not auto-port / manual safety gate required
- `GPIO`: do not auto-port / manual safety gate required
- `FIRE`: do not auto-port / manual safety gate required
- `TRIGGER`: do not auto-port / manual safety gate required
- `SHOOT`: do not auto-port / manual safety gate required

## Result

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC enable/current, hardware enable or physical serial command path was added.

no_physical_command_generated=true
