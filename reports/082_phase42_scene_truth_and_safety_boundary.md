# Phase 42 Scene Truth and Safety Boundary

Scene truth:

- KTR fixture mode is not live target evidence.
- Laptop camera development frames are separate from external USB camera acceptance.
- External USB camera is currently `OFFLINE_EXPECTED`.
- Pico is currently `OFFLINE_EXPECTED`.
- The selected visual asset is `REAL_STL`, displayed as an STL-derived digital twin visualization.

Safety:

- No motor/fire/servo/GPIO/PWM/STEP/DIR/hardware-enable path was added.
- No serial TX path was added.
- No Pico command is sent.
- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
