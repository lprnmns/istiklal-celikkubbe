# Motion Semantics Contract

## Screen/Image Semantics

- image_x_positive = right
- image_y_positive = down
- target_error_x = target_center_x - frame_center_x
- target_error_y = target_center_y - frame_center_y

## Required Camera Motion

- Target appears right -> pan_right
- Target appears left -> pan_left
- Target appears up -> tilt_up
- Target appears down -> tilt_down

## Expected Image Response

- Camera pan_right -> target should move left toward center
- Camera pan_left -> target should move right toward center
- Camera tilt_up -> target should move down toward center
- Camera tilt_down -> target should move up toward center

## Electrical/Mechanical Direction Mapping

- x_axis_multiplier = 1 means X positive matches camera_right.
- x_axis_multiplier = -1 means X positive is inverted relative to camera_right.
- y_axis_multiplier = 1 means Y positive matches camera_up.
- y_axis_multiplier = -1 means Y positive is inverted relative to camera_up.
- axis_swap=true means X/Y movement observation is inconsistent and requires manual retest.

## Safety Boundary

- advisory_only=true
- physical_command_enabled=false
- no_physical_command_generated=true
- No motor, servo, GPIO, PWM, STEP/DIR, TMC current, serial write, fire or hardware enable path is activated.
