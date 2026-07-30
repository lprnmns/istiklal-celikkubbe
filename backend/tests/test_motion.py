from pathlib import Path

from fastapi.testclient import TestClient

from app.schemas.motion import MotionStateValue


def test_motion_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/motion/status")

    assert response.status_code == 200
    assert response.json()["motion_state"] == "IDLE"
    assert response.json()["dry_run"] is True


def test_motion_settings_validation_positive(client: TestClient) -> None:
    settings = client.get("/api/motion/settings").json()
    settings["jog_step_deg"] = 2.0

    response = client.put("/api/motion/settings", json=settings)

    assert response.status_code == 200
    assert response.json()["jog_step_deg"] == 2.0


def test_invalid_pan_limit_negative(client: TestClient) -> None:
    settings = client.get("/api/motion/settings").json()
    settings["pan_min_deg"] = 10.0
    settings["pan_max_deg"] = 5.0

    response = client.put("/api/motion/settings", json=settings)

    assert response.status_code == 422


def test_invalid_speed_negative(client: TestClient) -> None:
    settings = client.get("/api/motion/settings").json()
    settings["pan_max_speed_deg_s"] = -1.0

    response = client.put("/api/motion/settings", json=settings)

    assert response.status_code == 422


def test_jog_dry_run_accepted(client: TestClient) -> None:
    response = client.post("/api/motion/jog", json={"axis": "pan", "direction": "positive", "step_deg": 1.5})

    body = response.json()
    assert response.status_code == 200
    assert body["accepted"] is True
    assert body["dry_run"] is True
    assert body["no_physical_command_generated"] is True
    assert body["state"]["pan_position_deg"] == 1.5


def test_jog_out_of_soft_limit_rejected(client: TestClient) -> None:
    response = client.post("/api/motion/jog", json={"axis": "pan", "direction": "positive", "step_deg": 99.0})

    body = response.json()
    assert body["accepted"] is False
    assert "pan_soft_limit" in body["blocking_reasons"]


def test_go_to_valid_dry_run_accepted(client: TestClient) -> None:
    response = client.post("/api/motion/go-to", json={"pan_target_deg": 10.0, "tilt_target_deg": 5.0})

    body = response.json()
    assert body["accepted"] is True
    assert body["generated_steps"] == {"pan": 100, "tilt": 50}


def test_go_to_out_of_range_rejected(client: TestClient) -> None:
    response = client.post("/api/motion/go-to", json={"pan_target_deg": 70.0, "tilt_target_deg": 0.0})

    body = response.json()
    assert body["accepted"] is False
    assert "pan_soft_limit" in body["blocking_reasons"]


def test_estop_active_motion_rejected(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.motion.state = runtime.motion.state.model_copy(update={"estop_state": True})

    response = client.post("/api/motion/jog", json={"axis": "tilt", "direction": "positive"})

    assert response.json()["accepted"] is False
    assert "estop_active" in response.json()["blocking_reasons"]


def test_limit_switch_active_corresponding_direction_rejected(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.motion.state = runtime.motion.state.model_copy(update={"pan_limit_left": True})

    response = client.post("/api/motion/jog", json={"axis": "pan", "direction": "negative"})

    assert response.json()["accepted"] is False
    assert "pan_left_limit_active" in response.json()["blocking_reasons"]


def test_fault_state_unsafe_command_rejected(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.motion.set_fault("test fault")

    response = client.post("/api/motion/go-to", json={"pan_target_deg": 0.0, "tilt_target_deg": 0.0})

    assert response.json()["accepted"] is False
    assert "motion_fault" in response.json()["blocking_reasons"]


def test_stop_always_accepted(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.motion.set_fault("test fault")

    response = client.post("/api/motion/stop")

    assert response.json()["accepted"] is True
    assert response.json()["state"]["motion_state"] == "STOPPED"


def test_hardware_disabled_no_physical_command_generated(client: TestClient) -> None:
    response = client.post("/api/motion/go-to", json={"pan_target_deg": 0.0, "tilt_target_deg": 0.0})

    body = response.json()
    assert body["accepted"] is True
    assert body["no_physical_command_generated"] is True


def test_motion_command_jsonl_log(client: TestClient, tmp_path: Path) -> None:
    client.post("/api/motion/jog", json={"axis": "pan", "direction": "positive"})

    log_files = list((tmp_path / "logs").glob("*.jsonl"))
    assert log_files
    assert any("Motion command evaluated" in path.read_text(encoding="utf-8") for path in log_files)


def test_websocket_motion_status_smoke(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        messages = [websocket.receive_json() for _ in range(20)]

    assert "motion.status" in {message["type"] for message in messages}


def test_tracking_dry_run_computes_delta_but_sends_no_command(client: TestClient) -> None:
    response = client.post(
        "/api/motion/track-dry-run",
        json={"frame_width": 640, "frame_height": 360, "target_center_x": 420, "target_center_y": 120},
    )

    body = response.json()
    assert body["accepted"] is True
    assert body["no_physical_command_generated"] is True
    assert body["tracking_preview"]["error_x_px"] == 100
    assert body["tracking_preview"]["computed_pan_delta_deg"] == 5.0


def test_safety_gates_include_motion_gates(client: TestClient) -> None:
    gates = client.get("/api/decision/state").json()["gates"]
    names = {gate["name"] for gate in gates}

    assert "motion_soft_limits_gate" in names
    assert "motion_estop_gate" in names
    assert "motion_fault_gate" in names
    assert "motion_driver_gate" in names
    assert "motion_dry_run_gate" in names
