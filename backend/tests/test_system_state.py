from fastapi.testclient import TestClient


def test_system_state_endpoint(client: TestClient) -> None:
    response = client.get("/api/system/state")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "DISARMED"
    assert body["fire_policy"] == "NO_FIRE"
    assert body["dry_run"] is True
    assert body["hardware_enabled"] is False
    assert body["ready"] is False
    assert "blocking_reasons" in body


def test_default_state_is_disarmed(client: TestClient) -> None:
    body = client.get("/api/system/state").json()

    assert body["mode"] == "DISARMED"
    assert body["armed"] is False
    assert "system_disarmed" in body["blocking_reasons"]

