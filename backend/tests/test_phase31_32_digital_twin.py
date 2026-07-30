from pathlib import Path

from fastapi.testclient import TestClient


def test_digital_twin_state_is_read_only(client: TestClient) -> None:
    response = client.get("/api/digital-twin/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["schema_version"].startswith("phase35")
    assert payload["no_physical_command_generated"] is True
    assert payload["safety"]["no_physical_command_generated"] is True
    assert payload["safety"]["digital_twin_read_only"] is True
    assert payload["safety"]["digital_twin_command_authority"] is False
    assert payload["safety"]["physical_command_enabled"] is False
    assert "serial_tx" in payload["safety"]["forbidden_actions"]
    assert payload["target"]["detected"] is True
    assert payload["device_pose"]["pose_source"] in {"telemetry", "gateway_open_loop_estimate", "tracker_estimate", "fixture"}
    assert "runtime" in payload
    assert "queue_length" in payload["runtime"]
    assert "pico_connection_state" in payload["runtime"]
    assert "total_pipeline_ms" in payload["runtime"]["latency"]


def test_digital_twin_assets_include_supplied_competition_target_models(client: TestClient) -> None:
    response = client.get("/api/digital-twin/assets")
    assert response.status_code == 200
    payload = response.json()

    assert payload["no_physical_command_generated"] is True
    assert payload["digital_twin_read_only"] is True
    classes = {asset["class_id"]: asset for asset in payload["target_assets"]}
    assert classes["ballistic_missile"]["source_file"] == "object_18.model"
    assert classes["ballistic_missile"]["model_path"] == "/assets/targets/ballistic_missile.glb"
    assert classes["ballistic_missile"]["status"] == "available"
    assert classes["helicopter"]["source_size_bytes"] == 50215966
    assert classes["f16"]["source_size_bytes"] == 57120249
    assert classes["mini_micro_uav"]["source_size_bytes"] == 58943183
    assert classes["unknown_target"]["status"] in {"planned", "available"}


def test_digital_twin_replay_fixture_export_is_evidence_only(client: TestClient) -> None:
    response = client.post("/api/digital-twin/replay/generate")
    assert response.status_code == 200
    payload = response.json()

    assert payload["accepted"] is True
    assert payload["event_count"] >= 3
    assert payload["digital_twin_read_only"] is True
    assert payload["no_physical_command_generated"] is True


def test_digital_twin_replay_latest_is_labelled_non_live(client: TestClient) -> None:
    response = client.get("/api/digital-twin/replay/latest")
    assert response.status_code == 200
    payload = response.json()

    assert payload["mode"] == "replay"
    assert payload["source"] == "fixture_deterministic_mock"
    assert payload["no_physical_command_generated"] is True
    assert payload["events"][0]["device_pose"]["pose_source"] in {"fixture", "replay_fixture"}


def test_digital_twin_frontend_does_not_call_physical_command_endpoints() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "frontend" / "src" / "api" / "digitalTwin.ts",
        root / "frontend" / "src" / "components" / "digital-twin" / "DigitalTwinPanel.vue",
        root / "frontend" / "src" / "stores" / "digitalTwinStore.ts",
    ]
    forbidden = [
        "/api/motion/jog",
        "/api/motion/go-to",
        "/api/motion/home",
        "/api/decision/fire",
        "/api/serial/send-json",
        "/api/hardware",
        "fire_request",
        "set_servo",
        "pwm_write",
        "step_pulse",
    ]

    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for item in forbidden:
        assert item not in combined
