from pathlib import Path

from fastapi.testclient import TestClient


def test_phase48_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200
    assert client.get("/cockpit?ktr_demo=1&perf=low").status_code == 200


def test_phase48_real_3d_operator_twin_is_default() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "REAL 3D DIGITAL TWIN" in panel
    assert "Clean operator twin + tactical projection overlay" in panel
    assert "sceneMode = ref<'tactical3d' | 'topdown' | 'cad'>('tactical3d')" in panel
    assert "dynamic import('three')" in panel
    assert "powerPreference: 'low-power'" in panel
    assert "GLB preferred / procedural low-poly active" in panel
    assert "CAD/STL Reference Preserved" in panel
    assert "new STLLoader" not in panel


def test_phase48_3d_scene_contains_required_operational_anchors() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "Camera module" in panel
    assert "Camera axis" in panel
    assert "Launcher axis" in panel
    assert "30 mm offset" in panel
    assert "Fire gate:" in panel
    assert "Target #" in panel
    assert "rangeBands3d = [5, 10, 15]" in panel
    assert "Top-down map" in panel


def test_phase48_mapping_and_evidence_paths() -> None:
    mapping = Path("frontend/src/utils/engagementGeometry.ts").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    evidence = Path("frontend/src/components/cockpit/EvidenceReplayPanel.vue").read_text(encoding="utf-8")

    assert "mapDetectionToEngagementGeometry" in mapping
    assert "target_scene_depth" in mapping
    assert "reports/screenshots/phase48_real_3d_digital_twin_rebuild/" in cockpit
    assert "PHASE 48" in cockpit
    assert "phase48" in evidence


def test_phase48_reports_exist() -> None:
    required = [
        "reports/101_phase48_real_3d_digital_twin_rebuild.md",
        "reports/102_phase48_3d_asset_pipeline_decision.md",
        "reports/103_phase48_camera_to_3d_projection_consistency.md",
        "reports/104_phase48_performance_and_rendering_strategy.md",
        "reports/105_phase48_safety_boundary_check.md",
        "reports/phase48_visual_acceptance_contract.json",
        "reports/phase48_3d_scene_contract.json",
        "reports/phase48_performance_contract.json",
        "reports/screenshots/phase48_real_3d_digital_twin_rebuild/screenshot_manifest.json",
    ]
    for path in required:
        assert Path(path).exists(), path


def test_phase48_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
