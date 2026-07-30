from pathlib import Path

from app.schemas.vision_runtime_settings import VisionRuntimeProfile
from fastapi.testclient import TestClient


def test_live_circle_surrogate_profile_and_status(client: TestClient) -> None:
    profile = VisionRuntimeProfile(
        inference_adapter="opencv_live_circle_surrogate",
        circle_min_radius=6,
        circle_max_radius=64,
        circle_blur_kernel=5,
        circle_target_color_mode="red",
    )
    response = client.post("/api/vision/runtime/apply-settings", json=profile.model_dump(mode="json"))
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["status"]["effective_adapter"] == "mock_camera_surrogate"
    assert body["status"]["surrogate_source_kind"] == "mock"
    assert body["status"]["frame_origin"] == "mock_frame"
    assert body["status"]["production_yolo_loaded"] is False
    assert body["status"]["advisory_only"] is True
    assert body["no_physical_command_generated"] is True
    assert any("production YOLO" in warning for warning in body["warnings"])


def test_surrogate_latest_event_and_snapshot_no_physical(client: TestClient) -> None:
    client.post("/api/vision/runtime/apply-settings", json=VisionRuntimeProfile(inference_adapter="opencv_live_circle_surrogate").model_dump(mode="json"))
    status = client.post("/api/vision/start")
    assert status.status_code == 200
    latest = client.get("/api/vision/latest")
    assert latest.status_code == 200
    body = latest.json()
    assert body["source"] in {"mock_camera_circle_surrogate", "live_camera_circle_surrogate"}
    assert body["camera_source_kind"] == "mock"
    assert body["frame_origin"] == "mock_frame"
    assert body["detector_kind"] == "opencv_circle_surrogate"
    assert body["detector_fps"] > 0
    assert body["balloon_detections"]
    assert "NOT PRODUCTION YOLO" in body["warnings"]
    snapshot = client.post("/api/camera/runtime/snapshot")
    assert snapshot.status_code == 200
    snap = snapshot.json()
    assert snap["no_physical_command_generated"] is True
    assert Path(snap["path"]).exists()


def test_surrogate_logs_and_reports(client: TestClient) -> None:
    client.post("/api/vision/runtime/apply-settings", json=VisionRuntimeProfile(inference_adapter="opencv_live_circle_surrogate").model_dump(mode="json"))
    client.get("/api/vision/latest")
    logs = client.app.state.runtime.logger.path
    assert logs.exists()
    text = logs.read_text(encoding="utf-8")
    assert "vision.mock_surrogate_detection" in text
    assert "OpenCV mock camera surrogate detection completed" in text
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase17 surrogate test"})
    assert export.status_code == 200
    files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert "live_camera_surrogate_summary.md" in files
    assert "live_camera_surrogate_summary.json" in files
    assert "vision_circle_detection_sample.json" in files
    summary = files["live_camera_surrogate_summary.md"].read_text(encoding="utf-8")
    assert "production YOLO veya yarışma modeli değildir" in summary
    assert "Camera source kind" in summary
    assert "Real camera capture not proven in this run" in summary


def test_self_test_contains_surrogate_steps(client: TestClient) -> None:
    run = client.post("/api/self-test/run")
    assert run.status_code == 200
    step_ids = {step["step_id"] for step in run.json()["steps"]}
    assert "mock_frame_readable" in step_ids
    assert "camera_frame_readable" in step_ids
    assert "real_camera_evidence" in step_ids
    assert "surrogate_detector_available" in step_ids
    assert "surrogate_detector_no_physical" in step_ids
    assert "snapshot_export_available" in step_ids
    assert "fps_latency_measured" in step_ids
    assert run.json()["no_physical_command_generated"] is True


def test_first_run_reset_and_complete_status_single_source(client: TestClient) -> None:
    reset = client.post("/api/first-run/reset")
    assert reset.status_code == 200
    status = client.get("/api/first-run/status").json()
    assert status["completed"] is False
    check = client.post("/api/first-run/check")
    assert check.status_code == 200
    status_after_check = client.get("/api/first-run/status").json()
    assert status_after_check["completed"] is False
    complete = client.post("/api/first-run/mark-complete")
    assert complete.status_code == 200
    assert complete.json()["status"]["completed"] is True
    assert client.get("/api/first-run/status").json()["completed"] is True


def test_release_manifest_current_phase(client: TestClient) -> None:
    response = client.get("/api/release/status")
    assert response.status_code == 200
    path = response.json()["release_manifest_path"]
    assert path
    manifest = Path(path).read_text(encoding="utf-8")
    assert '"phase": "Phase 22"' in manifest
    assert "phase22-" in manifest
