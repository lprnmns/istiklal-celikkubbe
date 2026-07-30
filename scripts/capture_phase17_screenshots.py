import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase17_live_camera_circle_surrogate"
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
    return driver_request(
        "POST",
        f"/session/{session_id}/execute/sync",
        {"script": script, "args": []},
    ).get("value")


def screenshot(session_id: str, name: str) -> None:
    raw = driver_request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    print(path)


def clear_old_screenshots() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*.png"):
        path.unlink()


def surrogate_profile() -> dict:
    return {
        "inference_adapter": "opencv_live_circle_surrogate",
        "active_body_model_id": None,
        "active_balloon_model_id": None,
        "device": "cpu",
        "imgsz": 640,
        "conf": 0.25,
        "iou": 0.45,
        "max_det": 20,
        "classes": None,
        "agnostic_nms": False,
        "half": False,
        "vid_stride": 1,
        "stream_buffer": False,
        "frame_skip": 0,
        "augment": False,
        "retina_masks": False,
        "tracker_enabled": False,
        "tracker_type": "none",
        "body_conf_threshold": 0.25,
        "balloon_conf_threshold": 0.25,
        "min_box_area_px": 20,
        "max_box_area_px": 200000,
        "target_class_map": {},
        "friend_enemy_color_mode": "disabled",
        "latency_budget_ms": 100,
        "target_fps": 15,
        "warmup_on_load": False,
        "benchmark_on_apply": False,
        "circle_min_radius": 8,
        "circle_max_radius": 90,
        "circle_blur_kernel": 5,
        "circle_threshold": 80,
        "circle_edge_param": 80,
        "circle_min_area": 80,
        "circle_circularity": 0.55,
        "circle_target_color_mode": "any",
        "circle_roi_enabled": False,
        "circle_smoothing": False,
    }


def prepare_backend_state() -> None:
    clear_old_screenshots()
    backend_request("POST", "/api/vision/runtime/apply-settings", surrogate_profile())
    backend_request("POST", "/api/vision/start")
    backend_request("GET", "/api/vision/latest")
    backend_request("POST", "/api/camera/runtime/snapshot")
    backend_request("POST", "/api/self-test/run", {"profile": "release_candidate_ready"})
    backend_request("POST", "/api/reports/generate-ktr-summary", {"notes": "phase17 live camera circle surrogate evidence"})


def open_and_capture(session_id: str, route: str, name: str, script: str | None = None) -> None:
    driver_request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{route}"})
    time.sleep(2.0)
    if script:
        execute(session_id, script)
        time.sleep(0.8)
    screenshot(session_id, name)


def main() -> None:
    prepare_backend_state()
    driver = subprocess.Popen(
        [GECKODRIVER, "--host", "127.0.0.1", "--port", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_driver()
        session = driver_request(
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
        driver_request("POST", f"/session/{session_id}/window/rect", {"width": 1440, "height": 980})
        open_and_capture(session_id, "/vision", "01_vision_live_circle_surrogate_settings.png")
        open_and_capture(
            session_id,
            "/vision",
            "02_vision_overlay_circle_detection_or_no_detection.png",
            "const text=[...document.querySelectorAll('*')].find(e=>e.textContent && e.textContent.includes('Detection Overlay')); if(text) text.scrollIntoView({block:'center'});",
        )
        open_and_capture(session_id, "/", "03_dashboard_surrogate_target_summary.png")
        open_and_capture(
            session_id,
            "/self-test",
            "04_self_test_surrogate_checks.png",
            "const input=document.querySelector('input[placeholder=\"Filter steps\"]'); if(input){input.value='surrogate'; input.dispatchEvent(new Event('input'));}",
        )
        open_and_capture(session_id, "/reports", "05_reports_surrogate_export.png")
        open_and_capture(
            session_id,
            "/logs",
            "06_logs_surrogate_events.png",
            "const input=document.querySelector('input[placeholder=\"Search type or summary\"]'); if(input){input.value='vision.surrogate'; input.dispatchEvent(new Event('input'));}",
        )
        open_and_capture(
            session_id,
            "/interfaces",
            "07_interfaces_ktr_surrogate_preview.png",
            "const input=document.querySelector('input[placeholder=\"Search interfaces\"]'); if(input){input.value='surrogate'; input.dispatchEvent(new Event('input'));}",
        )
        driver_request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=3)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
