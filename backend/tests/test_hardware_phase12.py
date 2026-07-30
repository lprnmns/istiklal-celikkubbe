from fastapi.testclient import TestClient


def test_serial_port_list_endpoint(client: TestClient) -> None:
    response = client.get("/api/hardware/serial/ports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_hardware_status_endpoint_safe_defaults(client: TestClient) -> None:
    body = client.get("/api/hardware/status").json()
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    assert body["transport_mode"] == "mock"


def test_connect_readonly_rejected_when_disabled(client: TestClient) -> None:
    response = client.post("/api/hardware/connect-readonly", json={"port": "MOCK_READONLY", "baudrate": 115200})
    body = response.json()
    assert body["accepted"] is False
    assert body["reason"] == "hardware_discovery_disabled"


def test_connect_readonly_mock_controlled(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.config.hardware.hardware_discovery_enabled = True
    runtime.config.hardware.allow_real_serial_readonly = True
    response = client.post("/api/hardware/connect-readonly", json={"port": "MOCK_READONLY", "baudrate": 115200})
    body = response.json()
    assert body["accepted"] is True
    assert body["status"]["transport_mode"] == "real_readonly"
    assert body["status"]["connection_state"] == "MOCK_READONLY_CONNECTED"
    assert body["status"]["transport_source"] == "mock"
    assert body["no_physical_command_generated"] is True
    assert client.get("/api/serial/status").json()["transport_mode"] == "real_readonly"
    assert client.get("/api/serial/status").json()["connection_state"] == "MOCK_READONLY_CONNECTED"


def test_disconnect(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.config.hardware.hardware_discovery_enabled = True
    runtime.config.hardware.allow_real_serial_readonly = True
    client.post("/api/hardware/connect-readonly", json={"port": "MOCK_READONLY", "baudrate": 115200})
    body = client.post("/api/hardware/disconnect").json()
    assert body["accepted"] is True
    assert body["status"]["connection_state"] == "DISCONNECTED"


def test_telemetry_parse_valid_json(client: TestClient) -> None:
    result = client.app.state.runtime.hardware.parse_line(
        '{"type":"telemetry","seq":10,"device":"pico2","firmware_version":"dev","estop_state":false,'
        '"driver_enabled":false,"pan_position_steps":0,"tilt_position_steps":0,'
        '"limits":{"pan_left":false,"pan_right":false,"tilt_up":false,"tilt_down":false},"safe_state":true,'
        '"physical_outputs_enabled":false,"timestamp_ms":123456}'
    )
    assert result.accepted is True
    assert result.telemetry.device == "pico2"
    assert result.telemetry.connection_state == "READONLY_CONNECTED_UNVERIFIED"
    assert result.telemetry.safe_state is True
    assert result.telemetry.physical_outputs_enabled is False
    assert result.telemetry.telemetry_timestamp_ms == 123456
    assert result.telemetry.no_physical_command_generated is True


def test_telemetry_only_firmware_verifies_pico(client: TestClient) -> None:
    result = client.app.state.runtime.hardware.parse_line(
        '{"type":"telemetry","seq":1,"device":"pico2","firmware_version":"telemetry-only-0.1",'
        '"estop_state":false,"driver_enabled":false,"pan_position_steps":0,"tilt_position_steps":0,'
        '"limits":{"pan_left":false,"pan_right":false,"tilt_up":false,"tilt_down":false},'
        '"safe_state":true,"physical_outputs_enabled":false,"timestamp_ms":123456}'
    )
    assert result.accepted is True
    assert result.telemetry.connection_state == "PICO_READONLY_VERIFIED"
    assert result.telemetry.pico_verified is True
    assert result.telemetry.telemetry_firmware_detected is True
    assert result.telemetry.physical_commands_disabled is True


def test_physical_outputs_enabled_flag_is_not_ready(client: TestClient) -> None:
    result = client.app.state.runtime.hardware.parse_line(
        '{"type":"telemetry","seq":1,"device":"pico2","firmware_version":"telemetry-only-0.1",'
        '"safe_state":true,"physical_outputs_enabled":true}'
    )
    assert result.accepted is True
    assert result.telemetry.physical_outputs_enabled is True
    assert result.telemetry.pico_verified is False
    body = client.post("/api/self-test/run", json={}).json()
    failed = [step for step in body["steps"] if step["step_id"] == "pico_physical_outputs_disabled"]
    assert failed[0]["status"] == "failed"


def test_telemetry_invalid_json_warning(client: TestClient) -> None:
    result = client.app.state.runtime.hardware.parse_line("{not-json")
    assert result.accepted is False
    assert result.event_type == "hardware.error"
    assert result.telemetry.last_error.startswith("invalid_json")


def test_unknown_message_warning(client: TestClient) -> None:
    result = client.app.state.runtime.hardware.parse_line('{"type":"diagnostic","seq":1}')
    assert result.accepted is False
    assert result.event_type == "hardware.warning"
    assert result.warning == "unknown_message_type:diagnostic"


def test_risky_command_rejected_in_real_readonly(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.serial.mark_real_readonly_connected("PICO_READONLY_VERIFIED")
    response = client.post("/api/serial/send-json", json={"message": {"type": "fire_request", "seq": 9}})
    body = response.json()
    assert body["accepted"] is False
    assert body["reason"] == "physical_commands_disabled_in_phase12_readonly"


def test_hardware_risky_command_blocker_endpoint(client: TestClient) -> None:
    response = client.post("/api/hardware/block-risky-command", json={"command_type": "pwm_write"})
    body = response.json()
    assert body["accepted"] is False
    assert body["reason"] == "physical_commands_disabled_in_phase12_readonly"
    assert body["no_physical_command_generated"] is True


def test_no_physical_command_generated_invariant(client: TestClient) -> None:
    result = client.app.state.runtime.hardware.block_risky_command("step_pulse")
    assert result.accepted is False
    assert result.no_physical_command_generated is True


def test_self_test_hardware_discovery_steps(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    step_ids = {step["step_id"] for step in body["steps"]}
    assert "hardware_discovery_config" in step_ids
    assert "pico_telemetry_firmware" in step_ids
    assert "pico_verified_from_telemetry" in step_ids
    assert "pico_physical_outputs_disabled" in step_ids
    assert "telemetry_age_within_timeout" in step_ids
    assert "readonly_serial_path_active" in step_ids
    assert "phase12_risky_blocker" in step_ids
    assert body["no_physical_command_generated"] is True


def test_websocket_hardware_telemetry_event_smoke(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        seen = {websocket.receive_json()["type"] for _ in range(35)}
    assert "hardware.status" in seen
    assert "hardware.telemetry" in seen
