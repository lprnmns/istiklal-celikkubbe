import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_phase50_colored_step_glb_and_manifest_exist() -> None:
    glb = Path("frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb")
    manifest_path = Path("frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert Path("work/ktr1.step").exists()
    assert glb.exists()
    assert glb.stat().st_size > 1_000_000
    assert manifest["source_asset"] == "work/ktr1.step"
    assert manifest["selected_asset_type"] == "REAL_STEP_GLB"
    assert manifest["output_asset"] == "/assets/digital-twin/ktr1_freecad_fidelity.glb"
    assert manifest["fallback_used"] is False
    assert manifest["source_stl_path"] is None
    assert manifest["color_count"] >= 4
    assert manifest["mesh_count"] > 1
    assert manifest["triangle_count"] > 10_000
    assert manifest["no_physical_command_generated"] is True


def test_phase50_assets_api_reports_colored_step_default(client: TestClient) -> None:
    payload = client.get("/api/digital-twin/assets").json()

    assert payload["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB"}
    assert payload["selected_asset_path"] in {"/assets/digital-twin/ktr1_kinematic_world_phase55.glb", "/assets/digital-twin/ktr1_colored_step_hero.glb", "/assets/digital-twin/ktr1_freecad_fidelity.glb", "/assets/digital-twin/ktr1_step_hifi_phase54.glb", "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb"}
    assert payload["preferred_browser_asset"] in {"/assets/digital-twin/ktr1_kinematic_world_phase55.glb", "/assets/digital-twin/ktr1_colored_step_hero.glb", "/assets/digital-twin/ktr1_freecad_fidelity.glb", "/assets/digital-twin/ktr1_step_hifi_phase54.glb", "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb"}
    assert payload["source_cad_path"] in {"ktr1.step", "work/ktr1.step"}
    assert payload["device_model"]["status"] in {"available", "placeholder"}


def test_phase50_interactive_step_world_ui_contract() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "REAL KTR DIGITAL TWIN" in panel
    assert "Interactive colored STEP twin + tactical projection overlay" in panel or "FreeCAD-fidelity colored STEP twin" in panel
    assert "ktr1_freecad_fidelity.glb" in panel
    assert "OrbitControls" in panel
    assert "Real STEP Model" in panel
    assert "Tactical Overlay" in panel
    assert "Top-down" in panel
    assert "CAD Debug" in panel
    assert "Operator View" in panel
    assert "Chase / Launcher Axis" in panel
    assert "Target POV" in panel
    assert "STEP FALLBACK ACTIVE" in panel
    assert "new STLLoader" not in panel


def test_phase50_routes_and_quality_modes_render(client: TestClient) -> None:
    for route in [
        "/cockpit",
        "/cockpit?quality=high",
        "/cockpit?quality=balanced",
        "/cockpit?quality=low",
        "/cockpit?perception=off",
        "/cockpit?ktr_demo=1",
        "/cockpit?ktr_demo=1&quality=high",
        "/cockpit?ktr_demo=1&perception=off&quality=high",
    ]:
        assert client.get(route).status_code == 200


def test_phase50_safety_invariants(client: TestClient) -> None:
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
