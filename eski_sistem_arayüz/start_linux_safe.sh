#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/python"

echo "ISTIKLAL legacy tracker Linux safe launcher"
echo "Mode: camera/perception/GUI only"
echo "Safety: serial TX disabled; motor/servo/fire/GPIO/PWM/STEP/DIR disabled"
echo "no_physical_command_generated=true"

export LEGACY_TRACKER_SAFE_DRY_RUN=1
export LEGACY_TRACKER_ENABLE_SERIAL_TX=0
export LEGACY_TRACKER_CAMERA_FALLBACK_URL="${LEGACY_TRACKER_CAMERA_FALLBACK_URL:-http://127.0.0.1:8005/api/camera/stream.mjpg}"

if command -v uv >/dev/null 2>&1; then
  exec uv run python main.py
fi

exec python3 main.py
