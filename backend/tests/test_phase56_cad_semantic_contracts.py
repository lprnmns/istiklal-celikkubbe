import json
from pathlib import Path


def _json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_phase56_semantic_audit_outputs_exist() -> None:
    audit = _json("reports/phase56_step_semantic_audit.json")
    tree = _json("reports/phase56_step_assembly_tree.json")

    assert audit["sourceCadPath"] == "work/ktr1.step"
    assert audit["freecad"]["partFeatureCount"] >= 100
    assert audit["step"]["record_counts"]["NEXT_ASSEMBLY_USAGE_OCCURRENCE"] > 0
    assert audit["step"]["record_counts"]["COLOUR_RGB"] > 0
    assert audit["diagnosis"]["webRendererCapacityIsPrimaryCause"] is False
    assert audit["diagnosis"]["exactAssemblyTreeAvailable"] is False
    assert tree["status"] == "partial"
    assert len(tree["flatFreecadParts"]) >= 100


def test_phase56_device_frame_and_groups_are_explicit_drafts() -> None:
    frame = _json("frontend/public/assets/digital-twin/ktr1_device_frame.json")
    groups = _json("frontend/public/assets/digital-twin/ktr1_mechanical_groups.json")
    calibration = _json("frontend/public/assets/digital-twin/ktr1_joint_calibration.json")

    assert frame["sourceCad"]["front"] == "-Y"
    assert frame["runtimeWorld"]["front"] == "+Z"
    assert frame["status"] == "draft_requires_freecad_and_physical_validation"
    assert groups["status"] == "draft_manual_validation_required"
    assert groups["counts"]["camera_assembly"] >= 1
    assert groups["counts"]["launcher_assembly"] >= 1
    assert groups["counts"]["pitch_cradle"] < 40
    assert groups["counts"]["candidate_review_required"] > 0
    assert calibration["status"] == "draft_requires_manual_pick_or_physical_measurement"
    assert calibration["joints"]["yaw"]["physicalMotor"] == "X/azimuth step motor"
    assert calibration["joints"]["pitch"]["physicalMotor"] == "Y/elevation step motor"
    assert calibration["joints"]["pitch"]["source"].startswith("candidate shaft/axis part")
    assert calibration["anchors"]["camera_origin"]["axisRuntime"] == [0, 0, 1]
    assert calibration["anchors"]["launcher_origin"]["axisRuntime"] == [0, 0, 1]


def test_phase56_runtime_loads_contracts_without_physical_command_paths() -> None:
    kinematics = _json("frontend/public/assets/digital-twin/ktr1_kinematics.json")
    coverage = _json("reports/phase56_runtime_node_group_coverage.json")
    simulation = _json("reports/phase56_kinematic_preview_simulation.json")
    assert kinematics["phase56Refinement"]["enabled"] is True
    assert len(kinematics["groups"]["pitch_group"]) < 30
    assert kinematics["pivots"]["yaw_pivot"]["source"].startswith("base/table part")
    assert kinematics["pivots"]["pitch_pivot"]["source"].startswith("candidate shaft/axis part")
    assert coverage["coverageRatio"] == 1.0
    assert coverage["keyNodeCoverage"]["kamera v3"] == "camera_group"
    assert coverage["keyNodeCoverage"]["Bileşen13"] == "launcher_group"
    assert coverage["keyNodeCoverage"]["Axel"] == "pitch_group"
    assert simulation["cameraLauncherRigid"] is True
    assert simulation["maxCameraLauncherDistanceError"] < 1e-6
    assert kinematics["coordinateSystems"]["runtimeWorld"]["front"] == "+Z"

    runtime_files = [
        Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue"),
        Path("frontend/src/utils/digitalTwinPhase56Contracts.ts"),
        Path("frontend/public/assets/digital-twin/ktr1_device_frame.json"),
        Path("frontend/public/assets/digital-twin/ktr1_mechanical_groups.json"),
        Path("frontend/public/assets/digital-twin/ktr1_joint_calibration.json"),
        Path("reports/phase56_runtime_node_group_coverage.json"),
        Path("reports/phase56_kinematic_preview_simulation.json"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in runtime_files)

    for expected in [
        "loadPhase56DeviceFrame",
        "loadPhase56MechanicalGroups",
        "loadPhase56JointCalibration",
        "PHASE56 CONTRACTS",
        "physical_command_enabled",
        "serial_tx_enabled",
        "no_physical_command_generated",
    ]:
        assert expected in combined
    for expected_front_positive_z in [
        "cam.z + 1.45 + geometry.value.target_scene_depth * 4.4",
        "cameraAnchor.z + 1.45 + geometry.value.target_scene_depth * 4.4",
        "const farZ = origin.z + far",
    ]:
        assert expected_front_positive_z in combined
    for expected_freecad_match in [
        "freecad: new THREE.Vector3(0.05, 0.34, 1)",
        "front: new THREE.Vector3(0, 0.18, 1)",
        "freecad_camera_mechanical_gray",
        "freecad_launcher_graphite",
    ]:
        assert expected_freecad_match in combined

    pipeline_files = [
        Path("scripts/convert_ktr_step_to_glb.py"),
        Path("scripts/export_ktr_kinematic_glb_phase55.py"),
        Path("scripts/audit_ktr_cad_phase55.py"),
    ]
    pipeline_text = "\n".join(path.read_text(encoding="utf-8") for path in pipeline_files)
    for expected_phase56_pipeline_frame in [
        "Runtime front is +Z",
        "\"camera_origin\": {\"position\": camera_origin, \"direction\": [0, 0, 1]",
        "\"launcher_origin\": {\"position\": launcher_origin, \"direction\": [0, 0, 1]",
        "camera_origin[2] + 1.0",
        "camera_center[2] + 1.0",
        "\"bileşen13\" in s or \"bilesen13\" in s",
    ]:
        assert expected_phase56_pipeline_frame in pipeline_text
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


def test_phase56_reports_exist() -> None:
    for path in [
        "reports/phase56_root_cause_diagnosis_and_rebuild_plan.md",
        "reports/phase56_step_semantic_audit.md",
        "reports/phase56_step_semantic_audit.json",
        "reports/phase56_step_assembly_tree.json",
        "reports/phase56_part_table.md",
        "reports/phase56_mechanical_grouping.md",
        "reports/phase56_joint_anchor_calibration.md",
        "reports/phase56_incremental_grouping_check.md",
        "reports/phase56_runtime_node_group_coverage.md",
        "reports/phase56_runtime_node_group_coverage.json",
        "reports/phase56_kinematic_preview_simulation.md",
        "reports/phase56_kinematic_preview_simulation.json",
        "reports/phase56_runtime_front_axis_fix.md",
    ]:
        assert Path(path).exists()
