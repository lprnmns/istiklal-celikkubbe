#!/usr/bin/env python3
"""Cross-platform one-click launcher for the ISTIKLAL application.

The launcher starts one Uvicorn process. FastAPI serves both the API and the
pre-built frontend, so the operator receives one URL and one process to manage.
It never selects LIVE_TEST, moves the turret, arms the trigger, or sends FIRE.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / ".runtime"
STATE_PATH = RUNTIME_DIR / "one_click_runtime.json"
LOCK_PATH = RUNTIME_DIR / "one_click_operation.lock"
URL_PATH = ROOT / "ISTIKLAL_URL.txt"
LOG_DIR = ROOT / "logs" / "one_click"
DEFAULT_PORT_START = 8000
DEFAULT_PORT_END = 8099


class LaunchError(RuntimeError):
    pass


class OperationBusy(RuntimeError):
    pass


def emit(message: str) -> None:
    print(message, flush=True)


def health(port: int, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return response.status == 200 and bool(payload.get("ok"))
    except (OSError, ValueError, urllib.error.URLError):
        return False


def load_state() -> dict:
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(payload: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(STATE_PATH)


def process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and f'"{pid}"' in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def process_create_time(pid: int) -> float:
    try:
        import psutil

        return float(psutil.Process(pid).create_time())
    except Exception:
        return 0.0


def process_belongs_to_launcher(state: dict) -> bool:
    """Reject PID reuse and avoid ever stopping an unrelated process."""
    pid = int(state.get("pid") or 0)
    if not process_exists(pid):
        return False
    expected_create_time = float(state.get("process_create_time") or 0.0)
    actual_create_time = process_create_time(pid)
    if expected_create_time and actual_create_time:
        return abs(expected_create_time - actual_create_time) < 1.0
    # Compatibility for state written by launcher version 1.
    try:
        import psutil

        process = psutil.Process(pid)
        command = " ".join(process.cmdline()).lower()
        cwd = Path(process.cwd()).resolve()
        return "uvicorn" in command and "app.main:app" in command and cwd == (ROOT / "backend").resolve()
    except Exception:
        return False


def discover_existing_server() -> dict:
    """Adopt a healthy project Uvicorn started by an older field script.

    This makes the single toggle authoritative after upgrades: an already
    running legacy ISTIKLAL server is recognized instead of opening a second
    port. Only a process whose command and working directory match this project
    is eligible.
    """
    try:
        import psutil

        connections = psutil.net_connections(kind="inet")
    except Exception:
        return {}
    backend = (ROOT / "backend").resolve()
    for connection in connections:
        if connection.status != "LISTEN" or not connection.pid or not connection.laddr:
            continue
        port = int(connection.laddr.port)
        if not DEFAULT_PORT_START <= port <= DEFAULT_PORT_END or not health(port):
            continue
        try:
            process = psutil.Process(connection.pid)
            command = " ".join(process.cmdline()).lower()
            cwd = Path(process.cwd()).resolve()
        except Exception:
            continue
        if "uvicorn" not in command or "app.main:app" not in command or cwd != backend:
            continue
        url = f"http://127.0.0.1:{port}/"
        state = {
            "pid": process.pid,
            "process_create_time": float(process.create_time()),
            "port": port,
            "url": url,
            "addresses": local_addresses(port),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "launcher_version": 2,
            "adopted_existing_server": True,
        }
        save_state(state)
        return state
    return {}


@contextmanager
def operation_lock():
    """Prevent a rapid double-click from starting two server processes."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"pid": os.getpid(), "created_at": time.time()})
    try:
        descriptor = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            existing = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
            lock_pid = int(existing.get("pid") or 0)
            lock_age = time.time() - float(existing.get("created_at") or 0.0)
        except (OSError, ValueError, TypeError):
            lock_pid, lock_age = 0, 9999.0
        if lock_pid and process_exists(lock_pid) and lock_age < 300:
            raise OperationBusy("ISTIKLAL icin bir baslatma veya durdurma islemi zaten devam ediyor.")
        LOCK_PATH.unlink(missing_ok=True)
        try:
            descriptor = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise OperationBusy("ISTIKLAL islemi zaten devam ediyor.") from exc
    try:
        os.write(descriptor, payload.encode("utf-8"))
        os.close(descriptor)
        yield
    finally:
        try:
            current = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = {}
        if int(current.get("pid") or 0) == os.getpid():
            LOCK_PATH.unlink(missing_ok=True)


