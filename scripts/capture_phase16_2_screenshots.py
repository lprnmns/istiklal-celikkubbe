import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase16_2_model_evidence_log_polish"
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
    with urllib.request.urlopen(req, timeout=25) as response:
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


def navigate(session_id: str, path: str, wait_s: float = 1.3) -> None:
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


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def prepare_backend_state() -> None:
    packages = backend_request("GET", "/api/models/packages")
    if not any(item.get("model_id") == "fixture-opencv-test-adapter" for item in packages):
        backend_request("POST", "/api/models/packages/import", {"source_path": FIXTURE})
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/validate")
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/activate", {"slot": "combined"})
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/test", {"source": "mock"})
    backend_request("POST", "/api/models/packages/fixture-opencv-test-adapter/apply-recommended-settings")
    backend_request("POST", "/api/first-run/check")
    backend_request("POST", "/api/self-test/run")
    backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase16.2 model evidence and log polish"})
    backend_request("POST", "/api/interfaces/export")


def main() -> None:
    clear_old_screenshots()
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
        set_viewport(session_id, 1440, 950)

        navigate(session_id, "/models")
        scroll_to_heading(session_id, "Active Model")
        screenshot(session_id, "01_models_active_model_values_visible.png")
        scroll_to_heading(session_id, "Safety Evidence")
        screenshot(session_id, "02_models_safety_evidence_values_visible.png")

        navigate(session_id, "/logs")
        execute(session_id, "const input = document.querySelector('input[placeholder=\"Search type or summary\"]'); if (input) { input.value = 'model.'; input.dispatchEvent(new Event('input')); }")
        time.sleep(0.8)
        screenshot(session_id, "03_logs_model_human_readable_summaries.png")

        navigate(session_id, "/first-run")
        screenshot(session_id, "04_first_run_release_vs_competition_explanation.png")

        navigate(session_id, "/self-test")
        execute(session_id, "const selects = document.querySelectorAll('select'); const category = selects[1]; if (category) { category.value = 'model'; category.dispatchEvent(new Event('change')); }")
        time.sleep(0.5)
        screenshot(session_id, "05_self_test_release_competition_warning_explanation.png")

        navigate(session_id, "/vision")
        scroll_to_heading(session_id, "YOLO Runtime")
        screenshot(session_id, "06_vision_runtime_fixture_adapter_consistency.png")

        navigate(session_id, "/reports")
        scroll_to_heading(session_id, "Export Detail")
        screenshot(session_id, "07_reports_active_model_semantic_export_detail.png")

        navigate(session_id, "/interfaces")
        scroll_to_heading(session_id, "KTR-ready 4.3 Preview")
        screenshot(session_id, "08_ktr_test_adapter_not_competition_text.png")

        request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
