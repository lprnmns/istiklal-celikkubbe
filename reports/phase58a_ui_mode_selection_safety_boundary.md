# Phase 58A UI Mode Selection Safety Boundary

## Scope

Phase 58A adds a launch-screen UI profile selector:

- Operator Mode routes to `/cockpit?ui=operator`
- Engineer Mode routes to `/cockpit?ui=engineer`
- Full Engagement / Competition Mode is shown as locked/disabled

This is a frontend UI-profile and routing change only.

## Safety Boundary

- `physical_command_enabled=false` remains required.
- `serial_tx_enabled=false` remains required.
- `no_physical_command_generated=true` remains required.
- No motor, fire, servo, GPIO, PWM, STEP/DIR, hardware-enable or serial TX path was added.
- Engineer Mode only changes visibility of advanced/debug UI sections.
- Operator Mode is the default when `/cockpit` has no `ui` query parameter.

## Route Behavior

- `/cockpit?ui=operator`: operator profile badge is shown and developer-heavy cockpit sections remain collapsed by default.
- `/cockpit?ui=engineer`: engineer profile badge is shown and existing advanced/debug cockpit sections are available.
- `/cockpit/world`: unchanged 3D world route behavior.

## Acceptance Notes

The launch screen keeps the existing background and system check cards. UI profile selection is visually separate from the safety mission mode `DRY-RUN / NO TX`.

## Evidence

Screenshots:

- `reports/screenshots/phase58a_ui_mode_selection/landing_ui_mode_selector.png`
- `reports/screenshots/phase58a_ui_mode_selection/cockpit_operator_badge.png`
- `reports/screenshots/phase58a_ui_mode_selection/cockpit_engineer_badge.png`

Route checks:

- `/` -> 200
- `/cockpit?ui=operator` -> 200
- `/cockpit?ui=engineer` -> 200
- `/cockpit/world` -> 200

Validation:

- `uv run pytest -q` passed
- `pnpm --dir frontend typecheck` passed
- `pnpm --dir frontend build` passed
- `python3 scripts/check_release.py` passed
- `bash -n release/linux/start_istiklal_c2.sh` passed
- `bash -n start_linux.sh` passed
