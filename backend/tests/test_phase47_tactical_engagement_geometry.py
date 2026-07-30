from pathlib import Path

from fastapi.testclient import TestClient


def test_phase47_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200
    assert client.get("/cockpit?ktr_demo=1&perf=low").status_code == 200


def test_phase47_replaces_toy_turret_with_engagement_geometry() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "TACTICAL ENGAGEMENT VIEW" in panel
    assert "Camera FOV + launcher axis + target projection" in panel
    assert "CAD-referenced tactical twin" in panel
    assert "Top-down map" in panel
    assert "Camera module" in panel
    assert "Launcher axis" in panel
    assert "30 mm camera-launcher offset" in panel
    assert "new THREE.Mesh(" not in panel


def test_phase47_projection_mapping_function_is_deterministic() -> None:
    mapping = Path("frontend/src/utils/engagementGeometry.ts").read_text(encoding="utf-8")

    assert "mapDetectionToEngagementGeometry" in mapping
    assert "target_scene_x" in mapping
    assert "target_scene_y" in mapping
    assert "target_scene_depth" in mapping
    assert "target_inside_fov" in mapping
    assert "launcher_axis_error_x" in mapping
    assert "launcher_axis_error_y" in mapping
    assert "INSIDE_FOV_FIRE_BLOCKED" in mapping
    assert "no_physical_command_generated: true" in mapping


def test_phase47_bottom_cards_and_log_are_operator_oriented() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    scene = Path("frontend/src/components/cockpit/ScenePlanPanel.vue").read_text(encoding="utf-8")
    log = Path("frontend/src/components/cockpit/OperatorLogPanel.vue").read_text(encoding="utf-8")
    evidence = Path("frontend/src/components/cockpit/EvidenceReplayPanel.vue").read_text(encoding="utf-8")

    assert "PHASE 47" in cockpit
    assert "Digital Twin · Engagement Geometry" in cockpit
    assert "KTR fixture selected" in cockpit
    assert "Target projected into FOV" in cockpit
    assert "Fire gate blocked" in cockpit
    assert "reports/screenshots/phase47_tactical_engagement_geometry/" in cockpit
    assert "Engagement Geometry" in scene
    assert "Target bearing" in scene
    assert "Offset comp." in scene
    assert "Fire gate" in scene
    assert "MAX_VISIBLE_EVENTS = 3" in log
    assert "phase47" in evidence


def test_phase47_reports_exist() -> None:
    required = [
        "reports/097_phase47_tactical_engagement_geometry.md",
        "reports/098_phase47_3d_twin_readability_fix.md",
        "reports/099_phase47_bbox_to_fov_projection_visual.md",
        "reports/100_phase47_cad_reference_vs_operator_twin.md",
        "reports/phase47_visual_acceptance_contract.json",
        "reports/phase47_projection_mapping_contract.json",
        "reports/phase47_safety_boundary_check.md",
        "reports/screenshots/phase47_tactical_engagement_geometry/screenshot_manifest.json",
    ]
    for path in required:
        assert Path(path).exists(), path


def test_phase47_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
