# Real Camera Safety Boundary

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added. Camera diagnostics and frame capture are read-only host/perception evidence.

- advisory_only=true
- physical_command_enabled=false
- no_physical_command_generated=true
