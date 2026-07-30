import json
from pathlib import Path

from app.services.digital_twin_projection import project_bbox_to_scene


def test_supplied_competition_targets_are_optimized_browser_assets() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "frontend/public/assets/targets/target_asset_manifest.json").read_text(encoding="utf-8"))
    targets = {item["class_name"]: item for item in manifest["targets"]}

    assert set(targets) == {"ballistic_missile", "helicopter", "f16", "mini_micro_uav"}
    assert targets["ballistic_missile"]["dimensions_mm"][2] == 500.0
    assert targets["helicopter"]["reference_span_mm"] == 583.0
    assert targets["f16"]["reference_span_mm"] == 500.0
    assert targets["mini_micro_uav"]["reference_span_mm"] == 375.0
    for target in targets.values():
        output = root / "frontend/public" / target["asset_path"].lstrip("/")
        assert output.exists()
        assert output.read_bytes()[:4] == b"glTF"
        assert target["lod_triangle_count"] < target["raw_triangle_count"]
        assert target["no_physical_command_generated"] is True


def test_class_size_projection_uses_14cm_balloon_and_distinguishes_aircraft() -> None:
    bbox = {"x": 290, "y": 140, "w": 60, "h": 60}
    balloon = project_bbox_to_scene(bbox=bbox, frame_width=640, frame_height=360, class_name="balloon", confidence=0.9)
    f16 = project_bbox_to_scene(bbox=bbox, frame_width=640, frame_height=360, class_name="f16", confidence=0.9)

    assert balloon.reference_size_m == 0.14
    assert balloon.range_source == "class_bbox_pinhole_estimate"
    assert balloon.estimated_range_m is not None
    assert f16.reference_size_m == 0.5
    assert f16.estimated_range_m is not None
    assert f16.estimated_range_m > balloon.estimated_range_m
    assert f16.range_uncertainty_m is not None and balloon.range_uncertainty_m is not None
    assert f16.range_uncertainty_m > balloon.range_uncertainty_m


def test_balloon_projection_accepts_16cm_hil_reference_without_changing_competition_default() -> None:
    bbox = {"x": 220, "y": 120, "w": 160, "h": 150}
    hil = project_bbox_to_scene(
        bbox=bbox,
        frame_width=640,
        frame_height=480,
        class_name="balloon",
        confidence=0.94,
        camera_fov_horizontal_deg=78.0,
        camera_fov_vertical_deg=48.0,
        known_target_size_mm=160.0,
    )
    competition = project_bbox_to_scene(
        bbox=bbox,
        frame_width=640,
        frame_height=480,
        class_name="balloon",
        confidence=0.94,
        camera_fov_horizontal_deg=78.0,
        camera_fov_vertical_deg=48.0,
    )

    assert hil.reference_size_m == 0.16
    assert competition.reference_size_m == 0.14
    assert hil.estimated_range_m > competition.estimated_range_m
    assert hil.range_source == "class_bbox_pinhole_estimate"


def test_16cm_balloon_bbox_calibrates_to_about_85cm_with_usb_camera_fov() -> None:
    estimate = project_bbox_to_scene(
        bbox={"x": 410, "y": 175, "w": 100, "h": 126},
        frame_width=640,
        frame_height=480,
        class_name="balloon",
        confidence=0.95,
        camera_fov_horizontal_deg=62.0,
        camera_fov_vertical_deg=40.0,
        known_target_size_mm=160.0,
    )

    assert estimate.reference_size_m == 0.16
    assert estimate.estimated_range_m is not None
    assert 0.78 <= estimate.estimated_range_m <= 0.92


def test_digital_twin_frontend_accepts_body_detections_and_loads_visuals_only() -> None:
    root = Path(__file__).resolve().parents[2]
    panel = (root / "frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")
    cockpit = (root / "frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    semantics = (root / "frontend/src/digitalTwin/targetSemantics.ts").read_text(encoding="utf-8")

    assert "visionBodies?: BodyDetection[]" in panel
    assert "projectionFromBodyDetection" in panel
    assert "addBodyTarget3d" in panel
    assert "ensureTargetAsset" in panel
    assert "transformDirectionByPreview" in panel
    assert "BALLOON_DIAMETER_M = 0.14" in semantics
    assert ":vision-bodies=\"latestFrame?.body_detections ?? []\"" in cockpit
    for forbidden in ["send_fire_command(", "set_servo_position(", "gpio_write(", "pwm_write(", "step_pulse("]:
        assert forbidden not in panel
