from pathlib import Path

from fastapi.testclient import TestClient


def test_phase53_cockpit_is_scrollable_3d_first_layout() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "PHASE 53" in cockpit
    assert "hero-world-section" in cockpit
    assert "min-height: 720px" in cockpit
    assert "height: 82vh" in cockpit
    assert "overflow-y: auto" in cockpit
    assert "camera-secondary-section" in cockpit
    assert "mission-grid-primary" in cockpit
    assert "mission-grid-secondary" in cockpit
    assert "reports/screenshots/phase53_3d_world_layout_priority/" in cockpit
    assert "height: clamp(540px, calc(100vh - 420px), 630px)" not in cockpit


def test_phase53_world_viewer_and_clutter_contract() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "geometryDrawerOpen" in panel
    assert "Geometry Details" in panel
    assert "requestFullscreen" in panel
    assert "Fullscreen" in panel
    assert "Open Full 3D World" in panel
    assert "min-height: 90vh" in panel
    assert "min-height: calc(90vh - 96px)" in panel
    assert "toolbar-select" in panel
    assert "fovVisible" in panel
    assert "targetVisible" in panel
    assert "labelMode.value !== 'clean'" in panel


def test_phase53_routes_render(client: TestClient) -> None:
    for route in [
        "/cockpit",
        "/cockpit?quality=ultra",
        "/cockpit?quality=high",
        "/cockpit?quality=balanced",
        "/cockpit?quality=low",
        "/cockpit?perception=off",
        "/cockpit?ktr_demo=1",
        "/cockpit/world",
        "/cockpit/world?quality=ultra",
        "/cockpit/world?quality=ultra&mode=freecad",
        "/cockpit/world?quality=ultra&mode=showcase",
        "/cockpit/world?quality=ultra&mode=tactical",
    ]:
        assert client.get(route).status_code == 200


def test_phase53_safety_invariants(client: TestClient) -> None:
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
