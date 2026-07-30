from copy import deepcopy

from fastapi.testclient import TestClient


def test_pico_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/pico/status")

    assert response.status_code == 200
    body = response.json()
    assert body["mock_mode"] is True
    assert body["telemetry"]["connection_status"] == "DISCONNECTED"
    assert body["telemetry"]["driver_enabled"] is False
    assert "hardware_disabled" in body["blocking_reasons"]


def test_mock_port_list_endpoint(client: TestClient) -> None:
    response = client.get("/api/pico/ports")

    assert response.status_code == 200
    ports = response.json()
    assert ports[0]["device"] == "MOCK_PICO"
    assert ports[0]["mock"] is True


def test_connect_disconnect_mock(client: TestClient) -> None:
    connect = client.post("/api/pico/connect", json={"port": "MOCK_PICO", "baudrate": 115200})

    assert connect.status_code == 200
    assert connect.json()["connection_status"] == "MOCK_CONNECTED"

    status = client.get("/api/pico/status").json()
    assert status["telemetry"]["connection_status"] == "MOCK_CONNECTED"
    assert status["telemetry"]["port"] == "MOCK_PICO"

    disconnect = client.post("/api/pico/disconnect")
    assert disconnect.status_code == 200
    assert disconnect.json()["connection_status"] == "DISCONNECTED"


def test_pin_validation_positive(client: TestClient) -> None:
    profile = client.get("/api/pico/pins").json()

    response = client.post("/api/pico/pins/validate", json=profile)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["can_apply"] is True
    assert body["issues"][0]["code"] == "PIN_PROFILE_VALID"


def test_duplicate_pin_assignment_negative(client: TestClient) -> None:
    profile = client.get("/api/pico/pins").json()
    duplicate = deepcopy(profile)
    duplicate["pins"][0]["function"] = "PAN_STEP"
    duplicate["pins"][0]["direction"] = "OUT"
    duplicate["pins"][0]["mode"] = "GPIO"

    response = client.post("/api/pico/pins/validate", json=duplicate)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(issue["code"] == "DUPLICATE_FUNCTION" for issue in body["issues"])


def test_missing_estop_in_critical_error(client: TestClient) -> None:
    profile = client.get("/api/pico/pins").json()
    for pin in profile["pins"]:
        if pin["function"] == "ESTOP_IN":
            pin["function"] = "UNUSED"
            pin["direction"] = "UNUSED"
            pin["mode"] = "UNUSED"

    response = client.post("/api/pico/pins/validate", json=profile)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(issue["code"] == "MISSING_ESTOP" and issue["level"] == "CRITICAL" for issue in body["issues"])


def test_pwm_capability_negative(client: TestClient) -> None:
    profile = client.get("/api/pico/pins").json()
    for pin in profile["pins"]:
        if pin["function"] == "TRIGGER_SERVO_PWM":
            pin["pwm_capable"] = False
            break

    response = client.post("/api/pico/pins/validate", json=profile)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(issue["code"] == "PWM_CAPABILITY_MISMATCH" for issue in body["issues"])


def test_pin_update_rejected_when_armed(client: TestClient) -> None:
    client.app.state.runtime.force_armed = True
    profile = client.get("/api/pico/pins").json()

    response = client.put("/api/pico/pins", json=profile)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["can_apply"] is False
    assert any(issue["code"] == "SYSTEM_NOT_DISARMED" for issue in detail["issues"])
