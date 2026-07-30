import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase16_4_cold_start_evidence"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:8000")
API_BASE = os.environ.get("SCREENSHOT_API_BASE_URL", "http://127.0.0.1:8000")
GECKODRIVER = os.environ.get("GECKODRIVER", "/snap/bin/geckodriver")
PORT = int(os.environ.get("GECKODRIVER_PORT", "4444"))


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def backend_request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_driver() -> None:
    for _ in range(60):
        try:
            request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []}).get("value")


def screenshot(session_id: str, name: str) -> None:
    raw = request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def prepare_backend_state() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()
    backend_request("POST", "/api/first-run/reset")
    backend_request("GET", "/api/release/cold-start-check")
    backend_request("POST", "/api/first-run/check")
    backend_request("POST", "/api/first-run/mark-complete")
    backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase16.4 cold-start release evidence"})


def open_and_capture(session_id: str, route: str, name: str, script: str | None = None) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{route}"})
    time.sleep(1.8)
    if script:
        execute(session_id, script)
        time.sleep(0.7)
    screenshot(session_id, name)


def main() -> None:
    prepare_backend_state()
    driver = subprocess.Popen([GECKODRIVER, "--host", "127.0.0.1", "--port", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_driver()
        session = request(
            "POST",
            "/session",
            {"capabilities": {"alwaysMatch": {"browserName": "firefox", "acceptInsecureCerts": True, "moz:firefoxOptions": {"args": ["-headless"]}}}},
        )
        session_id = session["value"]["sessionId"]
        request("POST", f"/session/{session_id}/window/rect", {"width": 1440, "height": 980})
        open_and_capture(session_id, "/first-run", "01_first_run_cold_start_evidence.png")
        open_and_capture(session_id, "/", "02_dashboard_release_vs_competition.png")
        open_and_capture(session_id, "/reports", "03_reports_cold_start_summary_detail.png")
        open_and_capture(
            session_id,
            "/logs",
            "04_logs_release_cold_start_checked.png",
            "const input = document.querySelector('input[placeholder=\"Search type or summary\"]'); if (input) { input.value = 'release.cold_start_checked'; input.dispatchEvent(new Event('input')); }",
        )
        open_and_capture(session_id, "/interfaces", "05_interfaces_ktr_cold_start_preview.png")
        request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
