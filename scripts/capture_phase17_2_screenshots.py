import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase17_2_first_run_status_consistency"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:8000")
API_BASE = os.environ.get("SCREENSHOT_API_BASE_URL", BASE)
GECKODRIVER = os.environ.get("GECKODRIVER", "/snap/bin/geckodriver")
PORT = int(os.environ.get("GECKODRIVER_PORT", "4444"))


def driver_request(method: str, path: str, payload: dict | None = None) -> dict:
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
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_driver() -> None:
    for _ in range(60):
        try:
            driver_request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return driver_request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []}).get("value")


def screenshot(session_id: str, name: str) -> None:
    raw = driver_request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def open_and_capture(session_id: str, route: str, name: str, script: str | None = None) -> None:
    driver_request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{route}"})
    time.sleep(2.0)
    if script:
        execute(session_id, script)
        time.sleep(0.8)
    screenshot(session_id, name)


def main() -> None:
    clear_old_screenshots()
    backend_request("POST", "/api/first-run/check")
    backend_request("POST", "/api/first-run/mark-complete")
    backend_request("POST", "/api/first-run/reset")

    driver = subprocess.Popen([GECKODRIVER, "--host", "127.0.0.1", "--port", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_driver()
        session = driver_request(
            "POST",
            "/session",
            {"capabilities": {"alwaysMatch": {"browserName": "firefox", "acceptInsecureCerts": True, "moz:firefoxOptions": {"args": ["-headless"]}}}},
        )
        session_id = session["value"]["sessionId"]
        driver_request("POST", f"/session/{session_id}/window/rect", {"width": 1440, "height": 980})

        open_and_capture(session_id, "/first-run", "01_first_run_reset_open_not_evaluated.png")
        open_and_capture(session_id, "/", "02_dashboard_open_not_evaluated_no_stale_pass.png")

        backend_request("POST", "/api/first-run/check")
        open_and_capture(session_id, "/first-run", "03_first_run_acceptance_passed.png")
        open_and_capture(session_id, "/", "04_dashboard_passed_after_acceptance.png")
        backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase17.2 first-run current vs previous evidence"})
        open_and_capture(session_id, "/reports", "05_reports_current_vs_previous_evidence.png")
        open_and_capture(session_id, "/", "06_topbar_profile_eval_consistent.png")
        driver_request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
