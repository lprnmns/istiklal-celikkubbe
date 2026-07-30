from pathlib import Path

from fastapi.testclient import TestClient


def test_direction_simulation_no_physical_command(client: TestClient) -> None:
    response = client.post("/api/calibration/direction/simulate", json={"target_position": "right", "frame_width": 640, "frame_height": 360})
    assert response.status_code == 200
    body = response.json()
    assert body["target_visual_side"] == "right"
    assert body["target_error_x"] > 0
    assert body["required_camera_motion"] == "pan_right"
    assert body["expected_image_response"] == "target_should_move_left_toward_center"
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True


def test_direction_observation_multiplier_calculation(client: TestClient) -> None:
    x_normal = client.post(
        "/api/calibration/direction/record-observation",
        json={
            "simulated_axis": "x",
            "system_expected_motion": "camera_right",
            "operator_observed_motion": "camera_right",
            "operator_confidence": "confirmed",
        },
    )
    assert x_normal.status_code == 200
    assert x_normal.json()["suggested_x_axis_multiplier"] == 1

    x_inverted = client.post(
        "/api/calibration/direction/record-observation",
        json={
            "simulated_axis": "x",
            "system_expected_motion": "camera_right",
            "operator_observed_motion": "camera_left",
            "operator_confidence": "confirmed",
        },
    )
    assert x_inverted.status_code == 200
    assert x_inverted.json()["suggested_x_axis_multiplier"] == -1

    y_normal = client.post(
        "/api/calibration/direction/record-observation",
        json={
            "simulated_axis": "y",
            "system_expected_motion": "camera_up",
            "operator_observed_motion": "camera_up",
            "operator_confidence": "confirmed",
        },
    )
    assert y_normal.status_code == 200
    assert y_normal.json()["suggested_y_axis_multiplier"] == 1

    y_inverted = client.post(
        "/api/calibration/direction/record-observation",
        json={
            "simulated_axis": "y",
            "system_expected_motion": "camera_up",
            "operator_observed_motion": "camera_down",
            "operator_confidence": "confirmed",
        },
    )
    assert y_inverted.status_code == 200
    assert y_inverted.json()["suggested_y_axis_multiplier"] == -1
    assert y_inverted.json()["physical_command_enabled"] is False


def test_direction_axis_swap_suspected(client: TestClient) -> None:
    response = client.post(
        "/api/calibration/direction/record-observation",
        json={
            "simulated_axis": "x",
            "system_expected_motion": "camera_right",
            "operator_observed_motion": "camera_up",
            "operator_confidence": "confirmed",
        },
    )
    assert response.status_code == 200
    assert response.json()["axis_swap_suspected"] is True
    profile = client.post("/api/calibration/direction/save-profile")
    assert profile.status_code == 200
    assert profile.json()["axis_swap"] is True
    assert profile.json()["no_physical_command_generated"] is True


def test_direction_exports_and_ktr_files(client: TestClient) -> None:
    client.post("/api/calibration/direction/simulate", json={"target_position": "up"})
    client.post(
        "/api/calibration/direction/record-observation",
        json={
            "simulated_axis": "y",
            "system_expected_motion": "camera_up",
            "operator_observed_motion": "camera_up",
            "operator_confidence": "confirmed",
        },
    )
    lab = client.post("/api/data-lab/export")
    assert lab.status_code == 200
    lab_files = {Path(path).name: Path(path) for path in lab.json()["files"]}
    assert {
        "direction_calibration_profile.json",
        "direction_simulation_summary.md",
        "direction_observation_log.json",
        "motion_semantics_contract.md",
    } <= set(lab_files)
    assert "no_physical_command_generated=true" in lab_files["motion_semantics_contract.md"].read_text(encoding="utf-8")

    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase27 direction semantics"})
    assert export.status_code == 200
    report_files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert {
        "direction_calibration_profile.json",
        "direction_simulation_summary.md",
        "motion_semantics_contract.md",
        "direction_safety_boundary.md",
    } <= set(report_files)
    ktr = report_files["ktr_4_3_interfaces.md"].read_text(encoding="utf-8")
    assert "Motion Direction Semantics and Calibration Interface" in ktr
    assert "no_physical_command_generated=true" in ktr


def test_direction_forbidden_paths_not_runtime_commands(client: TestClient) -> None:
    client.post("/api/calibration/direction/simulate", json={"target_position": "left"})
    status = client.get("/api/calibration/direction/status").json()
    text = str(status).upper()
    for token in ["MOTOR JOG", "SERIAL WRITE", "TMC_CURRENT", "FIRE", "TRIGGER", "SHOOT", "HARDWARE ENABLE"]:
        assert token not in text
    assert status["physical_command_enabled"] is False
    assert status["no_physical_command_generated"] is True
