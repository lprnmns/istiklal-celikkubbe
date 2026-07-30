# Phase 56 Selected Target Engagement Ray

Status: implemented.

Primary rule:
- Clean and Tactical modes render exactly one primary engagement ray.
- The ray starts at `launcher_muzzle_anchor`.
- The ray ends at the selected target world position.
- Camera-to-target helper rays are hidden outside Debug mode.

Launcher muzzle anchor:
- Method: manually calibrated runtime anchor.
- Origin: `launcher_origin + launcher_forward * 0.42`.
- Label: manual calibrated.
- Purpose: visual-only engagement explanation.

No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path was added.