def port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def choose_port(preferred: int | None = None) -> int:
    candidates: list[int] = []
    if preferred:
        candidates.append(preferred)
    env_port = os.getenv("ISTIKLAL_PORT")
    if env_port and env_port.isdigit():
        candidates.append(int(env_port))
    candidates.extend(range(DEFAULT_PORT_START, DEFAULT_PORT_END + 1))
    seen: set[int] = set()
    for port in candidates:
        if port in seen or not 1 <= port <= 65535:
            continue
        seen.add(port)
        if port_available(port):
            return port
    raise LaunchError(f"{DEFAULT_PORT_START}-{DEFAULT_PORT_END} araliginda bos port bulunamadi.")


def find_python() -> Path:
    candidates = [
        ROOT / "backend" / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"),
        ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise LaunchError(
        "Backend Python ortami bulunamadi. Once tek tik kurulum paketini calistirin "
        "veya backend/.venv klasorunu release paketine ekleyin."
    )


def validate_release() -> None:
    required = [
        ROOT / "backend" / "app" / "main.py",
        ROOT / "config" / "config.yaml",
        ROOT / "frontend" / "dist" / "index.html",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise LaunchError("Release eksik: " + ", ".join(missing))


def local_addresses(port: int) -> list[str]:
    values = [f"http://127.0.0.1:{port}/"]
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = item[4][0]
            if address and not address.startswith("127."):
                values.append(f"http://{address}:{port}/")
    except OSError:
        pass
    # Tailscale CLI is optional. It gives the most useful remote URL when present.
    tailscale = shutil.which("tailscale")
    if tailscale:
        result = subprocess.run([tailscale, "ip", "-4"], capture_output=True, text=True, check=False, timeout=4)
        address = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        if address:
            values.append(f"http://{address}:{port}/")
    return list(dict.fromkeys(values))


def notify(title: str, message: str, error: bool = False) -> None:
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 if error else 0x40)
            return
        except Exception:
            return
    zenity = shutil.which("zenity")
    if zenity:
        subprocess.Popen([zenity, "--error" if error else "--info", f"--title={title}", f"--text={message}"])
        return
    notifier = shutil.which("notify-send")
    if notifier:
        subprocess.Popen([notifier, "-u", "critical" if error else "normal", title, message])


def start(args: argparse.Namespace) -> int:
    validate_release()
    current = load_state()
    if not process_belongs_to_launcher(current):
        current = discover_existing_server()
    current_port = int(current.get("port") or 0)
    current_pid = int(current.get("pid") or 0)
    if current_port and process_belongs_to_launcher(current) and health(current_port):
        url = f"http://127.0.0.1:{current_port}/"
        emit(f"ISTIKLAL zaten calisiyor: {url}")
        URL_PATH.write_text(url + "\n", encoding="utf-8")
        if not args.no_browser:
            webbrowser.open(url)
        if args.gui:
            notify("ISTIKLAL Hazir", f"Sistem zaten calisiyor.\n\n{url}")
        return 0

    # A previous launcher-owned process may still exist but be unhealthy. Clear
    # only that verified process before creating a replacement.
    if current_pid and process_belongs_to_launcher(current):
        _terminate(current_pid)
    STATE_PATH.unlink(missing_ok=True)

    python = find_python()
    port = choose_port(args.port)
    url = f"http://127.0.0.1:{port}/"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stdout_path = LOG_DIR / f"server_{stamp}.out.log"
    stderr_path = LOG_DIR / f"server_{stamp}.err.log"
    command = [
        str(python),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["ISTIKLAL_ONE_CLICK"] = "1"
    creationflags = 0
    popen_kwargs: dict = {}
    if os.name == "nt":
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        popen_kwargs["start_new_session"] = True

    emit(f"ISTIKLAL baslatiliyor: {url}")
    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        process = subprocess.Popen(
            command,
            cwd=ROOT / "backend",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
            **popen_kwargs,
        )

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        if health(port):
            addresses = local_addresses(port)
            state = {
                "pid": process.pid,
                "process_create_time": process_create_time(process.pid),
                "port": port,
                "url": url,
                "addresses": addresses,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "stdout_log": str(stdout_path),
                "stderr_log": str(stderr_path),
                "launcher_version": 2,
            }
            save_state(state)
            URL_PATH.write_text("\n".join(addresses) + "\n", encoding="utf-8")
            emit("ISTIKLAL hazir.")
            for address in addresses:
                emit(f"  {address}")
            if not args.no_browser:
                webbrowser.open(url)
            if args.gui:
                notify("ISTIKLAL Hazir", "Sistem baslatildi.\n\n" + "\n".join(addresses))
            return 0
        time.sleep(0.5)

    detail = "\n".join(_tail(stderr_path, 20)) or "Sunucu logunda ayrinti yok."
    exited = process.poll() is not None
    if process.poll() is None:
        _terminate(process.pid)
    if exited:
        raise LaunchError(f"Sunucu baslatma sirasinda kapandi.\n\n{detail}")
    raise LaunchError(f"Sunucu {args.timeout:.0f} saniyede hazir olmadi.\n\n{detail}")


def _tail(path: Path, count: int) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]
    except OSError:
        return []


def _terminate(pid: int) -> None:
    if not process_exists(pid):
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and process_exists(pid):
        time.sleep(0.2)
    if process_exists(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass


def stop(args: argparse.Namespace) -> int:
    state = load_state()
    recorded_pid = int(state.get("pid") or 0)
    if recorded_pid and process_exists(recorded_pid) and not process_belongs_to_launcher(state):
        STATE_PATH.unlink(missing_ok=True)
        raise LaunchError(
            "Kayitli PID artik ISTIKLAL sunucusuna ait degil. Guvenlik icin baska bir surec durdurulmadi."
        )
    if not process_belongs_to_launcher(state):
        state = discover_existing_server()
    pid = int(state.get("pid") or 0)
    port = int(state.get("port") or 0)
    if not pid or not process_exists(pid):
        STATE_PATH.unlink(missing_ok=True)
        emit("ISTIKLAL zaten kapali.")
        if args.gui:
            notify("ISTIKLAL", "Sistem zaten kapali.")
        return 0
    if not process_belongs_to_launcher(state):
        STATE_PATH.unlink(missing_ok=True)
        raise LaunchError(
            "Kayitli PID artik ISTIKLAL sunucusuna ait degil. Guvenlik icin baska bir surec durdurulmadi."
        )
    _terminate(pid)
    STATE_PATH.unlink(missing_ok=True)
    emit(f"ISTIKLAL durduruldu (PID {pid}, port {port}).")
    if args.gui:
        notify("ISTIKLAL", "Sistem guvenli bicimde durduruldu.")
    return 0


def status(args: argparse.Namespace) -> int:
    state = load_state()
    if not process_belongs_to_launcher(state):
        state = discover_existing_server()
    pid = int(state.get("pid") or 0)
    port = int(state.get("port") or 0)
    running = bool(pid and process_belongs_to_launcher(state) and port and health(port))
    if running:
        message = "ISTIKLAL CALISIYOR\n" + "\n".join(state.get("addresses") or [state.get("url")])
        emit(message)
    else:
        message = "ISTIKLAL KAPALI veya SAGLIKSIZ"
        emit(message)
    if args.gui:
        notify("ISTIKLAL Durumu", message, error=not running)
    return 0 if running else 1


def toggle(args: argparse.Namespace) -> int:
    state = load_state()
    if not process_belongs_to_launcher(state):
        state = discover_existing_server()
    pid = int(state.get("pid") or 0)
    port = int(state.get("port") or 0)
    if pid and port and process_belongs_to_launcher(state) and health(port):
        return stop(args)
    return start(args)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    subparsers = result.add_subparsers(dest="command", required=True)
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--port", type=int)
    start_parser.add_argument("--timeout", type=float, default=75)
    start_parser.add_argument("--no-browser", action="store_true")
    start_parser.add_argument("--gui", action="store_true")
    start_parser.set_defaults(func=start)
    toggle_parser = subparsers.add_parser("toggle")
    toggle_parser.add_argument("--port", type=int)
    toggle_parser.add_argument("--timeout", type=float, default=75)
    toggle_parser.add_argument("--no-browser", action="store_true")
    toggle_parser.add_argument("--gui", action="store_true")
    toggle_parser.set_defaults(func=toggle)
    for name, function in (("stop", stop), ("status", status)):
        item = subparsers.add_parser(name)
        item.add_argument("--gui", action="store_true")
        item.set_defaults(func=function)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "status":
            return int(args.func(args))
        with operation_lock():
            return int(args.func(args))
    except OperationBusy as exc:
        emit(str(exc))
        if getattr(args, "gui", False):
            notify("ISTIKLAL", str(exc))
        return 0
    except Exception as exc:
        emit(f"HATA: {exc}")
        if getattr(args, "gui", False):
            notify("ISTIKLAL Baslatma Hatasi", str(exc), error=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
