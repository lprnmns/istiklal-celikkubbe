#!/usr/bin/env bash
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
LAUNCHER="$HERE/../launcher.py"
PYTHON="$ROOT/backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3 || true)"
fi
if [[ -z "$PYTHON" ]]; then
  command -v zenity >/dev/null && zenity --error --title='ISTIKLAL Hata' --text='Python 3 bulunamadi. Once kurulum paketini calistirin.'
  exit 1
fi
exec "$PYTHON" "$LAUNCHER" start --gui
