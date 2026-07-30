from pathlib import Path

from fastapi.testclient import TestClient

import app.services.camera_runtime_service as camera_runtime_module
from app.schemas.camera_runtime import CameraRuntimeProfile


def test_usb_camera_absent_falls_back_to_laptop_development_source(client: TestClient, monkeypatch) -> None:
    runtime = client.app.state.runtime
    runtime.camera_runtime.profile = CameraRuntimeProfile(
        source_type="usb",
        device_path="/dev/video2",
        width=1280,
        height=720,
        fps=30,
        pixel_format="MJPG",
        stream_width=1280,
        stream_height=720,
    )
    monkeypatch.setattr(camera_runtime_module.glob, "glob", lambda pattern: ["/dev/video0", "/dev/video1"] if pattern == "/dev/video*" else [])

    status = client.get("/api/camera/runtime/status").json()

    assert status["selected_device"] == "/dev/video0"
    assert status["is_laptop_camera"] is True
    assert status["is_external_usb_camera"] is False
    assert status["source_mode"] in {"REAL_LAPTOP_CAMERA_LATEST_FRAME", "REAL_LAPTOP_CAMERA_LIVE"}
    assert "using laptop camera for development" in status["hardware_presence_note"]
    assert status["no_physical_command_generated"] is True


def test_camera_unavailable_fallback_is_explicit(client: TestClient, monkeypatch) -> None:
    runtime = client.app.state.runtime
    runtime.camera_runtime.profile = CameraRuntimeProfile(source_type="usb", device_path="/dev/video2")
    monkeypatch.setattr(camera_runtime_module.glob, "glob", lambda _pattern: [])

    status = client.get("/api/camera/runtime/status").json()

    assert status["source_mode"] == "CAMERA_UNAVAILABLE"
    assert status["is_real_camera_evidence"] is False
    assert "CAMERA_UNAVAILABLE" in status["hardware_presence_note"]


def test_pico_absent_is_offline_expected_for_phase38(client: TestClient) -> None:
    status = client.get("/api/pico/protocol/status").json()

    assert status["pico_connected"] is False
    assert status["serial_tx_enabled"] is False
    assert status["physical_tx_disabled"] is True
    assert status["no_physical_command_generated"] is True


def test_digital_twin_asset_fallback_and_no_telemetry_are_explicit(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    assets = client.get("/api/digital-twin/assets").json()

    assert state["telemetry_protocol"]["pose_source"] in {"tracker_estimate", "fixture", "static_demo_pose"}
    assert state["telemetry_protocol"]["telemetry_missing"] is True
    assert "asset_fallback_reason" in assets
    assert assets["no_physical_command_generated"] is True


def test_cockpit_sources_do_not_claim_usb_good_or_add_physical_tx() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "frontend" / "src" / "views" / "CockpitView.vue",
        *sorted((root / "frontend" / "src" / "components" / "cockpit").glob("*.vue")),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)

    assert "USB CAMERA GOOD" not in combined.upper()
    assert "USB camera good" not in combined
    assert "OFFLINE_EXPECTED" in combined
    assert "no_physical_command_generated=true" in combined
    for forbidden in ["send_fire_command(", "set_servo_position(", "gpio_write(", "pwm_write(", "step_pulse(", "serial_tx_enabled: true"]:
        assert forbidden not in combined

