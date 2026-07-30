from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.services.camera_runtime_service as camera_runtime_module
from app.schemas.camera_runtime import CameraRuntimeProfile


class FakeFrame:
    shape = (720, 1280, 3)

    def copy(self) -> "FakeFrame":
        return self


def test_cockpit_route_renders_without_crashing(client: TestClient) -> None:
    response = client.get("/cockpit")

    assert response.status_code == 200


def test_camera_status_contract_exposes_phase37_diagnostics(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.camera_runtime.profile = CameraRuntimeProfile()
    response = client.get("/api/camera/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["selected_device"] == "mock"
    assert payload["selected_backend"] in {"mock", "fallback"}
    assert payload["input_format"] == "mjpeg" or payload["input_format"] == "auto"
    assert payload["resolution"] == "640x360"
    assert payload["no_physical_command_generated"] is True


def test_camera_source_selection_handles_dev_video2_ffmpeg_fallback(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = client.app.state.runtime
    monkeypatch.setattr(camera_runtime_module, "cv2", object())
    original_exists = Path.exists
    monkeypatch.setattr(Path, "exists", lambda self: str(self) == "/dev/video2" or original_exists(self))
    runtime.camera_runtime.profile = CameraRuntimeProfile(
        source_type="usb",
        device_id="camera_dev_video2",
        device_path="/dev/video2",
        width=1280,
        height=720,
        fps=30,
        pixel_format="MJPG",
        stream_width=1280,
        stream_height=720,
        inference_width=1280,
        inference_height=720,
    )

    def opencv_failed(_path: str):
        return None, ["opencv_persistent_open_failed:/dev/video2"]

    def ffmpeg_ok(_path: str):
        runtime.camera_runtime.last_capture_backend = "ffmpeg"
        runtime.camera_runtime.last_capture_error = None
        return FakeFrame(), ["ffmpeg frame capture used for real camera"]

    monkeypatch.setattr(runtime.camera_runtime, "_read_frame_opencv_persistent", opencv_failed)
    monkeypatch.setattr(runtime.camera_runtime, "_read_frame_ffmpeg", ffmpeg_ok)

    frame, warnings = runtime.camera_runtime.read_frame()
    status = client.get("/api/camera/runtime/status").json()

    assert frame is not None
    assert "ffmpeg frame capture used for real camera" in warnings
    assert status["selected_device"] == "/dev/video2"
    assert status["selected_backend"] == "ffmpeg"
    assert status["input_format"] == "mjpeg"
    assert status["resolution"] == "1280x720"
    assert status["is_real_camera_evidence"] is True
    assert status["last_capture_error"] is None
    assert status["no_physical_command_generated"] is True


def test_digital_twin_missing_telemetry_and_safety_fields_remain_visible(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    person = client.get("/api/person-safety/status").json()

    assert state["telemetry_protocol"]["telemetry_missing"] is True
    assert state["telemetry_protocol"]["pose_source"] in {"tracker_estimate", "fixture"}
    assert state["no_physical_command_generated"] is True
    assert person["no_physical_command_generated"] is True


def test_phase37_no_physical_command_tx_path_added() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "frontend" / "src" / "views" / "CockpitView.vue",
        *sorted((root / "frontend" / "src" / "components" / "cockpit").glob("*.vue")),
        root / "backend" / "app" / "services" / "camera_runtime_service.py",
        root / "backend" / "app" / "schemas" / "camera_runtime.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = [
        "write(b\"SPD",
        "write(b\"LZR",
        "write(b\"STP",
        ".write(b'SPD",
        ".write(b'LZR",
        ".write(b'STP",
        "send_fire_command(",
        "set_servo_position(",
        "gpio_write(",
        "pwm_write(",
        "step_pulse(",
        "serial_tx_enabled: true",
        "physical_command_enabled: true",
    ]
    for item in forbidden:
        assert item not in combined
