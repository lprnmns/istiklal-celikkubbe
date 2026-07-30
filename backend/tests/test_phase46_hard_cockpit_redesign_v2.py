from pathlib import Path

from fastapi.testclient import TestClient


def test_phase46_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200
    assert client.get("/cockpit?ktr_demo=1&perf=low").status_code == 200


def test_phase46_tactical_twin_replaces_stl_primary_render() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "STLLoader remains an engineering asset pipeline reference" in panel
    assert "uses tactical simplified geometry for the main cockpit scene" in panel
    assert "STL-derived tactical twin" in panel
    assert "ASSET: CAD-REF TWIN" in panel
    assert "proceduralGroup.scale.setScalar(1.34)" in panel
    assert "new THREE.PerspectiveCamera(36" in panel


def test_phase46_camera_hud_hides_raw_debug_values() -> None:
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "KTR fixture view · no live target claim" in panel
    assert "Laptop dev frame · not USB acceptance" in panel
    assert "source: {{ cleanSource }}" in panel
    assert "truth: {{ evidenceTruth }}" in panel
    assert "device={{" not in panel
    assert "backend={{" not in panel


def test_phase46_header_and_cards_use_presentation_labels() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "PHASE 46" in cockpit
    assert "Camera · ${cameraHeaderLabel.value}" in cockpit
    assert "USB Camera ·" in cockpit
    assert "Digital Twin · Tactical CAD-ref" in cockpit
    assert "Tactical twin active" in cockpit
    assert "KTR fixture view · truth=fixture" in cockpit


def test_phase46_reports_exist() -> None:
    required = [
        "reports/093_phase46_hard_cockpit_redesign_v2.md",
        "reports/094_phase46_tactical_digital_twin_scene.md",
        "reports/095_phase46_camera_hud_operator_visual.md",
        "reports/096_phase46_ktr_demo_presentation_mode.md",
        "reports/phase46_visual_acceptance_contract.json",
        "reports/phase46_performance_contract.json",
        "reports/phase46_safety_boundary_check.md",
        "reports/screenshots/phase46_hard_cockpit_redesign_v2/screenshot_manifest.json",
    ]
    for path in required:
        assert Path(path).exists(), path


def test_phase46_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
