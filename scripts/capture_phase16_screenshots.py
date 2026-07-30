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
OUT = ROOT / "reports" / "screenshots" / "phase16_model_handoff"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:8000")
API_BASE = os.environ.get("SCREENSHOT_API_BASE_URL", "http://127.0.0.1:8000")
GECKODRIVER = os.environ.get("GECKODRIVER", "/snap/bin/geckodriver")
PORT = int(os.environ.get("GECKODRIVER_PORT", "4444"))
FIXTURE = "backend/tests/fixtures/model_packages/opencv_test_adapter_package"


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
    with urllib.request.urlopen(req, timeout=20) as response:
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


def scroll_to_heading(session_id: str, text: str) -> None:
    execute(
        session_id,
        f"""
        const wanted = {json.dumps(text)};
        const el = Array.from(document.querySelectorAll('h2, h3, h4')).find((item) =>
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
      <body><main><div class="badge">NO PHYSICAL COMMAND GENERATED</div><h1>{html.escape(title)}</h1><pre>{html.escape(body)}</pre></main></body>
    </html>
    """
    request("POST", f"/session/{session_id}/url", {"url": "data:text/html;charset=utf-8," + urllib.parse.quote(page)})
    time.sleep(0.5)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def prepare_backend_state() -> dict:
    packages = backend_request("GET", "/api/models/packages")
    if not any(item.get("model_id") == "fixture-opencv-test-adapter" for item in packages):
        backend_request("POST", "/api/models/packages/import", {"source_path": FIXTURE})
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/validate")
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/activate", {"slot": "combined"})
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/test", {"source": "mock"})
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/benchmark")
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/apply-recommended-settings")
    backend_request("POST", "/api/first-run/check")
    backend_request("POST", "/api/self-test/run")
    export = backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase16 model handoff evidence"})
    backend_request("POST", "/api/interfaces/export")
    return export


def main() -> None:
    clear_old_screenshots()
    export = prepare_backend_state()

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

        navigate(session_id, "/models")
        screenshot(session_id, "01_models_inventory_empty_or_fixture.png")
        scroll_to_heading(session_id, "Import Model Package")
        screenshot(session_id, "02_model_package_import_validation.png")
        scroll_to_heading(session_id, "Active Model")
        screenshot(session_id, "03_active_model_panel_validation.png")
        scroll_to_heading(session_id, "Class Mapping Review")
        screenshot(session_id, "04_class_mapping_review.png")

        navigate(session_id, "/vision")
        scroll_to_heading(session_id, "YOLO Runtime")
        screenshot(session_id, "05_vision_runtime_recommended_settings.png")

        navigate(session_id, "/devices")
        screenshot(session_id, "06_devices_model_binding_status.png")

        navigate(session_id, "/first-run")
        screenshot(session_id, "07_first_run_model_profile_checks.png")

        navigate(session_id, "/self-test")
        execute(session_id, "const select = document.querySelectorAll('select')[1]; if (select) { select.value = 'model'; select.dispatchEvent(new Event('change')); }")
        time.sleep(0.5)
        screenshot(session_id, "08_self_test_model_checks.png")

        navigate(session_id, "/interfaces")
        scroll_to_heading(session_id, "KTR-ready 4.3 Preview")
        screenshot(session_id, "09_ktr_model_interface_section.png")

        render_json_page(session_id, "Reports Model Export Detail", export)
        screenshot(session_id, "10_reports_model_export_detail.png")

        navigate(session_id, "/logs")
        execute(session_id, "const input = document.querySelector('input[placeholder=\"Search type or summary\"]'); if (input) { input.value = 'model.'; input.dispatchEvent(new Event('input')); }")
        time.sleep(0.5)
        screenshot(session_id, "11_logs_model_events.png")

        request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
