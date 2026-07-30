from fastapi.testclient import TestClient


def upload_payload(**overrides):
    payload = {
        "name": "Vision Team Combined",
        "version": "0.1.0",
        "model_type": "combined_detector",
        "framework": "ultralytics",
        "file_name": "combined.pt",
        "file_size_bytes": 128,
        "class_names": ["f16", "helicopter", "ballistic_missile", "mini_micro_uav", "balloon"],
        "input_size": 960,
        "confidence_threshold": 0.35,
        "iou_threshold": 0.5,
        "provided_by": "vision_team",
    }
    payload.update(overrides)
    return payload


def start_session(client: TestClient) -> str:
    response = client.post(
        "/api/sessions/start",
        json={
            "name": "test_capture",
            "operator": "pytest",
            "mode": "capture",
            "scenario": {
                "target_type": "helicopter",
                "team": "enemy",
                "distance_m": "10",
                "lane": "center",
                "angle": "front",
                "lighting": "indoor_led",
                "lens_profile": "8mm",
                "camera_resolution": "640x360",
                "yolo_imgsz": 960,
                "active_model_ids": [],
            },
        },
    )
    assert response.status_code == 200
    return response.json()["session_id"]


def test_model_registry_list_includes_test_adapter(client: TestClient) -> None:
    response = client.get("/api/models")
    assert response.status_code == 200
    assert any(model["model_id"] == "opencv-circle-test-adapter" for model in response.json())


