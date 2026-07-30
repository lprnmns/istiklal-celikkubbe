from fastapi.testclient import TestClient


def test_websocket_mock_telemetry_smoke(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        messages = [websocket.receive_json() for _ in range(24)]

    event_types = {message["type"] for message in messages}
    assert "system.state" in event_types
    assert "pico.telemetry" in event_types
    assert "pico.connection" in event_types
    assert "pico.pin_validation" in event_types
    assert "serial.status" in event_types
    assert "vision.frame_stats" in event_types
    assert "vision.status" in event_types
    assert "vision.frame" in event_types
    assert "vision.detections" in event_types
    assert "camera.status" in event_types
    assert "decision.gates" in event_types
    for message in messages:
        assert message["seq"] >= 1
        assert isinstance(message["payload"], dict)


def test_websocket_serial_event_smoke(client: TestClient) -> None:
    client.post(
        "/api/serial/send-json",
        json={"message": {"type": "disarm", "seq": 22, "reason": "operator_request"}},
    )

    with client.websocket_connect("/ws") as websocket:
        messages = [websocket.receive_json() for _ in range(24)]

    event_types = {message["type"] for message in messages}
    assert "serial.status" in event_types
    assert "serial.tx" in event_types
