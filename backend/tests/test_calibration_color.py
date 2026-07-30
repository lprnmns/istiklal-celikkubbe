from pathlib import Path

from fastapi.testclient import TestClient

from app.schemas.vision import BalloonDetection, BBox, BodyDetection, VisionEvent


def test_calibration_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/calibration/status")

    assert response.status_code == 200
    assert response.json()["config"]["camera_height_cm"] == 60.0
    assert response.json()["valid"] is False


def test_calibration_config_validation(client: TestClient) -> None:
    config = client.get("/api/calibration/config").json()
    config["camera_height_cm"] = 70.0

    response = client.put("/api/calibration/config", json=config)

    assert response.status_code == 200
    assert response.json()["camera_height_cm"] == 70.0


def test_invalid_camera_height_negative(client: TestClient) -> None:
    config = client.get("/api/calibration/config").json()
    config["camera_height_cm"] = -1.0

    response = client.put("/api/calibration/config", json=config)

    assert response.status_code == 422


def test_fov_estimate_50cm_at_15m_pixel_calculation(client: TestClient) -> None:
    response = client.post(
        "/api/calibration/fov-estimate",
        json={"hfov_deg": 45.0, "distance_m": 15.0, "object_width_m": 0.5, "image_width_px": 640},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["visible_width_m"] == 12.4264
    assert body["object_width_px"] == 25.75
    assert body["warning_level"] == "poor"


def test_fov_thresholds(client: TestClient) -> None:
    poor = client.post("/api/calibration/fov-estimate", json={"hfov_deg": 45, "distance_m": 15, "object_width_m": 0.5, "image_width_px": 640}).json()
    marginal = client.post("/api/calibration/fov-estimate", json={"hfov_deg": 45, "distance_m": 15, "object_width_m": 1.5, "image_width_px": 640}).json()
    good = client.post("/api/calibration/fov-estimate", json={"hfov_deg": 45, "distance_m": 15, "object_width_m": 2.5, "image_width_px": 640}).json()

    assert poor["warning_level"] == "poor"
    assert marginal["warning_level"] == "marginal"
    assert good["warning_level"] == "good"


def test_calibration_point_add_delete(client: TestClient) -> None:
    added = client.post(
        "/api/calibration/points",
        json={"label": "5m", "world_x_m": 0, "world_y_m": 5, "image_x_px": 320, "image_y_px": 180},
    ).json()
    point_id = added["calibration_points"][0]["id"]

    deleted = client.delete(f"/api/calibration/points/{point_id}").json()

    assert deleted["calibration_points"] == []


def test_color_config_endpoint_and_default_balloon_mask(client: TestClient) -> None:
    response = client.get("/api/color/config")

    assert response.status_code == 200
    assert response.json()["balloon_mask_enabled"] is True


def test_invalid_hsv_range_negative(client: TestClient) -> None:
    config = client.get("/api/color/config").json()
    config["enemy_hsv_ranges"][0]["h_min"] = 30
    config["enemy_hsv_ranges"][0]["h_max"] = 20

    response = client.put("/api/color/config", json=config)

    assert response.status_code == 422


def classify(client: TestClient, team: str, balloon_bbox_present: bool = True):
    return client.post(
        "/api/color/classify-sample",
        json={"frame_id": 1, "detection_id": 1, "mock_team": team, "balloon_bbox_present": balloon_bbox_present},
    ).json()


def test_mock_color_classify_enemy(client: TestClient) -> None:
    result = classify(client, "enemy")

    assert result["decision"] == "enemy"
    assert result["confidence"] >= 0.55


def test_mock_color_classify_friend(client: TestClient) -> None:
    result = classify(client, "friend")

    assert result["decision"] == "friend"
    assert result["friend_pixel_ratio"] > result["enemy_pixel_ratio"]


def test_mock_color_classify_unknown(client: TestClient) -> None:
    result = classify(client, "unknown")

    assert result["decision"] == "unknown"


def test_balloon_mask_not_applied_warning(client: TestClient) -> None:
    result = classify(client, "enemy", balloon_bbox_present=False)

    assert "balloon_mask_not_applied" in result["blocking_warnings"]


def test_color_config_change_jsonl_log(client: TestClient, tmp_path: Path) -> None:
    config = client.get("/api/color/config").json()
    config["decision_threshold"] = 0.6
    client.put("/api/color/config", json=config)

    log_files = list((tmp_path / "logs").glob("*.jsonl"))
    assert log_files
    assert any("Color config updated" in path.read_text(encoding="utf-8") for path in log_files)


def test_websocket_color_calibration_event_smoke(client: TestClient) -> None:
    classify(client, "enemy")

    with client.websocket_connect("/ws") as websocket:
        messages = [websocket.receive_json() for _ in range(28)]

    types = {message["type"] for message in messages}
    assert "calibration.status" in types
    assert "color.classification" in types


def test_safety_invariant_color_classification_no_physical_command(client: TestClient) -> None:
    before = client.get("/api/serial/logs").json()
    classify(client, "enemy")
    after = client.get("/api/serial/logs").json()

    assert before == after


def test_decision_reads_color_friend_as_no_fire(client: TestClient) -> None:
    body = BodyDetection(
        id=1,
        class_name="helicopter",
        class_id=1,
        confidence=0.9,
        bbox=BBox(x=10, y=10, w=100, h=80),
        target_team="enemy",
        range_m=8.0,
        stable_frames=5,
    )
    balloon = BalloonDetection(
        id=1,
        confidence=0.9,
        bbox=BBox(x=120, y=120, w=30, h=30),
        center_x=135,
        center_y=135,
    )
    client.app.state.runtime.vision.latest_event = VisionEvent(
        frame_id=1,
        timestamp_ms=1,
        source="test",
        fps=15,
        preprocess_ms=1,
        inference_ms=1,
        postprocess_ms=1,
        total_latency_ms=3,
        body_detections=[body],
        balloon_detections=[balloon],
    )
    classify(client, "friend")

    decision = client.get("/api/decision/state").json()

    assert decision["decision_state"] == "NO_FIRE"
    assert "target_is_friend" in decision["blocking_reasons"]
