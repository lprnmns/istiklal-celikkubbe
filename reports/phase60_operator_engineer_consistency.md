# Phase 60 Operator / Engineer Consistency

## Summary

Phase 60 separates the cockpit presentation language by UI profile.

- `/cockpit?ui=operator` uses a clean operator view with camera, 3D world, operation strip, radar, log and compact system health.
- `/cockpit?ui=engineer` keeps technical controls in tabs: camera, detection model, motor/PID, 3D calibration and logs/evidence.

## Operator Mode

- Debug asset controls, PID controls, threshold controls, yaw/pitch sliders and developer details are hidden from the main operator surface.
- Camera copy is simplified to operator-safe labels such as `Kamera Önizleme Aktif`, `Algılama Aktif`, `Hedef Verisi: Simülasyon/Offline` and `Fiziksel Komut Kapalı`.
- Backend offline state is shown as a compact pill: `Backend: Offline — local preview active`.
- System health is reduced to camera, microcontroller, digital twin and physical command status.

## Engineer Mode

- Technical controls remain available in the engineer tab panel.
- Detection threshold panel shows active value, pending value, last apply time and apply status.
- Motor/PID panel shows active values, pending values, last apply time and preview/apply status.

## Evidence

Screenshots:

- `reports/screenshots/phase60_operator_engineer_consistency/operator_clean.png`
- `reports/screenshots/phase60_operator_engineer_consistency/engineer_tabs.png`

