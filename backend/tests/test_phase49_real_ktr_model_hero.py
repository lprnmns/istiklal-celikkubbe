from pathlib import Path

from fastapi.testclient import TestClient


def test_phase49_real_model_asset_pipeline_outputs_exist() -> None:
    glb = Path("frontend/public/assets/digital-twin/ktr1_operator_hero.glb")
    manifest = Path("frontend/public/assets/digital-twin/ktr1_operator_hero_manifest.json")
    public_manifest = Path("frontend/public/assets/digital-twin/asset_manifest.json")

    assert glb.exists()
    assert glb.stat().st_size > 1_000_000
    text = manifest.read_text(encoding="utf-8")
    assert '"selected_asset_type": "REAL_GLB"' in text
    assert '"source_asset"' in text
    assert '"triangle_count_before": 200512' in text
    assert '"no_physical_command_generated": true' in text
    assert '"selected_asset_path": "/assets/digital-twin/ktr1_kinematic_world_phase55.glb"' in public_manifest.read_text(encoding="utf-8")


def test_phase49_assets_api_reports_real_glb_hero(client: TestClient) -> None:
    payload = client.get("/api/digital-twin/assets").json()

    assert payload["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_GLB", "REAL_STEP_HIFI_GLB", "HYBRID_FIDELITY_GLB"}
    assert payload["selected_asset_path"] in {
        "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "/assets/digital-twin/ktr1_freecad_fidelity.glb",
        "/assets/digital-twin/ktr1_step_hifi_phase54.glb",
        "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb",
    }
    assert payload["preferred_browser_asset"] in {
        "/assets/digital-twin/ktr1_kinematic_world_phase55.glb",
        "/assets/digital-twin/ktr1_freecad_fidelity.glb",
        "/assets/digital-twin/ktr1_step_hifi_phase54.glb",
        "/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb",
    }
    assert payload["asset_fallback_reason"] in {"Phase 55 kinematic STEP GLB active; visualization-only yaw/pitch metadata loaded", "colored STEP GLB active", "browser_friendly_asset_available", "Phase 54 STEP HiFi GLB active; no fallback used", "Phase 54 hybrid fidelity GLB active; no physical command path"}
    assert payload["no_physical_command_generated"] is True


def test_phase49_cockpit_routes_and_quality_modes_render(client: TestClient) -> None:
    for route in [
        "/cockpit",
        "/cockpit?quality=high",
        "/cockpit?quality=balanced",
        "/cockpit?quality=low",
        "/cockpit?perception=off",
        "/cockpit?ktr_demo=1&quality=high",
        "/cockpit?ktr_demo=1&perception=off&quality=high",
    ]:
        assert client.get(route).status_code == 200


def test_phase49_digital_twin_uses_real_model_default_and_overlays() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "sceneMode = ref<'realStepModel' | 'tacticalOverlay' | 'topDown' | 'cadDebug'>" in panel
    assert "ktr1_freecad_fidelity.glb" in panel
    assert "GLTFLoader" in panel
    assert "REAL KTR DIGITAL TWIN" in panel
    assert "STEP FALLBACK ACTIVE" in panel
    assert "Camera axis" in panel
    assert "Launcher axis" in panel
    assert "30 mm offset" in panel
    assert "Target #" in panel
    assert "new STLLoader" not in panel


def test_phase49_yolo_toggle_and_quality_labels_present() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    camera = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "perception=off" in cockpit
    assert "quality" in cockpit
    assert "30 FPS Target" in cockpit
    assert "15 FPS Cap" in cockpit
    assert "10 FPS Low" in cockpit
    assert "YOLO ON" in camera
    assert "YOLO OFF" in camera
    assert "camera only" in camera


def test_phase49_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()
    files = [
        Path("frontend/src/views/CockpitView.vue"),
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
        Path("frontend/src/components/cockpit/LiveCameraPanel.vue"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)

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
