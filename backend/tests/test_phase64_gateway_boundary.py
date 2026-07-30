from pathlib import Path


BACKEND_APP = Path(__file__).resolve().parents[1] / "app"


def test_no_api_or_tracking_motion_write_bypasses_command_gateway() -> None:
    """Physical motion callers must not use the legacy SerialService API."""
    forbidden = ("send_speed_command(", "send_motor_command(", "send_fire_command(")
    permitted = {BACKEND_APP / "services" / "serial_service.py"}
    for path in [*BACKEND_APP.glob("api/*.py"), BACKEND_APP / "services" / "tracking_loop.py"]:
        if path in permitted:
            continue
        source = path.read_text(encoding="utf-8")
        hits = [token for token in forbidden if token in source]
        assert not hits, f"Gateway bypass in {path.relative_to(BACKEND_APP)}: {hits}"


def test_live_jog_uses_gateway_contract(client) -> None:
    runtime = client.app.state.runtime
    result = client.post("/api/hardware/test-jog", json={"speed_x": 100, "speed_y": -100, "duration_ms": 1})

    # No visible live profile/preflight means only this command is rejected.
    # Gateway may issue its safe-stop sequence, but it must not issue SPD.
    assert result.status_code == 200
    assert result.json()["accepted"] is False
    assert all(entry.raw != "SPD,100,-100" for entry in runtime.serial.logs)
