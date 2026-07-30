# Phase 35 Digital Twin Safety Boundary

Safety invariant: `no_physical_command_generated=true`

## Scope

Phase 35 is visualization, state mapping, and evidence only. It does not change the cockpit tracking pipeline, live camera path, Pico path, safety gates, logs, reports, or fire request behavior.

## Preserved Runtime Safety

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- `digital_twin_command_authority=false`
- `no_physical_command_generated=true`

## Forbidden Paths Not Added

- motor movement command generation
- fire command generation
- trigger servo command generation
- GPIO output path
- PWM output path
- STEP/DIR output path
- serial TX/write path
- hardware enable path

## Person Safety

If person safety is active, the 3D panel shows a red blocked/no-go overlay and reports `FIRE_BLOCKED: PERSON_DETECTED`. This remains an additional software safety gate and does not replace emergency stop, operator supervision, or mechanical safety.

## Evidence Interpretation

The digital twin can show live, estimated, fixture, or replay data. Fixture and replay data are explicitly labelled and never presented as real telemetry. Bbox projection is a relative visual estimate, not a calibrated ballistic or firing solution.

