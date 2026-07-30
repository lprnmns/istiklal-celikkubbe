# Pico Real RX-only Safety Boundary

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added.

- serial_write_enabled=false
- command_tx_enabled=false
- tx_disabled=true
- physical_command_enabled=false
- no_physical_command_generated=true

DTR/RTS reset risk is documented for CDC ACM devices. No firmware reset command or startup command is sent.
