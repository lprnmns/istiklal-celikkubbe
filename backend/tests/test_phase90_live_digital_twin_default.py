from pathlib import Path


def test_operator_digital_twin_keeps_calibrated_asset_with_curated_groups() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "? initialAssetParam : 'phase55-raw'" in panel
    assert "const group = rawManualGroupForNode(child.name)" in panel
    assert "applyRawManualKinematicSceneGraph(root)" in panel
    assert "yawPivotObject.rotation.z = THREE.MathUtils.degToRad(yawPreviewDeg.value)" in panel
    assert "yaw: { x: 0, y: 0, z: 1 }" in panel
    assert "pitchPivotObject.rotation.x" in panel
    assert "applyTelemetryPoseIfAvailable()\n    applyKinematicPreviewPose()" in panel
    assert "explicitPosePreview ? 'keyboard_preview'" in panel
    assert "performance.now() < keyboardPreviewUntil" in panel
    assert "keyboardPreviewUntil = performance.now() + 1500" in panel
    assert "MODEL ${yawPreviewDeg.value.toFixed(1)}° / ${pitchPreviewDeg.value.toFixed(1)}°" in panel
    assert "const renderedPitchDeg = computed(() => -pitchPreviewDeg.value)" in panel
    assert "pitchPivotObject.rotation.x = THREE.MathUtils.degToRad(renderedPitchDeg.value)" in panel
    for static_part in ("yan gövde1", "yan gövde 3", "bileşen18", "bileşen19", "bileşen20"):
        assert static_part in panel
    for pitch_part in ("solid", "axel", "wire", "grand fulffy"):
        assert pitch_part in panel
    assert "toLowerCase().replace(/_/g, ' ')" in panel
    assert "'compound001', 'compound002', 'compound009'" in panel
    assert "'compound005'" not in panel


def test_curated_groups_keep_only_base_parts_static() -> None:
    import json

    payload = json.loads(Path("frontend/public/assets/digital-twin/ktr1_kinematics.json").read_text(encoding="utf-8"))
    static = {name.casefold() for name in payload["groups"]["static_root"]}
    yaw = {name.casefold() for name in payload["groups"]["yaw_group"]}
    pitch = {name.casefold() for name in payload["groups"]["pitch_group"]}

    assert static == {"alt gövde", "tabla", "yan gövde1", "yan gövde 3"}
    assert {"bileşen18", "bileşen19", "bileşen20"} <= yaw
    assert {"kamera v3", "bileşen13"} <= pitch
