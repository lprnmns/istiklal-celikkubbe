import base64
import html
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase15_release_candidate"
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
    with urllib.request.urlopen(req, timeout=15) as response:
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


def navigate(session_id: str, path: str, wait_s: float = 1.2) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{path}"})
    time.sleep(wait_s)


def set_viewport(session_id: str, width: int, height: int) -> None:
    request("POST", f"/session/{session_id}/window/rect", {"width": width, "height": height})
    time.sleep(0.3)


def click_button(session_id: str, text: str, wait_s: float = 1.0) -> None:
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
        const el = Array.from(document.querySelectorAll('h2, h3')).find((item) =>
          (item.textContent || '').trim().includes(wanted)
        );
        if (!el) throw new Error('Heading not found: ' + wanted);
        window.scrollTo(0, Math.max(0, el.getBoundingClientRect().top + window.scrollY - 140));
        """,
    )
    time.sleep(0.5)


def screenshot(session_id: str, name: str) -> None:
    raw = request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def render_text_page(session_id: str, title: str, body: str) -> None:
    page = f"""
    <html>
      <head>
        <title>{html.escape(title)}</title>
        <style>
          body {{ margin: 0; background: #0b0d10; color: #dbeafe; font: 14px ui-monospace, SFMono-Regular, Menlo, monospace; }}
          main {{ padding: 28px; }}
          h1 {{ color: #67e8f9; font: 700 24px system-ui, sans-serif; }}
          pre {{ white-space: pre-wrap; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 18px; background: rgba(0,0,0,.34); line-height: 1.55; }}
          .badge {{ display: inline-block; margin-bottom: 12px; padding: 6px 10px; border: 1px solid #f87171; color: #fecaca; border-radius: 6px; }}
        </style>
      </head>
      <body><main><div class="badge">NO PHYSICAL COMMAND</div><h1>{html.escape(title)}</h1><pre>{html.escape(body)}</pre></main></body>
    </html>
    """
    request("POST", f"/session/{session_id}/url", {"url": "data:text/html;charset=utf-8," + urllib.parse.quote(page)})
    time.sleep(0.5)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def main() -> None:
    clear_old_screenshots()
    backend_request("POST", "/api/release/check")
    backend_request("POST", "/api/first-run/check")
    backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase15 screenshot evidence"})
    backend_request("POST", "/api/interfaces/export")

    driver = subprocess.Popen([GECKODRIVER, "--host", "127.0.0.1", "--port", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_driver()
        session = request(
            "POST",
            "/session",
            {"capabilities": {"alwaysMatch": {"browserName": "firefox", "acceptInsecureCerts": True, "moz:firefoxOptions": {"args": ["-headless"]}}}},
        )
        session_id = session["value"]["sessionId"]
        set_viewport(session_id, 1440, 950)

        navigate(session_id, "/first-run")
        screenshot(session_id, "01_release_first_run_profile.png")

        preflight = backend_request("GET", "/api/release/preflight")
        render_text_page(session_id, "Release Preflight Status", json.dumps(preflight, indent=2))
        screenshot(session_id, "02_release_preflight_status.png")

        render_text_page(session_id, "Windows Launcher Static Inspection", (ROOT / "release" / "windows" / "start_istiklal_c2.bat").read_text(encoding="utf-8"))
        screenshot(session_id, "03_windows_launcher_preview_or_log.png")

        render_text_page(session_id, "Linux Launcher Static Inspection", (ROOT / "release" / "linux" / "start_istiklal_c2.sh").read_text(encoding="utf-8"))
        screenshot(session_id, "04_linux_launcher_preview_or_log.png")

        navigate(session_id, "/devices")
        screenshot(session_id, "05_devices_release_binding_status.png")

        navigate(session_id, "/vision")
        scroll_to_heading(session_id, "Active Model Panel")
        screenshot(session_id, "06_vision_model_import_readiness.png")

        navigate(session_id, "/")
        scroll_to_heading(session_id, "Release Readiness")
        screenshot(session_id, "07_release_dashboard_status.png")

        navigate(session_id, "/interfaces")
        scroll_to_heading(session_id, "KTR-ready 4.3 Preview")
        screenshot(session_id, "08_ktr_release_interface_section.png")

        navigate(session_id, "/logs")
        execute(session_id, "const input = document.querySelector('input[placeholder=\"Search type or summary\"]'); if (input) { input.value = 'release'; input.dispatchEvent(new Event('input')); }")
        time.sleep(0.5)
        screenshot(session_id, "09_logs_release_check_events.png")

        navigate(session_id, "/reports")
        click_button(session_id, "Generate KTR Summary")
        screenshot(session_id, "10_reports_release_export.png")

        request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
