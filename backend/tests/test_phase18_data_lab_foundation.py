import json
from pathlib import Path

from app.schemas.vision_runtime_settings import VisionRuntimeProfile
from fastapi.testclient import TestClient


def _enable_surrogate(client: TestClient) -> None:
    response = client.post(
        "/api/vision/runtime/apply-settings",
        json=VisionRuntimeProfile(inference_adapter="opencv_live_circle_surrogate").model_dump(mode="json"),
    )
    assert response.status_code == 200


def test_data_lab_status_and_record_latest_detection(client: TestClient) -> None:
    _enable_surrogate(client)
    response = client.post("/api/data-lab/sessions/record-latest")
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["no_physical_command_generated"] is True
    assert body["detection_record"]["advisory_only"] is True
    assert body["detection_record"]["no_physical_command_generated"] is True
    assert body["detection_record"]["source"] in {"mock_camera_circle_surrogate", "live_camera_circle_surrogate"}

    status = client.get("/api/data-lab/status")
    assert status.status_code == 200
    assert status.json()["sessions_count"] >= 1
    assert status.json()["latest_detection"]["no_physical_command_generated"] is True


def test_data_lab_sessions_latest_and_sample_jsonl(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/data-lab/sessions/record-latest")
    sessions = client.get("/api/data-lab/sessions")
    assert sessions.status_code == 200
    assert sessions.json()
    latest = client.get("/api/data-lab/sessions/latest")
    assert latest.status_code == 200
    assert latest.json()["advisory_only"] is True
    sample = client.get("/api/data-lab/detection-events-sample")
    assert sample.status_code == 200
    assert sample.json()
    assert sample.json()[-1]["payload"]["no_physical_command_generated"] is True


def test_data_lab_export_writes_required_evidence_files(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/data-lab/sessions/record-latest")
    response = client.post("/api/data-lab/export")
    assert response.status_code == 200
    body = response.json()
    assert body["no_physical_command_generated"] is True
    assert body["export_id"].startswith("data_lab_export_")
    assert body["created_at"] > 0
    files = {Path(path).name: Path(path) for path in body["files"]}
    assert {
        "data_lab_summary.md",
        "data_lab_sessions.json",
        "detection_events_sample.jsonl",
        "replay_readiness.md",
        "replay_summary.md",
        "replay_latest.json",
        "annotation_candidates.json",
        "annotation_review_summary.md",
        "dataset_health_summary.md",
    } <= set(files)
    assert "No physical command generated: true" in files["data_lab_summary.md"].read_text(encoding="utf-8")
    assert "replay_foundation_ready" in files["replay_readiness.md"].read_text(encoding="utf-8")
    sessions = json.loads(files["data_lab_sessions.json"].read_text(encoding="utf-8"))
    assert sessions["no_physical_command_generated"] is True
    assert "no_physical_command_generated" in files["detection_events_sample.jsonl"].read_text(encoding="utf-8")
    assert "Data Lab replay replays recorded detection metadata only" in files["replay_summary.md"].read_text(encoding="utf-8")
    assert "Dataset ready for training: False" in files["dataset_health_summary.md"].read_text(encoding="utf-8")


def test_ktr_export_contains_data_lab_evidence_files_and_interface_text(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/data-lab/sessions/record-latest")
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase18 data lab test"})
    assert export.status_code == 200
    files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert {
        "data_lab_summary.md",
        "data_lab_sessions.json",
        "detection_events_sample.jsonl",
        "replay_readiness.md",
        "replay_summary.md",
        "replay_latest.json",
        "annotation_candidates.json",
        "annotation_review_summary.md",
        "dataset_health_summary.md",
    } <= set(files)
    assert "Data Lab" in files["data_lab_summary.md"].read_text(encoding="utf-8")
    ktr = files["ktr_4_3_interfaces.md"].read_text(encoding="utf-8")
    assert "Veri Seti, Oturum Kaydı ve Replay Arayüzü" in ktr
    assert "no_physical_command_generated=true" in ktr
    assert "/api/data-lab/replay/run" in ktr


def test_data_lab_log_summaries_are_not_generic_telemetry(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/data-lab/sessions/record-latest")
    client.post("/api/data-lab/export")
    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "data_lab.session_recorded" in text
    assert "data_lab.export_completed" in text
    assert "Data Lab session recorded; source=" in text
    assert "Data Lab evidence export completed; sessions=" in text
    assert "telemetry update" not in text.lower()


def test_data_lab_replay_annotation_and_health_endpoints(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/data-lab/sessions/record-latest")
    replay = client.post("/api/data-lab/replay/run")
    assert replay.status_code == 200
    replay_body = replay.json()
    assert replay_body["replay_status"] in {"completed", "completed_no_detection_events"}
    assert replay_body["advisory_only"] is True
    assert replay_body["no_physical_command_generated"] is True
    assert replay_body["replay_execution_not_physical"] is True

    latest = client.get("/api/data-lab/replay/latest")
    assert latest.status_code == 200
    assert latest.json()["replay_id"] == replay_body["replay_id"]

    candidates = client.get("/api/data-lab/annotations/candidates")
    assert candidates.status_code == 200
    assert candidates.json()
    candidate_id = candidates.json()[0]["candidate_id"]
    review = client.post("/api/data-lab/annotations/review", json={"candidate_id": candidate_id, "status": "accepted"})
    assert review.status_code == 200
    assert review.json()["review_status"] == "accepted"
    assert review.json()["no_physical_command_generated"] is True

    health = client.get("/api/data-lab/dataset-health")
    assert health.status_code == 200
    assert health.json()["dataset_ready_for_training"] is False
    assert health.json()["accepted_annotations"] >= 1
    assert health.json()["no_physical_command_generated"] is True

    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "Data Lab replay completed; session=" in text
    assert "Annotation candidate reviewed; status=accepted; no physical command generated." in text
    assert "Dataset health checked; dataset_ready_for_training=false." in text


def test_data_lab_websocket_event_summaries(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/data-lab/sessions/record-latest")
    client.post("/api/data-lab/export")
    seen: dict[str, str] = {}
    with client.websocket_connect("/ws") as websocket:
        for _ in range(80):
            event = websocket.receive_json()
            if event["type"] == "data_lab.export_completed":
                seen[event["type"]] = event["payload"].get("summary", "")
                break
    client.post("/api/data-lab/sessions/record-latest")
    with client.websocket_connect("/ws") as websocket:
        for _ in range(80):
            event = websocket.receive_json()
            if event["type"] == "data_lab.session_recorded":
                seen[event["type"]] = event["payload"].get("summary", "")
                break
    assert seen["data_lab.session_recorded"].startswith("Data Lab session recorded; source=")
    assert seen["data_lab.export_completed"].startswith("Data Lab evidence export completed; sessions=")


def test_data_lab_safety_invariant(client: TestClient) -> None:
    client.post("/api/data-lab/sessions/record-latest")
    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False
