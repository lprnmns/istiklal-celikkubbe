from fastapi.testclient import TestClient

from app.schemas.camera_runtime import CameraRuntimeProfile
from app.schemas.vision_runtime_settings import VisionRuntimeProfile


def test_device_scan_endpoint(client: TestClient) -> None:
    response = client.get("/api/devices")
    assert response.status_code == 200
    body = response.json()
    assert "devices" in body
    assert body["no_physical_command_generated"] is True


def test_camera_list_endpoint(client: TestClient) -> None:
    response = client.get("/api/devices/cameras")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_fake_camera_probe_not_found(client: TestClient) -> None:
    response = client.post("/api/devices/cameras/camera_missing/probe")
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["no_physical_command_generated"] is True


def test_serial_pico_candidate_classification(client: TestClient) -> None:
    service = client.app.state.runtime.device_manager
    assert service._pico_score("/dev/ttyACM0 Raspberry Pi Pico 2E8A") >= 50
    assert service._pico_score("/dev/ttyS0") < 50


def test_permission_warning_shape(client: TestClient) -> None:
    body = client.get("/api/devices/serial").json()
    for device in body:
        assert "permissions_ok" in device
        assert "warnings" in device


def test_camera_profile_validation() -> None:
    profile = CameraRuntimeProfile(source_type="mock", width=640, height=360, fps=15)
    assert profile.source_type == "mock"


def test_camera_profile_rollback(client: TestClient) -> None:
    bad_profile = {
        "source_type": "usb",
        "device_id": "camera_missing",
        "device_path": "/dev/video-missing",
        "stable_path": None,
        "width": 640,
        "height": 360,
        "fps": 15,
        "pixel_format": "auto",
        "exposure_auto": True,
        "flip_horizontal": False,
        "flip_vertical": False,
        "rotate_deg": 0,
        "lens_profile": "unknown",
        "stream_width": 640,
        "stream_height": 360,
        "inference_width": 640,
        "inference_height": 360,
        "roi": {"enabled": False, "x": 0, "y": 0, "w": 0, "h": 0},
    }
    response = client.post("/api/camera/runtime/apply-profile", json=bad_profile)
    body = response.json()
    assert body["accepted"] is False
    assert body["rollback_performed"] is True
    assert body["no_physical_command_generated"] is True


def test_vision_settings_validation() -> None:
    profile = VisionRuntimeProfile(inference_adapter="opencv_circle_test", conf=0.25, iou=0.45)
    assert profile.inference_adapter == "opencv_circle_test"


def test_invalid_yolo_param_rejected(client: TestClient) -> None:
    body = client.get("/api/vision/runtime/settings").json()
    body["conf"] = 1.5
    response = client.post("/api/vision/runtime/apply-settings", json=body)
    assert response.status_code == 422


def test_model_missing_warning_for_yolo(client: TestClient) -> None:
    body = client.get("/api/vision/runtime/settings").json()
    body["inference_adapter"] = "ultralytics_yolo"
    body["active_body_model_id"] = "missing-model"
    response = client.post("/api/vision/runtime/apply-settings", json=body)
    assert response.status_code == 200
    result = response.json()
    assert result["accepted"] is True
    status = client.get("/api/vision/runtime/status").json()
    assert any("model_missing" in warning for warning in status["warnings"])


def test_opencv_circle_test_adapter_selected(client: TestClient) -> None:
    body = client.get("/api/vision/runtime/status").json()
    assert body["profile"]["inference_adapter"] == "opencv_circle_test"
    assert body["no_physical_command_generated"] is True


def test_self_test_device_manager_steps(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    step_ids = {step["step_id"] for step in body["steps"]}
    assert "device_manager_scan" in step_ids
    assert "camera_runtime_profile" in step_ids
    assert "vision_runtime_settings" in step_ids
    assert "pico_candidate_detection" in step_ids


def test_no_physical_command_generated_invariant(client: TestClient) -> None:
    assert client.get("/api/camera/runtime/status").json()["no_physical_command_generated"] is True
    assert client.get("/api/vision/runtime/status").json()["no_physical_command_generated"] is True
    assert client.get("/api/devices").json()["no_physical_command_generated"] is True
