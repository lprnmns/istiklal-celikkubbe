# Development Scripts

## UI Screenshot Capture

`scripts/capture_ui_screenshots.py` uses local backend/frontend dev servers and headless Firefox through `geckodriver` to refresh the UI proof screenshots under `reports/screenshots/ui_safety_polish/`.

Expected local services:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

Run from repo root:

```bash
python3 scripts/capture_ui_screenshots.py
```

The script deletes old PNG files in `reports/screenshots/ui_safety_polish/` before writing the current set. It is a development/reporting utility only; it does not send real hardware, motion, servo or fire commands.
