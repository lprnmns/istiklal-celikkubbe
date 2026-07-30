# Phase 53 - Canvas Framing and Resize Fix

The 3D viewer now treats model framing as independent from dashboard card layout.

- Box3 and bounding radius are used to frame the STEP-derived model.
- Resize events refit the camera around the model.
- Orthographic FreeCAD Match mode uses larger margins to avoid clipping.
- World viewer height is no longer reduced by lower cockpit cards.

Acceptance target: the model remains centered, large and fully visible instead of falling to the bottom of a small viewport.
