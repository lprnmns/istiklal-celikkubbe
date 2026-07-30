# Person Safety Gate Summary

Safety invariant: `no_physical_command_generated=true`

The person safety gate watches existing YOLO/tracker detections for
`person`, `human`, or `insan` classes above the configured confidence threshold.
When active, the engagement state is blocked as:

`FIRE_BLOCKED: PERSON_DETECTED`

This is an additional software gate. It does not replace emergency stop,
operator supervision, mechanical protections, or existing fire policy checks.
It can only block; it cannot enable fire.
