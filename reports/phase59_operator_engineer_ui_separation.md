# Phase 59 Operator / Engineer UI Separation

## Summary

Phase 59 separates the cockpit into two UI profiles:

- `/cockpit?ui=operator`: clean operator task screen.
- `/cockpit?ui=engineer`: technical settings and calibration screen.

The shared top status bar remains visible in both modes and now includes the active UI profile. The mode is visualization/UI-only and does not alter safety or hardware command state.

## Operator Mode

Operator mode now emphasizes:

- Live camera panel.
- Camera selection, refresh, connect, stop, fullscreen.
- YOLO ON/OFF state.
- Selected target badge.
- 3D digital twin panel with only View and Full 3D World controls.
- Operation summary strip:
  - selected target
  - class
  - confidence
  - bearing/elevation
  - depth
  - tracking state
  - fire gate
  - person safety
- Lower operational cards:
  - Sahne Planı / Radar
  - Operator Log
  - System Health

Operator mode hides the main-screen developer controls:

- asset selector
- yaw/pitch preview sliders
- PID settings
- detection threshold slider
- developer/debug drawer
- evidence panel
- material/asset debug labels
- geometry/debug buttons

## Engineer Mode

Engineer mode keeps the camera and 3D view visible, then moves technical controls into a tabbed panel:

- Kamera Ayarları
- Algılama Modeli
- Motor / PID
- 3D Kalibrasyon
- Loglar / Evidence

Only the selected tab content is shown, preventing the previous stacked technical dashboard.

## 3D Operator Cleanup

In operator mode:

- FOV stays available as the simplified mission visualization.
- Unselected target clutter is hidden from the 3D world.
- Selected target marker only appears after target selection.
- Primary engagement ray only appears after target selection.
- Developer asset/pose/material controls are hidden.

Engineer/world modes preserve diagnostic controls for calibration and debugging.

## Screenshots

Saved under:

`reports/screenshots/phase59_operator_engineer_modes/`

Key screenshots:

- `operator_clean_task_screen.png`
- `operator_3d_clean_overlay.png`
- `engineer_tabbed_technical_panel.png`
- `engineer_detection_tab.png`
- `safety_no_tx_status.png`
