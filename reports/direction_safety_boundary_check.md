# Direction Safety Boundary Check

- Generated at: 2026-05-14T19:36:53
- Source commit: d178c84
- Safety invariant: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false
- advisory_only=true
- physical_command_enabled=false
- no_physical_command_generated=true

## Result

Direction simulator endpoints, Data Lab exports and KTR exports produce advisory mapping/evidence only. No motor jog, step pulse, DIR pin change, PWM/GPIO output, serial TX/write, Pico/Arduino command, fire/trigger/shoot or hardware enable path was added.

no_physical_command_generated=true