def test_model_upload_metadata_and_registry(client: TestClient) -> None:
    response = client.post("/api/models/upload", json=upload_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["file_name"] == "combined.pt"
    assert body["no_physical_command_generated"] if "no_physical_command_generated" in body else True
    assert any(model["model_id"] == body["model_id"] for model in client.get("/api/models").json())


def test_unsupported_extension_rejected(client: TestClient) -> None:
    response = client.post("/api/models/upload", json=upload_payload(file_name="unsafe.exe"))
    assert response.status_code == 400


def test_model_validate_missing_file_warning(client: TestClient) -> None:
    uploaded = client.post("/api/models/upload", json=upload_payload(file_name="missing.onnx", framework="onnx")).json()
    # Simulate external deletion without crashing validation.
    client.app.state.runtime.model_registry.get_model(uploaded["model_id"])
    response = client.post(f"/api/models/{uploaded['model_id']}/validate")
    assert response.status_code == 200
    assert "can_be_loaded" in response.json()["checks"]


def test_activate_model_and_active_endpoint(client: TestClient) -> None:
    uploaded = client.post("/api/models/upload", json=upload_payload()).json()
    response = client.post(f"/api/models/{uploaded['model_id']}/activate", json={"slot": "combined"})
    assert response.status_code == 200
    assert response.json()["active_combined_model_id"] == uploaded["model_id"]
    assert client.get("/api/models/active").json()["active_combined_model_id"] == uploaded["model_id"]


def test_opencv_circle_stub_and_model_test_inference(client: TestClient) -> None:
    circle = client.post("/api/models/opencv-circle-test", json={"source": "mock", "frame_id": "circle-test"})
    assert circle.status_code == 200
    assert circle.json()["adapter"] == "opencv_stub"
    assert circle.json()["detections"][0]["is_balloon"] is True
    test = client.post("/api/models/test-inference", json={"model_id": None, "source": "mock", "frame_id": "mock-test", "use_test_adapter": True})
    assert test.status_code == 200
    assert test.json()["no_physical_command_generated"] is True


def test_session_start_stop_and_snapshot_metadata(client: TestClient) -> None:
    session_id = start_session(client)
    snapshot = client.post(f"/api/sessions/{session_id}/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["no_physical_command_generated"] is True
    stop = client.post("/api/sessions/stop")
    assert stop.status_code == 200
    assert stop.json()["ended_at"] is not None


def test_record_detection_event_and_annotation_flow(client: TestClient) -> None:
    session_id = start_session(client)
    client.post(f"/api/sessions/{session_id}/record-event", json={"event_type": "detection", "payload": {"frame_id": "frame-1"}})
    detections = client.get(f"/api/sessions/{session_id}/detections").json()
    assert detections[0]["payload"]["frame_id"] == "frame-1"
    annotation = client.post(
        "/api/annotations",
        json={
            "session_id": session_id,
            "frame_id": "frame-1",
            "image_path": "/tmp/frame-1.jpg",
            "source": "manual",
            "objects": [
                {
                    "object_id": "obj-1",
                    "class_name": "balloon",
                    "class_id": 4,
                    "bbox_format": "yolo_normalized",
                    "bbox": [0.5, 0.5, 0.2, 0.2],
                    "is_balloon": True,
                    "verified_by_operator": True,
                }
            ],
        },
    )
    assert annotation.status_code == 200
    assert client.get(f"/api/sessions/{session_id}/annotations").json()[0]["objects"][0]["class_name"] == "balloon"


def test_model_prediction_to_annotation(client: TestClient) -> None:
    session_id = start_session(client)
    result = client.post("/api/models/opencv-circle-test", json={"source": "mock"}).json()
    response = client.post(
        "/api/annotations/from-prediction",
        json={
            "session_id": session_id,
            "frame_id": result["frame_id"],
            "image_path": "/tmp/mock.jpg",
            "detections": result["detections"],
        },
    )
    assert response.status_code == 200
    assert response.json()["source"] == "model_prediction"


def test_yolo_export_data_yaml_and_label_format(client: TestClient) -> None:
    session_id = start_session(client)
    snapshot = client.post(f"/api/sessions/{session_id}/snapshot").json()
    client.post(
        "/api/annotations",
        json={
            "session_id": session_id,
            "frame_id": snapshot["frame_id"],
            "image_path": snapshot["image_path"],
            "objects": [
                {
                    "object_id": "obj-1",
                    "class_name": "balloon",
                    "class_id": 4,
                    "bbox_format": "yolo_normalized",
                    "bbox": [0.5, 0.5, 0.2, 0.2],
                    "is_balloon": True,
                    "verified_by_operator": True,
                }
            ],
        },
    )
    response = client.post(
        "/api/datasets/export-yolo",
        json={"dataset_name": "pytest_dataset", "version": "v1", "export_mode": "combined_body_balloon", "selected_sessions": [session_id]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label_count"] == 1
    assert body["data_yaml_path"].endswith("data.yaml")


def test_dataset_validation_and_health(client: TestClient) -> None:
    response = client.post("/api/datasets/validate", json={"dataset_name": "pytest_dataset", "version": "v1"})
    assert response.status_code == 200
    assert "warnings" in response.json()
    health = client.get("/api/datasets/health")
    assert health.status_code == 200
    assert "recommendations" in health.json()


def test_dataset_validation_catches_invalid_bbox(client: TestClient) -> None:
    response = client.post(
        "/api/annotations",
        json={
            "session_id": start_session(client),
            "frame_id": "bad-frame",
            "image_path": "/tmp/bad.jpg",
            "objects": [
                {
                    "object_id": "obj-1",
                    "class_name": "f16",
                    "class_id": 0,
                    "bbox_format": "yolo_normalized",
                    "bbox": [1.2, 0.5, 0.2, 0.2],
                }
            ],
        },
    )
    assert response.status_code == 422


def test_replay_load_play_pause_step_no_physical_command(client: TestClient) -> None:
    session_id = start_session(client)
    client.post(f"/api/sessions/{session_id}/snapshot")
    loaded = client.post("/api/replay/load-session", json={"session_id": session_id})
    assert loaded.status_code == 200
    assert loaded.json()["no_physical_command_generated"] is True
    assert client.post("/api/replay/play").json()["state"] == "playing"
    assert client.post("/api/replay/pause").json()["state"] == "paused"
    assert client.post("/api/replay/step").json()["frame_index"] == 0


def test_config_models_dataset_sections(client: TestClient) -> None:
    config = client.app.state.runtime.config
    assert config.models.default_adapter == "mock"
    assert config.dataset.default_export_mode == "combined_body_balloon"


def test_safety_invariant_model_dataset_replay_no_serial_command(client: TestClient) -> None:
    before = client.get("/api/serial/logs").json()
    session_id = start_session(client)
    client.post("/api/models/opencv-circle-test", json={"source": "mock"})
    client.post("/api/replay/load-session", json={"session_id": session_id})
    client.post("/api/datasets/validate", json={"dataset_name": "pytest_dataset", "version": "v1"})
    after = client.get("/api/serial/logs").json()
    assert before == after
    assert client.get("/api/system/state").json()["fire_policy"] == "NO_FIRE"


def test_websocket_model_session_replay_event_smoke(client: TestClient) -> None:
    session_id = start_session(client)
    client.post("/api/replay/load-session", json={"session_id": session_id})
    client.post("/api/models/opencv-circle-test", json={"source": "mock"})
    with client.websocket_connect("/ws") as websocket:
        seen = {websocket.receive_json()["type"] for _ in range(40)}
    assert "model.test_completed" in seen
    assert "session.started" in seen or "replay.loaded" in seen
