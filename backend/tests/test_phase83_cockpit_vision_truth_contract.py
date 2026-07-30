from pathlib import Path


def test_cockpit_distinguishes_running_detection_from_competition_model_readiness() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "productionVisionReady" in cockpit
    assert "runtime.visionStatus.production_yolo_loaded" in cockpit
    assert "runtime.visionStatus.advisory_only" in cockpit
    assert "PROD YOLO AKTİF" in cockpit
    assert "TEST ADAPTÖRÜ AKTİF" in cockpit
    assert "LEGACY YOLO · YARIŞMA DIŞI" in cockpit
    assert "BALON ADAYI" in cockpit
    assert "MODEL ${yoloStatusLabel.value}" in cockpit


def test_camera_panel_uses_parent_truth_label_and_marks_unverified_detections_as_candidates() -> None:
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "perceptionStatusLabel?: string" in panel
    assert "props.perceptionStatusLabel ?? fallbackPerceptionStatusLabel.value" in panel
    assert "targetLabelPrefix?: string" in panel
    assert "props.targetLabelPrefix ?? 'BALON'" in panel
    assert "Vision frame processed" in panel
    assert "<span>DETECTOR</span>" in panel
    assert "YOLO ON — detection active" not in panel
