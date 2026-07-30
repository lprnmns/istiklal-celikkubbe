from pathlib import Path

from fastapi.testclient import TestClient


def test_phase41_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200


def test_phase41_asset_transform_contract_and_api(client: TestClient) -> None:
    contract = Path("reports/digital_twin_asset_transform_contract.json")
    assert contract.exists()

    assets = client.get("/api/digital-twin/assets").json()
    assert assets["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB"}
    assert assets["selected_asset_path"] in {
        "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "/assets/digital-twin/ktr1_freecad_fidelity.glb",
        "/assets/digital-twin/ktr1_step_hifi_phase54.glb",
        "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb",
    }
    assert assets["asset_transform"]["scale"]["x"] == 1
    assert assets["asset_transform"]["camera_mount_anchor"]["source"] == "estimated_from_kamera_part_or_manual_anchor"
    assert assets["asset_transform"]["launcher_axis_anchor"]["source"] == "estimated_from_launcher_like_part_or_manual_anchor"
    assert assets["no_physical_command_generated"] is True


def test_phase41_camera_truth_and_fixture_labels() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "FIXTURE VIEW - NOT REAL CAMERA EVIDENCE" in cockpit
    assert "LAPTOP CAMERA DEV - REAL FRAME" in cockpit
    assert "KTR DEMO FIXTURE - NOT LIVE TARGET" in panel
    assert "evidence_truth" in panel
    assert "labelX(target)" in panel
    assert "textLength=\"325\"" in panel


def test_phase41_projection_semantics_visible() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "aim reference only / no physical command" in panel
    assert "bbox_area_ratio" in panel
    assert "normalized_center_x" in panel
    assert "normalized_center_y" in panel
    assert "estimated_range_band === 'near' ? 1.38" in panel


def test_phase41_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True


def test_phase41_no_physical_command_path_added() -> None:
    files = [
        Path("frontend/src/views/CockpitView.vue"),
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
        Path("frontend/src/components/cockpit/LiveCameraPanel.vue"),
        Path("backend/app/services/digital_twin_service.py"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for forbidden in [
        "send_fire_command(",
        "set_servo_position(",
        "gpio_write(",
        "pwm_write(",
        "step_pulse(",
        "serial_tx_enabled: true",
        "physical_command_enabled: true",
        "SPD,",
        "LZR",
        "STP",
    ]:
        assert forbidden not in combined
