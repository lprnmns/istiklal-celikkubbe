# Phase 56 Visual Noise Cleanup

Status: implemented.

Removed from Clean / Showcase mode:
- Multiple camera-to-target rays.
- Always-on launcher-axis extension lines.
- Debug grid dominance.
- Repeated target labels.

Mode behavior:
- Clean: realistic world, KTR model, selected target, one subtle engagement ray.
- Tactical: FOV frustum, camera axis, launcher axis, selected target, one engagement ray, no-go zone when relevant.
- Debug: helper axes, debug target rays, labels, anchor names, and range/grid diagnostics.

The FOV volume and launcher engagement ray are visually distinct: FOV uses cyan dashed geometry; primary engagement ray uses a single yellow line.

