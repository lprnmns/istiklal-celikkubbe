# ISTIKLAL C2 Offline Portable Notes

The portable ZIP can run without internet after dependencies and frontend assets are prepared.

Recommended preparation before field/demo use:

1. Run `uv sync` in `backend/`.
2. Run `pnpm install` and `pnpm build` in `frontend/`.
3. Confirm `frontend/dist/index.html` exists.
4. Copy the full project folder as the portable package.
5. Start with `start_linux.sh` or `start_windows.bat`.

Offline behavior:

- Node/pnpm is not required at runtime if `frontend/dist` is already present.
- The backend serves the built Vue app from `frontend/dist`.
- API routes remain under `/api/*`.
- SPA routes such as `/devices`, `/vision`, `/self-test`, `/reports` and `/interfaces` open directly.
- Logs are written under `logs/launcher` and runtime JSONL log folders.

Hardware safety:

- Offline mode does not enable hardware commands.
- Physical command flags remain rejected by backend config validation.
- Pico real serial use remains read-only unless a future approved hardware phase changes the policy.
