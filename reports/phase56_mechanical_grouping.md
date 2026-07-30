# Phase 56 Mechanical Grouping Draft

This is a draft grouping contract. It is not final mechanical truth until checked against the physical X/Y step motor mechanism and FreeCAD part selection.

- `static_base`: 2 parts
- `yaw_rotor`: 37 parts
- `pitch_cradle`: 16 parts
- `pitch_drive`: 4 parts
- `launcher_assembly`: 1 parts
- `camera_assembly`: 1 parts
- `candidate_review_required`: 81 parts
- `decorative_covers`: 0 parts
- `unclassified`: 0 parts

## Required Manual Validation

- Confirm static_base parts do not rotate with yaw.
- Confirm yaw_rotor contains every part moved by X/azimuth step motor.
- Confirm pitch_cradle contains every part moved by Y/elevation step motor.
- Confirm launcher_assembly and camera_assembly are physically attached to pitch_cradle.

## Safety

- Visualization-only.
- No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path.
- No serial TX.
- No Pico command sending.
