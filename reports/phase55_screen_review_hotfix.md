# Phase 55 Screen Review Hotfix

## Issue Observed

The user-provided cockpit screenshot showed the Phase 55 model in the dark Showcase World default view. In that view the camera angle, dark tactical lighting, and optional overlays made the front launcher/camera mechanism hard to read, even though the FreeCAD reference shows the STEP/STL model with clear weapon detail.

The camera panel also depended on backend camera evidence and did not expose a direct browser/laptop camera selector for development testing.

## Fixes Applied

- `/cockpit` now defaults to FreeCAD Match mode instead of Showcase World when no explicit `mode=` query is provided.
- FreeCAD Match keeps tactical FOV/target overlays off by default so the model is not visually covered.
- CAD edge outlines are stronger in FreeCAD Match mode to better resemble the FreeCAD view.
- Orthographic framing was tightened so the model appears larger while preserving full silhouette.
- The camera panel now enumerates browser `videoinput` devices with `navigator.mediaDevices.enumerateDevices()`.
- The operator can select a camera, connect it with `getUserMedia()`, refresh the list, or stop the local preview.
- Browser laptop preview is explicitly labelled as local development camera evidence, not competition USB acceptance and not a physical command path.

## Safety Boundary

- This change is frontend visualization only.
- No tracking/detection pipeline behavior was modified.
- No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path was added.
- No serial TX or Pico command sender was added.
- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

