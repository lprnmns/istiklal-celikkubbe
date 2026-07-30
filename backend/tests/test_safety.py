from fastapi.testclient import TestClient


def test_default_decision_is_no_fire(client: TestClient) -> None:
    response = client.get("/api/safety/gates")

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "NO_FIRE"
    assert body["gates"]["armed"] is False
    assert body["gates"]["dry_run"] is True
    assert body["gates"]["hardware_enabled"] is False
    assert "system_disarmed" in body["blocking_reasons"]


def test_fire_request_rejected_by_default(client: TestClient) -> None:
    response = client.post(
        "/api/safety/fire-request",
        json={"track_id": 7, "operator_confirmed": True},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["accepted"] is False
    assert body["decision_state"] in {"NO_TARGET", "NO_FIRE", "LOCKED", "WAIT"}
    assert "system_disarmed" in body["blocking_reasons"]
    assert "hardware_disabled" in body["blocking_reasons"]


def test_motor_jog_rejected_by_default(client: TestClient) -> None:
    response = client.post(
        "/api/motor/jog",
        json={"axis": "pan", "degrees": 1.0, "operator_confirmed": True},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["accepted"] is False
    assert body["command"] == "MOTOR_JOG"
    assert body["decision"] == "NO_FIRE"
    assert "hardware_disabled" in body["blocking_reasons"]
