from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.schemas.self_test import SelfTestStep


def test_self_test_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/self-test/status")
    assert response.status_code == 200
    assert response.json()["running"] is False


def test_self_test_run_creates_run_id(client: TestClient) -> None:
    response = client.post("/api/self-test/run", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"].startswith("selftest-")
    assert body["no_physical_command_generated"] is True


def test_self_test_step_model_validation() -> None:
    step = SelfTestStep(step_id="backend_health", name="Backend health", category="backend")
    assert step.status == "pending"
    with pytest.raises(ValidationError):
        SelfTestStep(step_id="bad", name="Bad", category="unsafe")  # type: ignore[arg-type]


def test_self_test_completes_with_mock_services(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    assert body["status"] in {"warning", "passed"}
    assert body["readiness_level"] in {"demo_ready", "hardware_blocked", "field_test_ready"}
    assert body["summary"]["critical_failures"] == 0
    assert len(body["steps"]) >= 40


def test_self_test_critical_safety_invariant(client: TestClient) -> None:
    client.app.state.runtime.config.system.hardware_enabled = True
    body = client.post("/api/self-test/run", json={}).json()
    assert body["status"] == "failed"
    assert body["overall_ready"] is False
    assert any(step["step_id"] == "default_safety_state" and step["status"] == "failed" for step in body["steps"])


def test_fire_request_rejection_step(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    step = next(step for step in body["steps"] if step["step_id"] == "fire_rejected")
    assert step["status"] == "passed"
    assert step["details"]["accepted"] is False


def test_risky_serial_command_rejected_step(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    step = next(step for step in body["steps"] if step["step_id"] == "risky_tx_rejected")
    assert step["status"] == "passed"
    assert step["details"]["accepted"] is False


def test_motion_dry_run_no_physical_command(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    step = next(step for step in body["steps"] if step["step_id"] == "jog_dry_run")
    assert step["status"] == "passed"
    assert step["details"]["no_physical_command_generated"] is True


def test_model_test_adapter_no_physical_command(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    step = next(step for step in body["steps"] if step["step_id"] == "model_no_physical")
    assert step["status"] == "passed"
    assert step["details"]["no_physical_command_generated"] is True


def test_report_json_and_md_created(client: TestClient) -> None:
    body = client.post("/api/self-test/run", json={}).json()
    report_path = Path(body["report_path"])
    assert report_path.exists()
    assert report_path.with_suffix(".json").exists()
    assert "Self-test readiness does not enable physical fire" in report_path.read_text(encoding="utf-8")


def test_websocket_self_test_event_smoke(client: TestClient) -> None:
    client.post("/api/self-test/run", json={})
    with client.websocket_connect("/ws") as websocket:
        seen = {websocket.receive_json()["type"] for _ in range(40)}
    assert "self_test.completed" in seen or "self_test.warning" in seen


def test_no_physical_command_generated_invariant(client: TestClient) -> None:
    before = client.get("/api/serial/logs").json()
    body = client.post("/api/self-test/run", json={}).json()
    after = client.get("/api/serial/logs").json()
    assert body["no_physical_command_generated"] is True
    assert all("fire_request" not in str(entry.get("message", {})) or entry["kind"] == "error" for entry in after)
    assert len(after) >= len(before)
