from pathlib import Path

from fastapi.testclient import TestClient


def test_phase42_cockpit_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200


def test_phase42_ktr_fixture_truth_labels() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    camera = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "FIXTURE_KTR_DEMO" in cockpit
    assert "evidence_truth=fixture" in cockpit
    assert "KTR DEMO FIXTURE - NOT LIVE TARGET" in camera
    assert "FIXTURE VIEW - NOT REAL CAMERA EVIDENCE" in camera
    assert "Real camera path preserved separately" in camera
    assert "showCameraImage" in camera


def test_phase42_projection_explanation_panel_exists() -> None:
    scene_plan = Path("frontend/src/components/cockpit/ScenePlanPanel.vue").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "2D Detection → 3D Digital Twin Mapping" in scene_plan
    assert "bbox center" in scene_plan
    assert "bbox area" in scene_plan
    assert "relative depth" in scene_plan
    assert "read-only visualization" in scene_plan
    assert "projectionXNorm" in cockpit
    assert "projectionArea" in cockpit
    assert "30 mm" in cockpit


def test_phase42_digital_twin_scene_metadata_truthful(client: TestClient) -> None:
    assets = client.get("/api/digital-twin/assets").json()
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert assets["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB"}
    assert assets["selected_asset_path"] in {
        "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "/assets/digital-twin/ktr1_freecad_fidelity.glb",
        "/assets/digital-twin/ktr1_step_hifi_phase54.glb",
        "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb",
    }
    assert assets["no_physical_command_generated"] is True
    assert "ASSET: STL-DERIVED TWIN" in panel
    assert "STL-derived simplified digital twin" in panel
    assert "cameraAnchor" in panel
    assert "launcherAnchor" in panel
    assert "targetRayGroup" in panel
    assert "launcher axis / no physical command" in panel
    assert "aim reference only / no physical command" in panel


def test_phase42_operator_cards_are_ktr_story_driven() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "Fixture selected intentionally" in cockpit
    assert "STL asset loaded" in cockpit
    assert "Twin · STL-derived simplified" in cockpit
    assert "Command path · DISABLED" in cockpit
    assert "fixture truth / camera truth separated" in cockpit
    assert "projection + asset + camera truth" in cockpit
    assert "no_physical_command_generated=true; serial TX disabled" in cockpit


def test_phase42_target_label_clamping() -> None:
    camera = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "Math.min(target.bbox.x, props.width - 360)" in camera
    assert "textLength=\"325\"" in camera
    assert "lengthAdjust=\"spacingAndGlyphs\"" in camera
    assert "x_norm=" in camera
    assert "y_norm=" in camera


def test_phase42_reports_and_contracts_exist() -> None:
    for path in [
        "reports/080_phase42_ktr_digital_twin_presentation.md",
        "reports/081_phase42_operator_cockpit_explainability.md",
        "reports/082_phase42_scene_truth_and_safety_boundary.md",
        "reports/digital_twin_ktr_story_contract.json",
        "reports/cockpit_projection_explainability_contract.json",
        "reports/phase42_safety_boundary_check.md",
    ]:
        text = Path(path).read_text(encoding="utf-8")
        assert "no_physical_command_generated" in text


def test_phase42_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True


def test_phase42_no_physical_command_path_added() -> None:
    files = [
        Path("frontend/src/views/CockpitView.vue"),
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
        Path("frontend/src/components/cockpit/LiveCameraPanel.vue"),
        Path("frontend/src/components/cockpit/ScenePlanPanel.vue"),
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
