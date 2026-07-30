import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_phase54_asset_candidates_and_default_exist() -> None:
    step = Path("frontend/public/assets/digital-twin/ktr1_step_hifi_phase54_manifest.json")
    stl = Path("frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54_manifest.json")
    hybrid = Path("frontend/public/assets/digital-twin/ktr1_hybrid_fidelity_phase54_manifest.json")
    public = json.loads(Path("frontend/public/assets/digital-twin/asset_manifest.json").read_text(encoding="utf-8"))

    for manifest_path in [step, stl, hybrid]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        output = Path("frontend/public") / manifest["output_asset"].lstrip("/")
        assert output.exists()
        assert manifest["triangle_count"] > 100_000
        assert manifest["no_physical_command_generated"] is True

    assert public["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_HIFI_GLB"}
    assert public["selected_asset_path"] in {"/assets/digital-twin/ktr1_kinematic_world_phase55.glb", "/assets/digital-twin/ktr1_step_hifi_phase54.glb"}
    assert public["triangle_count"] > 1_000_000


def test_phase54_assets_api_reports_hifi_default(client: TestClient) -> None:
    assets = client.get("/api/digital-twin/assets").json()

    assert assets["selected_asset_type"] in {"REAL_STEP_KINEMATIC_GLB", "REAL_STEP_HIFI_GLB"}
    assert assets["selected_asset_path"] in {"/assets/digital-twin/ktr1_kinematic_world_phase55.glb", "/assets/digital-twin/ktr1_step_hifi_phase54.glb"}
    assert assets["preferred_browser_asset"] in {"/assets/digital-twin/ktr1_kinematic_world_phase55.glb", "/assets/digital-twin/ktr1_step_hifi_phase54.glb"}
    assert assets["source_cad_path"] == "work/ktr1.step"
    assert assets["no_physical_command_generated"] is True


def test_phase54_ui_has_asset_compare_and_weapon_inspector_tools() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    for text in [
        "STEP HiFi",
        "STL Geometry",
        "Hybrid Fidelity",
        "Previous GLB",
        "Weapon Focus",
        "Front Weapon Closeup",
        "Wireframe",
        "X-Ray",
        "Exploded View",
        "ktr1_step_hifi_phase54.glb",
        "ktr1_hybrid_fidelity_phase54.glb",
    ]:
        assert text in panel
    assert "PHASE 54" in cockpit
    assert "reports/screenshots/phase54_model_fidelity_fix/" in cockpit


def test_phase54_reports_and_screenshots_exist() -> None:
    for path in [
        "reports/142_phase54_asset_inventory.md",
        "reports/143_phase54_step_conversion_diagnostics.md",
        "reports/144_phase54_stl_geometry_fallback.md",
        "reports/145_phase54_hybrid_asset_decision.md",
        "reports/146_phase54_weapon_visibility_acceptance.md",
        "reports/147_phase54_model_inspector_tools.md",
        "reports/148_phase54_freecad_match_visual_validation.md",
        "reports/149_phase54_safety_boundary_check.md",
        "reports/phase54_visual_acceptance_contract.json",
    ]:
        assert Path(path).exists()
    for name in [
        "browser_step_hifi_same_angle.png",
        "weapon_focus_closeup.png",
        "front_weapon_closeup.png",
        "asset_compare_selector_visible.png",
        "safety_no_physical_command.png",
    ]:
        assert Path("reports/screenshots/phase54_model_fidelity_fix", name).exists()


def test_phase54_safety_invariants(client: TestClient) -> None:
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
