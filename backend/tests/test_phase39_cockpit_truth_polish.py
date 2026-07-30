from pathlib import Path

from fastapi.testclient import TestClient


def test_phase39_camera_live_claim_requires_real_frame_evidence() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "REAL_LAPTOP_CAMERA_LIVE' && runtime.cameraStatus.is_real_camera_evidence" in cockpit
    assert "LAPTOP CAMERA FRAME PENDING" in cockpit


def test_phase39_asset_manifest_and_fallback_are_explicit(client: TestClient) -> None:
    manifest = Path("frontend/public/assets/digital-twin/asset_manifest.json")
    assert manifest.exists()
    assets = client.get("/api/digital-twin/assets").json()

    assert assets["device_model"]["status"] in {"available", "placeholder"}
    assert assets["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB", "REAL_GLB", "REAL_STL", "CAD_SOURCE_ONLY", "PROCEDURAL_FALLBACK"}
    assert "procedural" in assets["asset_fallback_reason"].lower() or assets["preferred_browser_asset"] or assets["selected_asset_type"] == "REAL_STL"
    assert assets["no_physical_command_generated"] is True


def test_phase39_digital_twin_camera_truth_fields_present(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    camera = state["camera"]

    assert "selected_device" in camera
    assert "is_real_camera_evidence" in camera
    if camera["source_mode"] == "REAL_LAPTOP_CAMERA_LIVE":
        assert camera["is_real_camera_evidence"] is True
    assert state["no_physical_command_generated"] is True


def test_phase39_cockpit_ktr_demo_route_renders(client: TestClient) -> None:
    response = client.get("/cockpit?ktr_demo=1")

    assert response.status_code == 200


def test_phase39_target_label_clamping_and_no_placeholder_rows() -> None:
    camera_panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "labelX(target)" in camera_panel
    assert "textLength=\"325\"" in camera_panel
    assert "USB camera good" not in cockpit
    assert "OFFLINE_EXPECTED" in cockpit


def test_phase39_no_physical_command_path_added() -> None:
    files = [
        Path("frontend/src/views/CockpitView.vue"),
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
        Path("frontend/src/components/cockpit/LiveCameraPanel.vue"),
        Path("backend/app/services/digital_twin_service.py"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for forbidden in ["send_fire_command(", "set_servo_position(", "gpio_write(", "pwm_write(", "step_pulse(", "serial_tx_enabled: true", "physical_command_enabled: true"]:
        assert forbidden not in combined
