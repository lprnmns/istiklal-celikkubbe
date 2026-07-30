import json
from pathlib import Path


def test_landing_exposes_only_tracking_test_and_live_fire_authorities() -> None:
    landing = Path("frontend/src/views/LandingView.vue").read_text(encoding="utf-8")

    assert "type StartupMode = 'TRACKING_TEST' | 'LIVE_HARDWARE'" in landing
    assert "selectCommandProfile('LIVE_TEST', actuatorArm)" in landing
    assert "preflight.physical_motion_enabled" in landing
    assert "preflight.physical_fire_enabled" in landing
    assert "Tetik kapalı" in landing
    assert "autotrack=1" in landing


def test_cockpit_automatically_starts_tracking_after_authorized_startup() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "const autoTrackingRequested = initialParams.get('autotrack') === '1'" in cockpit
    assert "await motion.startTracking()" in cockpit
    assert "Otomatik takip hazır" in cockpit


def test_windows_hil_profile_is_packaged_as_default() -> None:
    preference = json.loads(Path("config/default_device_profile.json").read_text(encoding="utf-8"))
    profile = json.loads(Path("data/device_profiles/windows-taret-hil.json").read_text(encoding="utf-8"))

    assert preference["profile_id"] == "windows-taret-hil"
    assert profile["selected_camera_id"] == "camera_index_2"
    assert profile["selected_pico_port"] == "COM8"
    assert profile["selected_pico_baudrate"] == 460800
    assert profile["command_profile"] == "LIVE_TEST"
    assert profile["vision_config"]["balloon_conf_threshold"] == 0.15


def test_windows_one_click_uses_persistent_task_when_available() -> None:
    script = Path("release/one_click/windows/ISTIKLAL_TEK_TIK.ps1").read_text(encoding="utf-8")

    assert "$taskName = 'ISTIKLAL_UI_8000'" in script
    assert "Start-ScheduledTask" in script
    assert "Test-Health" in script
    assert "launcher.py" in script
