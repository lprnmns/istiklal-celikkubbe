# Phase 56 Incremental Grouping Check

## Purpose

This checkpoint focuses only on the root model problem: the browser runtime must stop treating the CAD as a single visual mesh and must start exposing meaningful mechanical groups for the real digital twin.

## Current Diagnosis

- The web renderer is not the primary blocker.
- The STEP source contains the geometry and colors needed for the KTR visual model.
- The blocker is semantic loss during STEP-to-runtime conversion:
  - exact STEP assembly hierarchy is not resolved yet,
  - part roles are inferred from FreeCAD labels and bounding boxes,
  - yaw/pitch pivots are still draft calibration values,
  - many repeated bearing/fastener parts require manual validation.

## Grouping Correction Applied

The previous heuristic assigned too many front/upper parts to `pitch_cradle`.

Updated grouping rules:

- `static_base`: lower body/platform parts.
- `yaw_rotor`: upper side body, side covers, central carrier body and large cover compounds. This is the group expected to rotate with the physical X/azimuth step motor.
- `pitch_cradle`: launcher/camera/front elevation mechanism candidates. This is the group expected to rotate with the physical Y/elevation step motor.
- `pitch_drive`: pitch motor/gear candidates such as upper gear box, worm gear, gear 20 and NEMA17.
- `launcher_assembly`: launcher/namlu candidate.
- `camera_assembly`: camera module candidate.
- `candidate_review_required`: bearings/fasteners whose moving role cannot be trusted from labels alone.

Current generated counts:

- `static_base`: 2
- `yaw_rotor`: 37
- `pitch_cradle`: 16
- `pitch_drive`: 4
- `launcher_assembly`: 1
- `camera_assembly`: 1
- `candidate_review_required`: 81

## Pivot Correction Applied

- Yaw/X motor pivot remains a draft yaw ring/body center candidate.
- Pitch/Y motor pivot is no longer derived from the whole pitch group bounding box.
- Pitch pivot now uses the `Axel` part as the shaft/axis candidate:
  - runtime axis: `[1, 0, 0]`
  - pivot X normalized to centerline because any X value on a line parallel to X represents the same rotation axis.

## Still Not Final

This is still not mechanically final. The next required control step is browser-side yaw/pitch preview validation:

- yaw preview should rotate only `yaw_rotor` and children/candidates,
- pitch preview should rotate only `pitch_cradle`, `pitch_drive`, `launcher_assembly`, and `camera_assembly`,
- `static_base` must remain fixed,
- camera and launcher anchors must stay rigidly attached to pitch motion,
- uncertain bearing/fastener parts must be reviewed from FreeCAD selection or manually assigned.

## Safety

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
- yaw/pitch controls remain visualization-only preview controls.
