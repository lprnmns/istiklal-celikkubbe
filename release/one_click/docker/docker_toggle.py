#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from contextlib import contextmanager
from pathlib import Path


HERE = Path(__file__).resolve().parent
COMPOSE = HERE / "compose.yaml"
ROOT = HERE.parents[2]
URL_FILE = ROOT / "ISTIKLAL_DOCKER_URL.txt"
LOCK_FILE = ROOT / ".runtime" / "docker_one_click_operation.lock"


class OperationBusy(RuntimeError):
    pass


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


@contextmanager
def operation_lock():
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"pid": os.getpid(), "created_at": time.time()})
    try:
        descriptor = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            current = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            lock_pid = int(current.get("pid") or 0)
            lock_age = time.time() - float(current.get("created_at") or 0.0)
        except (OSError, ValueError, TypeError):
            lock_pid, lock_age = 0, 9999.0
        if lock_pid and process_exists(lock_pid) and lock_age < 1800:
            raise OperationBusy("ISTIKLAL Docker icin bir acma/kapatma islemi zaten devam ediyor.")
        LOCK_FILE.unlink(missing_ok=True)
        descriptor = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(descriptor, payload.encode("utf-8"))
        os.close(descriptor)
        yield
    finally:
        try:
            current = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = {}
        if int(current.get("pid") or 0) == os.getpid():
            LOCK_FILE.unlink(missing_ok=True)


def notify(title: str, message: str, error: bool = False) -> None:
    if os.name == "nt":
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 if error else 0x40)
        return
    if shutil.which("zenity"):
        subprocess.Popen(["zenity", "--error" if error else "--info", f"--title={title}", f"--text={message}"])
    elif shutil.which("notify-send"):
        subprocess.Popen(["notify-send", "-u", "critical" if error else "normal", title, message])


def docker_command(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), *args],
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )


def running() -> bool:
    result = docker_command("ps", "-q", "--status", "running", "istiklal", capture=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def published_port() -> int:
    result = docker_command("port", "istiklal", "8000", capture=True)
    if result.returncode != 0 or not result.stdout.strip():
        return 0
    value = result.stdout.strip().splitlines()[0].rsplit(":", 1)[-1]
    return int(value) if value.isdigit() else 0


def healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
            return response.status == 200 and bool(json.load(response).get("ok"))
    except Exception:
        return False


def toggle(options: argparse.Namespace) -> int:
    if not shutil.which("docker"):
        message = "Docker Desktop / Docker Engine bulunamadi. Yerel ISTIKLAL_TEK_TIK baslaticisini kullanin."
        print(message)
        if options.gui:
            notify("ISTIKLAL Docker Hata", message, True)
        return 1
    if running():
        result = docker_command("down")
        message = "ISTIKLAL Docker TEST sistemi durduruldu. Kalici log/veri volume'leri korundu."
        print(message)
        if options.gui:
            notify("ISTIKLAL Docker", message, result.returncode != 0)
        return result.returncode

    print("ISTIKLAL Docker TEST image hazirlaniyor ve baslatiliyor...", flush=True)
    result = docker_command("up", "-d", "--build")
    if result.returncode != 0:
        message = "Docker build/baslatma basarisiz. Docker Desktop'in calistigini kontrol edin."
        if options.gui:
            notify("ISTIKLAL Docker Hata", message, True)
        return result.returncode
    deadline = time.monotonic() + 180
    port = 0
    while time.monotonic() < deadline:
        port = published_port()
        if port and healthy(port):
            url = f"http://127.0.0.1:{port}/"
            URL_FILE.write_text(url + "\n", encoding="utf-8")
            webbrowser.open(url)
            message = f"ISTIKLAL Docker TEST hazir.\n\n{url}\n\nFiziksel donanim komutlari kapali."
            print(message)
            if options.gui:
                notify("ISTIKLAL Docker Hazir", message)
            return 0
        time.sleep(2)
    logs = docker_command("logs", "--tail", "30", "istiklal", capture=True)
    message = "Docker servisi 180 saniyede hazir olmadi.\n\n" + (logs.stdout or logs.stderr)[-2000:]
    if options.gui:
        notify("ISTIKLAL Docker Hata", message, True)
    print(message)
    return 1


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--gui", action="store_true")
    options = args.parse_args()
    try:
        with operation_lock():
            return toggle(options)
    except OperationBusy as exc:
        print(str(exc))
        if options.gui:
            notify("ISTIKLAL Docker", str(exc))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
