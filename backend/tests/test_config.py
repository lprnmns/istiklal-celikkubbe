from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.services.config_service import ConfigService
from tests.conftest import write_config


def test_config_validation_positive(tmp_path: Path, config_data: dict[str, Any]) -> None:
    path = write_config(tmp_path, config_data)

    config = ConfigService(path).load()

    assert config.system.mode == "DISARMED"
    assert config.system.default_fire_policy == "NO_FIRE"
    assert config.system.dry_run is True
    assert config.system.hardware_enabled is False
    assert config.hardware.hardware_discovery_enabled is False
    assert config.hardware.physical_command_enabled is False
    assert config.hardware.allow_real_serial_readonly is False
    assert config.camera.camera_mode == "mock"
    assert config.camera.stream_enabled is True
    assert config.vision.vision_mode == "mock"
    assert config.vision.model_loading_required is False
    assert config.vision.overlay_coordinate_format == "pixel"
    assert config.serial.protocol_mode == "json-line"
    assert config.serial.transport_mode == "mock"
    assert config.serial.real_serial_enabled is False
    assert config.motion.dry_run is True
    assert config.motion.real_motion_enabled is False
    assert config.motion.soft_limits_enabled is True
    assert config.calibration.camera_height_cm == 60.0
    assert config.color.balloon_mask_enabled is True
    assert config.pins.profile_name == "pico2_placeholder_not_final"


def test_config_validation_rejects_unsafe_defaults(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["system"]["dry_run"] = False
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="dry_run must be true"):
        ConfigService(path).load()


def test_config_validation_rejects_pin_conflict(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["pins"]["assignments"]["tilt_step"] = "GP2"
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="duplicates"):
        ConfigService(path).load()


def test_config_validation_rejects_invalid_confidence(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["vision"]["body_conf"] = 1.5
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError):
        ConfigService(path).load()


def test_config_validation_rejects_real_serial_enabled(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["serial"]["real_serial_enabled"] = True
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="real_serial_enabled must be false"):
        ConfigService(path).load()


def test_config_validation_rejects_physical_command_enabled(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["hardware"]["physical_command_enabled"] = True
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="physical_command_enabled must be false"):
        ConfigService(path).load()


def test_config_validation_real_readonly_requires_allow_flag(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["serial"]["transport_mode"] = "real_readonly"
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="allow_real_serial_readonly"):
        ConfigService(path).load()


def test_config_validation_rejects_physical_motion_and_fire(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["hardware"]["allow_physical_motion"] = True
    config_data["hardware"]["allow_physical_fire"] = True
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="allow_physical_motion"):
        ConfigService(path).load()


def test_config_validation_rejects_invalid_camera_mode(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["camera"]["camera_mode"] = "unsafe"
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="camera_mode"):
        ConfigService(path).load()


def test_config_validation_rejects_real_motion_enabled(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["motion"]["real_motion_enabled"] = True
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="real_motion_enabled must be false"):
        ConfigService(path).load()


def test_config_validation_rejects_invalid_motion_limits(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["motion"]["pan_min_deg"] = 60.0
    config_data["motion"]["pan_max_deg"] = 60.0
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="pan_min_deg"):
        ConfigService(path).load()


def test_config_validation_rejects_invalid_camera_height(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["calibration"]["camera_height_cm"] = -1
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError):
        ConfigService(path).load()


def test_config_validation_rejects_invalid_hsv_range(
    tmp_path: Path,
    config_data: dict[str, Any],
) -> None:
    config_data["color"]["enemy_hsv_ranges"][0]["h_min"] = 20
    config_data["color"]["enemy_hsv_ranges"][0]["h_max"] = 10
    path = write_config(tmp_path, config_data)

    with pytest.raises(ValidationError, match="h_min"):
        ConfigService(path).load()
