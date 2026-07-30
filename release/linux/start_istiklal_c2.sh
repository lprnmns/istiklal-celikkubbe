#!/usr/bin/env bash
set -euo pipefail

# Safety invariant: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false.
# This launcher starts the software only. It never calls motor, fire, GPIO, STEP/DIR/PWM or hardware-enable endpoints.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs/launcher"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/launcher_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

PORT="${ISTIKLAL_PORT:-8000}"
URL="http://127.0.0.1:$PORT"

echo "ISTIKLAL C2 Console portable launcher"
echo "Root: $ROOT_DIR"
echo "Log: $LOG_FILE"
echo "Safety: software startup only; physical commands remain disabled."

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python bulunamadı. Python 3.12+ kurup tekrar çalıştırın."
  exit 1
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 12):
    raise SystemExit("ERROR: Python bulunamadı veya sürüm yetersiz. Python 3.12+ kurup tekrar çalıştırın.")
print(f"Python OK: {sys.version.split()[0]}")
PY

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv bulunamadı. İlk kurulum için uv gereklidir."
  echo "Offline release kullanıyorsanız wheelhouse/önceden hazırlanmış .venv paketi gerekir."
  exit 1
fi

for required in "$ROOT_DIR/backend" "$ROOT_DIR/config" "$ROOT_DIR/models" "$ROOT_DIR/release"; do
  if [ ! -e "$required" ]; then
    echo "ERROR: Release paketi eksik veya bozuk: $required bulunamadı."
    exit 1
  fi
done

if [ ! -f "$ROOT_DIR/backend/pyproject.toml" ] && [ ! -f "$ROOT_DIR/backend/requirements.txt" ]; then
  echo "ERROR: Backend bağımlılık tanımı bulunamadı."
  exit 1
fi

if [ ! -f "$ROOT_DIR/frontend/dist/index.html" ]; then
  echo "ERROR: Frontend static build bulunamadı. Release paketi eksik veya bozuk."
  echo "Runtime'da pnpm/npm build çalıştırılmayacak."
  exit 1
fi

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/exports" "$ROOT_DIR/models/import"
if ! touch "$ROOT_DIR/logs/.launcher_write_test" "$ROOT_DIR/exports/.launcher_write_test" 2>/dev/null; then
  echo "ERROR: logs veya exports klasörü yazılabilir değil."
  exit 1
fi
rm -f "$ROOT_DIR/logs/.launcher_write_test" "$ROOT_DIR/exports/.launcher_write_test"

if compgen -G "/dev/ttyACM*" >/dev/null || compgen -G "/dev/ttyUSB*" >/dev/null; then
  echo "Serial devices detected. Pico görünmüyorsa kullanıcı dialout grubunda olmayabilir."
else
  echo "No /dev/ttyACM* or /dev/ttyUSB* serial device detected. Pico disconnected state is safe."
fi

if compgen -G "/dev/video*" >/dev/null; then
  echo "Camera device(s) detected: $(ls /dev/video* 2>/dev/null | tr '\n' ' ')"
else
  echo "No /dev/video* camera detected. Mock/no-camera fallback remains safe."
fi

python3 - "$PORT" <<'PY'
import socket
import sys
port = int(sys.argv[1])
s = socket.socket()
try:
    s.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(f"ERROR: Port {port} is already in use. Close the other service or set ISTIKLAL_PORT.")
finally:
    s.close()
print(f"Port {port} available")
PY

echo "İlk çalıştırma için backend bağımlılıkları kuruluyor. Bu işlem birkaç dakika sürebilir."
cd "$ROOT_DIR/backend"
if ! uv sync; then
  echo "ERROR: Bağımlılıklar indirilemedi. Offline wheelhouse/release paketi gerekli."
  exit 1
fi

if command -v xdg-open >/dev/null 2>&1; then
  (sleep 2 && xdg-open "$URL" >/dev/null 2>&1 || true) &
else
  echo "Browser otomatik açılamadı. URL: $URL"
fi

echo "Starting backend at $URL"
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
