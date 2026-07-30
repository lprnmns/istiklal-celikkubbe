# Layered Safety Architecture

Safety invariant: `no_physical_command_generated=true`

ISTIKLAL C2 safety is layered:

1. Operator supervision and field discipline.
2. Emergency stop and hardware-level safe state.
3. Runtime configuration gates: DISARMED, NO_FIRE, dry-run, hardware disabled.
4. Existing decision gates: enemy/friend, balloon, range, stable track, operator confirmation.
5. Person safety gate: `FIRE_BLOCKED: PERSON_DETECTED`.
6. Digital twin safety boundary: read-only visualization with no command authority.

The person safety gate is not the only safety layer. It adds a software block
when person/human detections are present, and every related report/log/export
uses `no_physical_command_generated=true`.
