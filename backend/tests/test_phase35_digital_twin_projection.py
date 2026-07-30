from pathlib import Path

from fastapi.testclient import TestClient

from app.services.digital_twin_projection import project_bbox_to_scene


def test_bbox_projection_maps_right_and_left_side() -> None:
    right = project_bbox_to_scene(
        bbox={"x": 450, "y": 140, "w": 80, "h": 80},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.9,
    )
    left = project_bbox_to_scene(
        bbox={"x": 70, "y": 140, "w": 80, "h": 80},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.9,
    )

    assert right.normalized_center_x > 0.65
    assert right.normalized_screen_x > 0
    assert right.scene_position_m.x > 0
    assert left.normalized_center_x < 0.35
    assert left.normalized_screen_x < 0
    assert left.scene_position_m.x < 0
    assert right.mapping_source == "bbox_projection_estimate"
    assert right.no_physical_command_generated is True


def test_larger_bbox_maps_closer_than_smaller_bbox() -> None:
    small = project_bbox_to_scene(
        bbox={"x": 300, "y": 160, "w": 30, "h": 30},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.8,
    )
    large = project_bbox_to_scene(
        bbox={"x": 260, "y": 110, "w": 150, "h": 150},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.8,
    )

    assert large.bbox_area_ratio > small.bbox_area_ratio
    assert large.relative_depth < small.relative_depth
    assert large.scene_position_m.z > small.scene_position_m.z
    assert large.depth_source == "class_bbox_pinhole_estimate"
    assert large.reference_size_m == 0.14
    assert large.estimated_range_m is not None
    assert large.range_uncertainty_m is not None
    assert large.projection_is_calibrated is False


def test_projection_maps_above_and_below_optical_axis() -> None:
    above = project_bbox_to_scene(
        bbox={"x": 300, "y": 40, "w": 70, "h": 70},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.7,
    )
    below = project_bbox_to_scene(
        bbox={"x": 300, "y": 250, "w": 70, "h": 70},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.7,
    )

    assert above.normalized_screen_y > 0
    assert below.normalized_screen_y < 0
    assert above.scene_position_m.y > below.scene_position_m.y


def test_projection_uses_configured_mechanical_offset_for_visualization_only() -> None:
    projected = project_bbox_to_scene(
        bbox={"normalized_center_x": 0.5, "normalized_center_y": 0.5, "normalized_width": 0.1, "normalized_height": 0.1},
        frame_width=640,
        frame_height=360,
        class_name="balloon",
        confidence=0.7,
        camera_to_launcher_offset_z_mm=30.0,
        camera_to_launcher_offset_y_mm=12.0,
    )

    assert projected.camera_to_launcher_offset_z_mm == 30.0
    assert projected.camera_to_launcher_offset_y_mm == 12.0
    assert projected.scene_position_m.y > 0
    assert projected.scene_position_m.x > 0
    assert projected.no_physical_command_generated is True


def test_digital_twin_state_contract_exposes_projection_fields(client: TestClient) -> None:
    response = client.get("/api/digital-twin/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["camera_fov_horizontal_deg"] > 1
    assert payload["camera_fov_vertical_deg"] > 1
    assert payload["camera_to_launcher_offset_z_mm"] == 30.0
    assert payload["camera_to_launcher_offset_y_mm"] == 0.0
    assert payload["projection_is_calibrated"] is False
    assert payload["depth_source"] == "class_bbox_pinhole_estimate"
    assert payload["no_physical_command_generated"] is True
    assert payload["target_projection_estimates"]
    projection = payload["target_projection_estimates"][0]
    assert projection["mapping_source"] == "bbox_projection_estimate"
    assert projection["depth_source"] == "class_bbox_pinhole_estimate"
    assert projection["reference_size_m"] == 0.14
    assert projection["estimated_range_m"] is not None
    assert projection["projection_is_calibrated"] is False
    assert projection["no_physical_command_generated"] is True


def test_phase35_visual_layer_does_not_add_physical_command_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "backend" / "app" / "services" / "digital_twin_projection.py",
        root / "backend" / "app" / "services" / "digital_twin_service.py",
        root / "backend" / "app" / "api" / "digital_twin.py",
        root / "frontend" / "src" / "api" / "digitalTwin.ts",
        root / "frontend" / "src" / "components" / "digital-twin" / "DigitalTwinPanel.vue",
        root / "frontend" / "src" / "stores" / "digitalTwinStore.ts",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = [
        "/api/motion/jog",
        "/api/motion/go-to",
        "/api/motion/home",
        "/api/decision/fire",
        "/api/serial/send-json",
        "send_json(",
        "send_speed_command(",
        "send_fire_command(",
        "set_servo_position(",
        "gpio_write(",
        "pwm_write(",
        "step_pulse(",
        "STEP/DIR command",
        "hardware_enabled = True",
        "physical_command_enabled = True",
    ]

    for item in forbidden:
        assert item not in combined
    assert "no_physical_command_generated" in combined
