from pathlib import Path

from fastapi.testclient import TestClient


def test_phase40_asset_manifest_selects_explicit_asset() -> None:
    manifest = Path("frontend/public/assets/digital-twin/asset_manifest.json").read_text(encoding="utf-8")

    assert '"selected_asset_type": "REAL_STEP_KINEMATIC_GLB"' in manifest
    assert '"selected_asset_path": "/assets/digital-twin/ktr1_kinematic_world_phase55.glb"' in manifest
    assert '"source_stl_path"' in manifest
    assert '"no_physical_command_generated": true' in manifest


def test_phase40_digital_twin_assets_reports_stl_model(client: TestClient) -> None:
    payload = client.get("/api/digital-twin/assets").json()

    assert payload["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB"}
    assert payload["selected_asset_path"] in {
        "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "/assets/digital-twin/ktr1_freecad_fidelity.glb",
        "/assets/digital-twin/ktr1_step_hifi_phase54.glb",
        "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb",
    }
    assert "ktr1.step" in str(payload["source_cad_path"])
    assert payload["device_model"]["status"] in {"available", "placeholder"}
    assert payload["no_physical_command_generated"] is True


def test_phase40_cockpit_ktr_demo_and_truth_labels(client: TestClient) -> None:
    assert client.get("/cockpit?ktr_demo=1").status_code == 200

    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    camera_panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")
    digital_twin = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "KTR DEMO" in cockpit
    assert "KTR DEMO FIXTURE" in camera_panel
    assert "NOT REAL CAMERA EVIDENCE" in camera_panel
    assert "PICO OFFLINE_EXPECTED" in cockpit
    assert "USB OFFLINE_EXPECTED" in cockpit
    assert "STLLoader" in digital_twin
    assert "launcher axis / no physical command" in digital_twin


def test_phase40_safety_invariants_preserved(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["no_physical_command_generated"] is True
    assert state["safety"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True


def test_phase40_no_physical_command_path_added() -> None:
    files = [
        Path("frontend/src/views/CockpitView.vue"),
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
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
