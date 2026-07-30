import json
from pathlib import Path

from fastapi.testclient import TestClient


def _generate_ktr(client: TestClient) -> dict:
    response = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase 11 test"})
    assert response.status_code == 200
    return response.json()


def test_report_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/reports/status")
    assert response.status_code == 200
    body = response.json()
    assert body["no_physical_command_generated"] is True
    assert body["root_dir"]


def test_generate_ktr_summary(client: TestClient) -> None:
    body = _generate_ktr(client)
    assert body["kind"] == "ktr_summary"
    assert body["status"] == "completed"
    assert body["no_physical_command_generated"] is True
    output_dir = Path(body["output_dir"])
    assert (output_dir / "ktr_summary.md").exists()
    assert "NO_FIRE" in (output_dir / "ktr_summary.md").read_text(encoding="utf-8")


def test_generate_demo_pack(client: TestClient) -> None:
    response = client.post("/api/reports/generate-demo-pack", json={})
    assert response.status_code == 200
    body = response.json()
    output_dir = Path(body["output_dir"])
    assert body["kind"] == "demo_pack"
    assert (output_dir / "demo_runbook.md").exists()
    assert not (output_dir / "ktr_summary.md").exists()


def test_generate_readiness_pack(client: TestClient) -> None:
    response = client.post("/api/reports/generate-readiness-pack", json={})
    assert response.status_code == 200
    body = response.json()
    output_dir = Path(body["output_dir"])
    assert body["kind"] == "readiness_pack"
    assert (output_dir / "self_test_summary.md").exists()
    assert (output_dir / "safety_summary.md").exists()
    assert not (output_dir / "dataset_summary.md").exists()


def test_export_metadata_json(client: TestClient) -> None:
    body = _generate_ktr(client)
    metadata_path = Path(body["output_dir"]) / "export_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["export_id"] == body["export_id"]
    assert metadata["no_physical_command_generated"] is True


def test_interface_inventory_contains_core_interfaces(client: TestClient) -> None:
    body = _generate_ktr(client)
    inventory = (Path(body["output_dir"]) / "interface_inventory.md").read_text(encoding="utf-8")
    assert "Frontend ↔ Backend REST" in inventory
    assert "Backend ↔ Pico Serial JSON-line" in inventory
    assert "Self-test ↔ all services" in inventory
    assert "Reports/KTR export ↔ backend services" in inventory


def test_safety_summary_includes_safe_defaults(client: TestClient) -> None:
    body = _generate_ktr(client)
    safety = (Path(body["output_dir"]) / "safety_summary.md").read_text(encoding="utf-8")
    assert "NO_FIRE" in safety
    assert "dry_run=true" in safety
    assert "hardware_enabled=false" in safety


def test_self_test_summary_inclusion(client: TestClient) -> None:
    client.post("/api/self-test/run", json={})
    body = _generate_ktr(client)
    self_test = (Path(body["output_dir"]) / "self_test_summary.md").read_text(encoding="utf-8")
    assert "Readiness level" in self_test
    assert "No physical command generated: True" in self_test


def test_model_registry_summary_path(client: TestClient) -> None:
    body = _generate_ktr(client)
    model_summary = (Path(body["output_dir"]) / "model_registry_summary.md").read_text(encoding="utf-8")
    assert "Model Registry Summary" in model_summary
    assert "Vision team provides production models" in model_summary


def test_dataset_summary_generation(client: TestClient) -> None:
    body = _generate_ktr(client)
    dataset_summary = (Path(body["output_dir"]) / "dataset_summary.md").read_text(encoding="utf-8")
    assert "Dataset Summary" in dataset_summary
    assert "Session count" in dataset_summary


def test_report_export_never_sends_physical_command(client: TestClient) -> None:
    before = client.get("/api/serial/logs").json()
    body = _generate_ktr(client)
    after = client.get("/api/serial/logs").json()
    assert body["no_physical_command_generated"] is True
    assert body["summary"]["hardware_enabled"] is False
    assert len(after) == len(before)


def test_websocket_report_event_smoke(client: TestClient) -> None:
    _generate_ktr(client)
    with client.websocket_connect("/ws") as websocket:
        seen = {websocket.receive_json()["type"] for _ in range(60)}
    assert "report.export_completed" in seen
