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
OUT = ROOT / "reports" / "screenshots" / "phase18_data_lab_foundation"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:8001")
API_BASE = os.environ.get("SCREENSHOT_API_BASE_URL", BASE)
GECKODRIVER = os.environ.get("GECKODRIVER", "/snap/bin/geckodriver")
PORT = int(os.environ.get("GECKODRIVER_PORT", "4444"))


def webdriver_request(method: str, path: str, payload: dict | None = None) -> dict:
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
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_driver() -> None:
    for _ in range(80):
        try:
            webdriver_request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return webdriver_request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []}).get("value")


def navigate(session_id: str, path: str, wait_s: float = 1.2) -> None:
    webdriver_request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{path}"})
    time.sleep(wait_s)


def set_viewport(session_id: str, width: int, height: int) -> None:
    webdriver_request("POST", f"/session/{session_id}/window/rect", {"width": width, "height": height})
    time.sleep(0.3)


def scroll_to_heading(session_id: str, text: str) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('h2, h3, h4')).find((item) =>
          (item.textContent || '').trim().includes(wanted)
        );
        if (el) window.scrollTo(0, Math.max(0, el.getBoundingClientRect().top + window.scrollY - 140));
        """,
    )
    time.sleep(0.5)


def screenshot(session_id: str, name: str) -> None:
    raw = webdriver_request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def render_json_page(session_id: str, title: str, payload: dict) -> None:
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    page = f"""
    <html>
      <head>
        <title>{html.escape(title)}</title>
        <style>
          body {{ margin: 0; background: #0b0d10; color: #dbeafe; font: 14px ui-monospace, SFMono-Regular, Menlo, monospace; }}
          main {{ padding: 28px; }}
          h1 {{ color: #67e8f9; font: 700 24px system-ui, sans-serif; }}
          pre {{ white-space: pre-wrap; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 18px; background: rgba(0,0,0,.34); line-height: 1.55; }}
          .badge {{ display: inline-block; margin-bottom: 12px; padding: 6px 10px; border: 1px solid #f59e0b; color: #fde68a; border-radius: 6px; }}
        </style>
      </head>
      <body><main><div class="badge">ADVISORY ONLY · NO PHYSICAL COMMAND</div><h1>{html.escape(title)}</h1><pre>{html.escape(body)}</pre></main></body>
    </html>
    """
    webdriver_request("POST", f"/session/{session_id}/url", {"url": "data:text/html;charset=utf-8," + urllib.parse.quote(page)})
    time.sleep(0.5)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def prepare_backend_state() -> dict:
    backend_request("POST", "/api/vision/runtime/apply-settings", {"inference_adapter": "opencv_live_circle_surrogate"})
    backend_request("POST", "/api/data-lab/sessions/record-latest")
    data_export = backend_request("POST", "/api/data-lab/export")
    report_export = backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase18 screenshot evidence"})
    interfaces = backend_request("GET", "/api/interfaces/ktr-section")
    logs = backend_request("GET", "/api/data-lab/status")
    return {"data_export": data_export, "report_export": report_export, "interfaces": interfaces, "status": logs}


def main() -> None:
    clear_old_screenshots()
    evidence = prepare_backend_state()
    driver = subprocess.Popen([GECKODRIVER, "--port", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_driver()
        session = webdriver_request(
            "POST",
            "/session",
            {"capabilities": {"alwaysMatch": {"browserName": "firefox", "acceptInsecureCerts": True, "moz:firefoxOptions": {"args": ["-headless"]}}}},
        )
        session_id = session["value"]["sessionId"]
        set_viewport(session_id, 1440, 950)

        navigate(session_id, "/data-lab")
        screenshot(session_id, "01_data_lab_foundation_status.png")
        scroll_to_heading(session_id, "Data Lab Session Evidence")
        screenshot(session_id, "02_data_lab_session_evidence.png")

        render_json_page(session_id, "Data Lab Export Detail", evidence["data_export"])
        screenshot(session_id, "03_data_lab_export_detail.png")

        navigate(session_id, "/reports")
        screenshot(session_id, "04_reports_data_lab_export_files.png")

        navigate(session_id, "/interfaces")
        scroll_to_heading(session_id, "Veri Seti, Oturum Kaydı ve Replay Arayüzü")
        screenshot(session_id, "05_interfaces_data_lab_ktr_section.png")

        navigate(session_id, "/logs")
        execute(session_id, "const input = document.querySelector('input[placeholder=\"Search type or summary\"]'); if (input) { input.value = 'data_lab'; input.dispatchEvent(new Event('input')); }")
        time.sleep(0.6)
        screenshot(session_id, "06_logs_data_lab_events.png")

        render_json_page(session_id, "KTR Data Lab Interface Preview", {"markdown": evidence["interfaces"]["markdown"]})
        screenshot(session_id, "07_ktr_data_lab_preview.png")

        webdriver_request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        driver.wait(timeout=5)


if __name__ == "__main__":
    main()
