import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_pico_discovery_ports_are_readonly(client: TestClient) -> None:
    response = client.get("/api/pico/discovery/ports")

    assert response.status_code == 200
    body = response.json()
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    for port in body["ports"]:
        assert port["physical_command_enabled"] is False
        assert port["no_physical_command_generated"] is True


def test_pico_readonly_connect_uses_rx_only_without_serial_write(client: TestClient, monkeypatch) -> None:
    writes: list[bytes] = []

    class FakeSerial:
        def __init__(self, *args, **kwargs) -> None:
            self.in_waiting = 1
            self.closed = False

        def reset_input_buffer(self) -> None:
            return None

        def readline(self) -> bytes:
            self.in_waiting = 0
            return (
                b'{"type":"telemetry","device":"pico2","firmware_version":"telemetry-only-test",'
                b'"heartbeat":true,"estop_state":"released","driver_enabled":false,'
                b'"physical_outputs_enabled":false,"limits":{"left":false,"right":false}}\n'
            )

        def write(self, data: bytes) -> int:
            writes.append(data)
            raise AssertionError("serial write must not be called in read-only phase")

        def close(self) -> None:
            self.closed = True

    fake_serial_module = SimpleNamespace(Serial=FakeSerial)
    monkeypatch.setattr("app.services.pico_service.serial", fake_serial_module)

    response = client.post("/api/pico/read-only/connect", json={"port": "/dev/fakepico0", "baudrate": 115200, "read_only": True})

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["rx_only"] is True
    assert body["tx_disabled"] is True
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    assert writes == []

    telemetry = client.get("/api/pico/read-only/latest-telemetry").json()
    assert telemetry["heartbeat"] is True
    assert telemetry["firmware_version"] == "telemetry-only-test"
    assert telemetry["physical_command_enabled"] is False
    assert telemetry["no_physical_command_generated"] is True
    assert writes == []


def test_pico_readonly_evidence_handles_absent_device_safely(client: TestClient) -> None:
    response = client.post("/api/pico/read-only/capture-evidence")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"not_available", "recorded"}
    assert body["advisory_only"] is True
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True

    latest = client.get("/api/pico/read-only/latest-evidence").json()
    assert latest["evidence_id"] == body["evidence_id"]


def test_pico_readonly_exports_in_data_lab_and_reports(client: TestClient) -> None:
    client.get("/api/pico/discovery/ports")
    client.post("/api/pico/read-only/capture-evidence")

    lab = client.post("/api/data-lab/export")
    assert lab.status_code == 200
    lab_files = {Path(path).name: Path(path) for path in lab.json()["files"]}
    assert {
        "pico_readonly_status.json",
        "pico_readonly_latest_telemetry.json",
        "pico_readonly_evidence_summary.md",
        "pico_readonly_port_inventory.json",
        "pico_readonly_safety_boundary.md",
    } <= set(lab_files)
    status = json.loads(lab_files["pico_readonly_status.json"].read_text(encoding="utf-8"))
    assert status["physical_command_enabled"] is False
    assert status["no_physical_command_generated"] is True
    assert "no_physical_command_generated=true" in lab_files["pico_readonly_safety_boundary.md"].read_text(encoding="utf-8")

    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase28 pico readonly"})
    assert export.status_code == 200
    report_files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert {
        "pico_readonly_status.json",
        "pico_readonly_port_inventory.json",
        "pico_readonly_evidence_summary.md",
        "pico_readonly_safety_boundary.md",
    } <= set(report_files)
    ktr = report_files["ktr_4_3_interfaces.md"].read_text(encoding="utf-8")
    assert "Pico Read-Only Hardware Discovery Interface" in ktr
    assert "no_physical_command_generated=true" in ktr


def test_pico_readonly_logs_use_canonical_safety_wording(client: TestClient) -> None:
    client.get("/api/pico/discovery/ports")
    client.get("/api/pico/read-only/status")
    client.post("/api/pico/read-only/capture-evidence")

    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "pico.readonly_ports_discovered" in text
    assert "pico.readonly_status_checked" in text
    assert "pico.readonly_evidence_recorded" in text
    assert "no_physical_command_generated=true" in text
    for line in text.splitlines():
        if "pico.readonly_" in line:
            sanitized = line.replace("no_physical_command_generated=true", "")
            assert "physical command generated" not in sanitized


def test_phase28_safety_invariant_and_forbidden_runtime_paths(client: TestClient) -> None:
    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False

    status = client.get("/api/pico/read-only/status").json()
    runtime_text = json.dumps(status, ensure_ascii=False).upper()
    for token in [
        "MOTOR JOG",
        "STEP PULSE",
        "DIR PIN CHANGE",
        "PWM/GPIO OUTPUT",
        "TMC_CURRENT WRITE",
        "SERIAL TX/WRITE",
        "PICO COMMAND",
        "FIRE",
        "TRIGGER",
        "SHOOT",
        "HARDWARE ENABLE",
    ]:
        assert token not in runtime_text
    assert status["physical_command_enabled"] is False
    assert status["no_physical_command_generated"] is True
