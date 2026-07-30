# Phase 50 - Projection Overlay Alignment

The Phase 50 digital twin keeps the existing bbox-to-FOV mapping behavior:
- `x_norm > 0.5` projects to the right side of the FOV.
- `x_norm < 0.5` projects to the left side of the FOV.
- `y_norm < 0.5` projects upward.
- `y_norm > 0.5` projects downward/mid.
- Larger bbox area projects nearer.
- Smaller bbox area projects farther.

KTR fixture target:
- x_norm: approximately `0.71-0.76`
- y_norm: approximately `0.43-0.54`
- depth: `mid`

The overlay shows:
- cyan camera axis from the estimated camera anchor
- yellow launcher axis from the estimated launcher anchor
- target marker inside/near the camera FOV
- 30 mm camera-to-launcher offset annotation

All depth is labelled as relative unless calibrated range data exists.

no_physical_command_generated=true
