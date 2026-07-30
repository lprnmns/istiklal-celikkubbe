import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_phase55_asset_audit_and_kinematics_exist() -> None:
    audit = json.loads(Path("reports/phase55_asset_audit.json").read_text(encoding="utf-8"))
    kinematics = json.loads(Path("frontend/public/assets/digital-twin/ktr1_kinematics.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path("frontend/public/assets/digital-twin/asset_manifest.json").read_text(encoding="utf-8"))

    assert audit["source_step_path"].endswith("ktr1.step")
    assert audit["shape_count"] >= 100
    assert audit["front_launcher_camera_detail_detected"] is True
    assert audit["step_import_preserves_hierarchy"] is False
    assert kinematics["assetVersion"] == "phase55"
    assert kinematics["visualizationOnly"] is True
    assert kinematics["source"]["cadPath"] == "work/ktr1.step"
    assert kinematics["source"]["glbPath"] == "/assets/digital-twin/ktr1_kinematic_world_phase55.glb"
    assert kinematics["groups"]["static_root"]
    assert kinematics["groups"]["yaw_group"]
    assert kinematics["groups"]["pitch_group"]
    assert kinematics["groups"]["camera_group"]
    assert kinematics["groups"]["launcher_group"]
    assert kinematics["pivots"]["yaw_pivot"]["position"]
    assert kinematics["pivots"]["pitch_pivot"]["position"]
    assert kinematics["anchors"]["camera_origin"]["position"]
    assert kinematics["anchors"]["launcher_origin"]["position"]
    assert manifest["selected_asset_type"] == "REAL_STEP_KINEMATIC_GLB"
    assert Path("frontend/public/assets/digital-twin/ktr1_kinematic_world_phase55.glb").exists()


def test_phase55_assets_api_reports_kinematic_default(client: TestClient) -> None:
    assets = client.get("/api/digital-twin/assets").json()

    assert assets["selected_asset_type"] == "REAL_STEP_KINEMATIC_GLB"
    assert assets["selected_asset_path"] == "/assets/digital-twin/ktr1_kinematic_world_phase55.glb"
    assert assets["preferred_browser_asset"] == "/assets/digital-twin/ktr1_kinematic_world_phase55.glb"
    assert assets["source_cad_path"] == "work/ktr1.step"
    assert assets["no_physical_command_generated"] is True


def test_phase55_runtime_has_kinematic_preview_and_inspector() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    for text in [
        "ktr1_kinematic_world_phase55.glb",
        "ktr1_kinematics.json",
        "yawPreviewDeg",
        "pitchPreviewDeg",
        "Kinematic STEP",
        "Part inspector",
        "Reset Pose",
        "yaw_pivot",
        "pitch_pivot",
    ]:
        assert text in panel
    assert "PHASE 55" in cockpit
    assert "reports/screenshots/phase55_kinematic_digital_twin/" in cockpit


def test_phase55_reports_exist() -> None:
    for path in [
        "reports/phase55_asset_audit.md",
        "reports/phase55_asset_audit.json",
        "reports/phase55_glb_node_hierarchy.md",
        "reports/phase55_kinematic_grouping.md",
        "reports/phase55_pivot_anchor_report.md",
        "reports/phase55_blender_authoring.md",
        "reports/phase55_visual_validation.md",
        "reports/phase55_safety_boundary_check.md",
    ]:
        assert Path(path).exists()


def test_phase55_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()
    files = [
        Path("frontend/src/views/CockpitView.vue"),
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
        Path("frontend/src/utils/digitalTwinKinematics.ts"),
        Path("frontend/public/assets/digital-twin/ktr1_kinematics.json"),
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
