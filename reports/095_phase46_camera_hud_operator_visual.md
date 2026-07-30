# Phase 46 Camera HUD Operator Visual

The Camera HUD was simplified to feel more like an optical operator view.

## Improvements

- Debug-like `device=` and `backend=` strings were removed from the visible HUD strip.
- Fixture and laptop dev modes use human-readable labels.
- The HUD keeps crosshair, FOV frame, lock indicator, target label, scan arcs and horizon/range curves.
- Target label remains compact: `ID #1 | BALON | confidence | depth`.
- Person check remains explicit and does not claim clear when unavailable.

## Truth Boundary

KTR fixture mode remains labelled as fixture and not live target evidence. Laptop camera mode remains development evidence, not competition USB acceptance.
