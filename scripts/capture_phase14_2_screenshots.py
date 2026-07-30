import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase14_2_final_readiness_polish"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:5173")
API_BASE = os.environ.get("SCREENSHOT_API_BASE_URL", "http://127.0.0.1:8000")
GECKODRIVER = "/snap/bin/geckodriver"
PORT = 4444


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
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_driver() -> None:
    for _ in range(50):
        try:
            request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []}).get("value")


def navigate(session_id: str, path: str, wait_s: float = 1.2) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{path}"})
    time.sleep(wait_s)


def set_viewport(session_id: str, width: int, height: int) -> None:
    request("POST", f"/session/{session_id}/window/rect", {"width": width, "height": height})
    time.sleep(0.3)


def click_button(session_id: str, text: str, wait_s: float = 0.8) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('button')).find((item) =>
          (item.textContent || '').trim().includes(wanted)
        );
        if (!el) throw new Error('Button not found: ' + wanted);
        el.scrollIntoView({{ block: 'center' }});
        el.click();
        """,
    )
    time.sleep(wait_s)


def scroll_to_heading(session_id: str, text: str) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('h3, h2')).find((item) =>
          (item.textContent || '').trim() === wanted
        );
        if (!el) throw new Error('Heading not found: ' + wanted);
        const top = el.getBoundingClientRect().top + window.scrollY - 140;
        window.scrollTo(0, Math.max(0, top));
        """,
    )
    time.sleep(0.4)


def screenshot(session_id: str, name: str) -> None:
    raw = request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def main() -> None:
    clear_old_screenshots()
    backend_request("POST", "/api/first-run/check")
    backend_request("POST", "/api/device-profiles/save", {"profile_id": "default"})
    backend_request("POST", "/api/device-profiles/verify", {"profile_id": "default"})
    backend_request("POST", "/api/interfaces/export")

    driver = subprocess.Popen(
        [GECKODRIVER, "--host", "127.0.0.1", "--port", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_driver()
        session = request(
            "POST",
            "/session",
            {
                "capabilities": {
                    "alwaysMatch": {
                        "browserName": "firefox",
                        "acceptInsecureCerts": True,
                        "moz:firefoxOptions": {"args": ["-headless"]},
                    }
                }
            },
        )
        session_id = session["value"]["sessionId"]
        set_viewport(session_id, 1440, 950)

        navigate(session_id, "/first-run")
        click_button(session_id, "Mark complete")
        screenshot(session_id, "01_first_run_passed_consistent.png")
        click_button(session_id, "Reset")
        screenshot(session_id, "02_first_run_reset_open_consistent.png")

        backend_request("POST", "/api/first-run/check")
        navigate(session_id, "/")
        screenshot(session_id, "03_dashboard_top_blockers.png")
        screenshot(session_id, "04_environment_profile_labels.png")

        navigate(session_id, "/interfaces")
        screenshot(session_id, "05_ktr_table_turkish_polished.png")
        click_button(session_id, "Export interface inventory")
        scroll_to_heading(session_id, "Export")
        screenshot(session_id, "06_interfaces_export_after_polish.png")

        request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
