import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_phase52_freecad_match_world_contract_files() -> None:
    manifest = json.loads(Path("frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json").read_text(encoding="utf-8"))
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert manifest["source_asset"] == "work/ktr1.step"
    assert manifest["output_asset"] == "/assets/digital-twin/ktr1_freecad_fidelity.glb"
    assert manifest["fallback_used"] is False
    assert manifest["color_count"] >= 6
    assert manifest["mesh_count"] >= 100
    assert Path("frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb").exists()
    assert "FREECAD MATCH VIEWER" in panel
    assert "OrthographicCamera" in panel
    assert "EdgesGeometry" in panel
    assert "material_debug_table" in panel
    assert "Showcase World" in panel
    assert "Tactical Overlay" in panel
    assert "mode=freecad" in panel or "freecadMatch" in panel


def test_phase52_world_routes_render(client: TestClient) -> None:
    for route in [
        "/cockpit/world",
        "/cockpit/world?quality=ultra",
        "/cockpit/world?quality=ultra&mode=freecad",
        "/cockpit/world?quality=ultra&mode=showcase",
        "/cockpit/world?quality=ultra&mode=tactical",
    ]:
        assert client.get(route).status_code == 200


def test_phase52_ui_clutter_and_overlay_contract() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "showTacticalOverlays" in panel
    assert "showModelLabels" in panel
    assert "freecad-layout" in panel
    assert "world-layout" in panel
    assert "Full 3D World" in panel
    assert "PHASE 52" in cockpit
    assert "reports/screenshots/phase52_freecad_match_world/" in cockpit


def test_phase52_safety_invariants(client: TestClient) -> None:
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
