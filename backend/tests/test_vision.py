from fastapi.testclient import TestClient

from app.mocks.mock_camera import MockCamera
from app.mocks.mock_vision import MockVisionGenerator
from app.schemas.camera_runtime import CameraRuntimeProfile


def test_vision_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/vision/status")

    assert response.status_code == 200
    body = response.json()
    assert body["vision_mode"] == "mock"
    assert body["advisory_only"] is True
    assert body["running"] is False


def test_camera_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/camera/status")

    assert response.status_code == 200
    body = response.json()
    assert body["camera_mode"] == "mock"
    assert body["stream_enabled"] is True
    assert body["width"] == 640


def test_camera_status_rejects_selected_camera_missing_from_inventory(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.camera_runtime.profile = CameraRuntimeProfile(
        source_type="usb",
        device_id="camera_dev_video404",
        device_path="/dev/video404",
        width=1280,
        height=720,
        fps=30,
        stream_width=1280,
        stream_height=720,
        inference_width=1280,
        inference_height=720,
    )

    response = client.get("/api/camera/status")

    assert response.status_code == 200
    body = response.json()
    assert body["camera_mode"] == "usb"
    assert body["connected"] is False
    assert body["running"] is False
    assert body["last_error"] == "selected_camera_not_in_inventory"


def test_mock_camera_frame_generation() -> None:
    camera = MockCamera(width=640, height=360, fps=15)
    camera.start()

    frame = camera.jpeg_frame()

    assert frame.startswith(b"\xff\xd8")
    assert camera.running is True


def test_mock_vision_detection_generation() -> None:
    event = MockVisionGenerator().next_event(source="mock", width=640, height=360)

    assert event.frame_id == 1
    assert len(event.body_detections) == 1
    assert len(event.balloon_detections) == 1
    assert event.aim_points[0].x == event.balloon_detections[0].center_x


def test_model_path_missing_controlled_warning(client: TestClient) -> None:
    response = client.put(
        "/api/vision/config",
        json={
            "vision_mode": "mock",
            "body_model_path": "models/body/missing.pt",
            "balloon_model_path": "models/balloon/missing.pt",
            "body_conf_threshold": 0.35,
            "balloon_conf_threshold": 0.35,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "body_model_path_not_found" in body["warnings"]
    assert "balloon_model_path_not_found" in body["warnings"]


def test_vision_start_stop_state_transition(client: TestClient) -> None:
    start = client.post("/api/vision/start")
    assert start.status_code == 200
    assert start.json()["running"] is True

    stop = client.post("/api/vision/stop")
    assert stop.status_code == 200
    assert stop.json()["running"] is False


def test_latest_detection_endpoint(client: TestClient) -> None:
    response = client.get("/api/vision/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "mock"
    assert len(body["body_detections"]) == 1
    assert len(body["balloon_detections"]) == 1


def test_camera_sources_and_select(client: TestClient) -> None:
    sources = client.get("/api/camera/sources")
    assert sources.status_code == 200
    assert sources.json()[0]["mode"] == "mock"

    selected = client.post("/api/camera/select", json={"camera_mode": "mock", "camera_source": None})
    assert selected.status_code == 200
    assert selected.json()["camera_mode"] == "mock"


def test_vision_event_does_not_create_fire_or_motor_command(client: TestClient) -> None:
    before_logs = client.get("/api/serial/logs").json()
    response = client.get("/api/vision/latest")
    after_logs = client.get("/api/serial/logs").json()

    assert response.status_code == 200
    assert after_logs == before_logs
    system = client.get("/api/system/state").json()
    assert system["mode"] == "DISARMED"
    assert system["fire_policy"] == "NO_FIRE"
    assert system["dry_run"] is True
