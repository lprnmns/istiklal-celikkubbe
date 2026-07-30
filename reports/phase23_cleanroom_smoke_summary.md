# Release Portability Audit

- Run ID: cleanroom_20260715_184806
- Package ID: istiklal_c2_release_20260715_184744
- ZIP path: /home/alperen/teknofest/exports/release/istiklal_c2_release_20260715_184744.zip
- Extract path: /tmp/istiklal_c2_cleanroom_20260715_184806/istiklal_c2_release_20260715_184744
- Launch command: `bash release/linux/start_istiklal_c2.sh`
- Smoke status: passed
- Endpoints passed: 10/10
- Frontend dist present: True
- Backend present: True
- Forbidden dirs present: False
- Secrets/tokens present: False
- Launcher hardcoded repo path: False
- Release demo ready: True
- Competition ready: False
- no_physical_command_generated=true

## Endpoints

- GET /dashboard: HTTP 200
- GET /demo: HTTP 200
- GET /reports: HTTP 200
- GET /interfaces: HTTP 200
- GET /logs: HTTP 200
- GET /data-lab: HTTP 200
- GET /api/demo/readiness: HTTP 200
- GET /api/demo/latest: HTTP 200
- GET /api/release/package/latest: HTTP 200
- GET /api/health: HTTP 200
