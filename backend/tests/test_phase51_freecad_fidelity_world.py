import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_phase51_freecad_reference_and_fidelity_asset_exist() -> None:
    manifest = json.loads(Path("frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json").read_text(encoding="utf-8"))

    assert Path("work/ktr1.step").exists()
    assert Path("frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb").stat().st_size > 1_000_000
    assert manifest["source_asset"] == "work/ktr1.step"
    assert manifest["material_preservation_status"] == "reconstructed"
    assert manifest["step_color_records"] >= 1
    assert manifest["freecad_reference_generated"] is True
    assert manifest["color_count"] >= 6
    assert manifest["mesh_count"] >= 100
    assert manifest["triangle_count"] > 100_000
    for name in ["freecad_reference_operator.png", "freecad_reference_front.png", "freecad_reference_top.png"]:
        assert Path("reports/screenshots/phase51_freecad_fidelity_reference", name).exists()


def test_phase51_world_route_and_asset_api(client: TestClient) -> None:
    assets = client.get("/api/digital-twin/assets").json()

    assert client.get("/cockpit/world").status_code == 200
    assert client.get("/cockpit/world?quality=ultra").status_code == 200
    assert assets["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB"}
    assert assets["selected_asset_path"] in {
        "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "/assets/digital-twin/ktr1_freecad_fidelity.glb",
        "/assets/digital-twin/ktr1_step_hifi_phase54.glb",
        "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb",
    }
    assert assets["source_cad_path"] == "work/ktr1.step"


def test_phase51_model_first_ui_and_controls_contract() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "/cockpit/world" in panel
    assert "REAL KTR DIGITAL TWIN WORLD" in panel
    assert "FreeCAD-fidelity colored STEP twin" in panel
    assert "Full 3D World" in panel
    assert "labelMode" in panel
    assert "QUALITY ULTRA / 60 FPS" in panel
    assert "ACESFilmicToneMapping" in panel
    assert "HemisphereLight" in panel
    assert "OrbitControls" in panel
    assert "worldMode" in cockpit
    assert "world-main-grid" in cockpit


def test_phase51_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            Path("frontend/src/views/CockpitView.vue"),
            Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
            Path("frontend/src/components/cockpit/LiveCameraPanel.vue"),
        ]
    )

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
    for forbidden in [
        "send_fire_command(",
        "set_servo_position(",
        "gpio_write(",
        "pwm_write(",
        "step_pulse(",
        "serial_tx_enabled: true",
        "physical_command_enabled: true",
    ]:
        assert forbidden not in combined
