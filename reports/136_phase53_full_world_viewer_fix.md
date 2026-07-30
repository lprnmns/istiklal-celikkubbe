# Phase 53 - Full 3D World Viewer Fix

`/cockpit/world` is the primary full-size inspection route.

- Viewer uses 90vh target height.
- No camera panel or bottom card row is rendered in world mode.
- FreeCAD Match mode remains the default for `/cockpit/world`.
- Showcase and Tactical modes are still available via query parameter.
- Browser fullscreen is available from the 3D toolbar.

Primary routes:

- `/cockpit/world?quality=ultra&mode=freecad`
- `/cockpit/world?quality=ultra&mode=showcase`
- `/cockpit/world?quality=ultra&mode=tactical`
