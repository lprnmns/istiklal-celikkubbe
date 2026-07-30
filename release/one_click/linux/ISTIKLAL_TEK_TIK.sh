#!/usr/bin/env bash
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
PYTHON="$ROOT/backend/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python3 || true)"
if [[ -z "$PYTHON" ]]; then
  command -v zenity >/dev/null && zenity --error --title='ISTIKLAL Hata' --text='Python 3 bulunamadi. Once kurulum paketini calistirin.'
  exit 1
fi
exec "$PYTHON" "$HERE/../launcher.py" toggle --gui
