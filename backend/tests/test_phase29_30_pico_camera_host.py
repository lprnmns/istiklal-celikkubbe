from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_pico_readonly_contract_exposes_tx_disabled_fields(client: TestClient, monkeypatch) -> None:
    writes: list[bytes] = []

    class FakeSerial:
        def __init__(self, *args, **kwargs) -> None:
            self.in_waiting = 1

        def reset_input_buffer(self) -> None:
            return None

        def readline(self) -> bytes:
            self.in_waiting = 0
            return b'{"type":"telemetry","firmware_version":"telemetry-only-acceptance","heartbeat":true}\\n'

        def write(self, data: bytes) -> int:
            writes.append(data)
            raise AssertionError("serial write must not be called")

        def close(self) -> None:
            return None

    monkeypatch.setattr("app.services.pico_service.serial", SimpleNamespace(Serial=FakeSerial))
    response = client.post("/api/pico/read-only/connect", json={"port": "/dev/fakepico", "baudrate": 115200, "read_only": True})
    assert response.status_code == 200
    body = response.json()
    assert body["rx_only"] is True
    assert body["tx_disabled"] is True
    assert body["serial_write_enabled"] is False
    assert body["command_tx_enabled"] is False
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    assert writes == []

    evidence = client.post("/api/pico/read-only/capture-evidence").json()
    assert evidence["serial_write_enabled"] is False
    assert evidence["command_tx_enabled"] is False
    assert evidence["no_physical_command_generated"] is True


def test_camera_host_status_and_diagnose_contract(client: TestClient) -> None:
    status = client.get("/api/vision/camera-host/status")
    assert status.status_code == 200
    body = status.json()
    assert body["camera_acceptance_status"] in {"passed", "partial", "blocked_by_host_os", "failed"}
    assert body["camera_app_not_seen_note"] is True
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    assert isinstance(body["dev_video_entries"], list)
    assert "ffmpeg_available" in body
    assert "user_in_video_group" in body
    assert "camera_groups" in body
    for group in body["camera_groups"]:
        assert group["physical_command_enabled"] is False
        assert group["no_physical_command_generated"] is True

    diagnose = client.post("/api/vision/camera-host/diagnose")
    assert diagnose.status_code == 200
    diagnostic = diagnose.json()
    assert diagnostic["commands"]
    assert diagnostic["advisory_only"] is True
    assert diagnostic["physical_command_enabled"] is False
    assert diagnostic["no_physical_command_generated"] is True
    assert "ffmpeg -f v4l2 -list_formats all -i /dev/video0 || true" in {item["command"] for item in diagnostic["commands"]}


def test_pico_permission_status_reports_manual_fix_without_tx(client: TestClient) -> None:
    response = client.get("/api/pico/read-only/permission-status")
    assert response.status_code == 200
    body = response.json()
    assert body["blocker_class"] in {"none", "user_not_in_dialout", "device_permission_denied", "device_missing", "serial_busy"}
    assert body["serial_write_enabled"] is False
    assert body["command_tx_enabled"] is False
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    assert "sudo usermod -aG dialout $USER" in body["manual_recommendations"]


def test_real_camera_acceptance_contract(client: TestClient) -> None:
    response = client.get("/api/vision/real-camera/acceptance")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"passed", "partial", "blocked"}
    assert body["physical_command_enabled"] is False
    assert body["no_physical_command_generated"] is True
    assert body["latest_evidence"]["frame_origin"] != "mock_frame"


def test_usb_camera_selection_contract_is_evidence_only(client: TestClient) -> None:
    internal = client.post("/api/vision/real-camera/select", json={"device_path": "/dev/video0", "camera_kind": "internal_laptop_camera"})
    assert internal.status_code == 200
    assert internal.json()["camera_kind"] == "internal_laptop_camera"
    assert internal.json()["physical_command_enabled"] is False
    assert internal.json()["no_physical_command_generated"] is True

    external = client.post("/api/vision/real-camera/select", json={"device_path": "/dev/video2", "camera_kind": "external_usb_camera"})
    assert external.status_code == 200
    assert external.json()["selected_camera_device"] == "/dev/video2"
    assert external.json()["camera_kind"] == "external_usb_camera"
    assert external.json()["physical_command_enabled"] is False
    assert external.json()["no_physical_command_generated"] is True


def test_real_camera_capture_respects_host_blocker_and_no_mock_pass(client: TestClient) -> None:
    host = client.get("/api/vision/camera-host/status").json()
    capture = client.post("/api/vision/real-camera/capture-evidence", params={"device_path": "/dev/video2"})
    assert capture.status_code == 200
    evidence = capture.json()
    assert evidence["physical_command_enabled"] is False
    assert evidence["no_physical_command_generated"] is True
    assert evidence["camera_device_path"] in {None, "/dev/video2"} or evidence["camera_source"] == "host_camera_not_detected"
    if not host["host_camera_devices_detected"]:
        assert evidence["status"] == "blocked_by_host_os"
        assert evidence["camera_source"] == "host_camera_not_detected"
        assert evidence["frame_origin"] == "real_camera_not_available"
    assert evidence["frame_origin"] != "mock_frame"


def test_data_lab_and_reports_include_camera_host_diagnostics(client: TestClient) -> None:
    client.post("/api/vision/camera-host/diagnose")
    client.post("/api/vision/real-camera/capture-evidence")
    lab = client.post("/api/data-lab/export")
    assert lab.status_code == 200
    lab_files = {Path(path).name: Path(path) for path in lab.json()["files"]}
    expected = {
        "pico_permission_diagnosis.json",
        "pico_rxonly_permission_acceptance.json",
        "camera_host_device_inventory.json",
        "camera_device_inventory.json",
        "camera_tooling_diagnosis.json",
        "camera_device_permission_report.json",
        "camera_host_blocker_report.md",
        "real_camera_status.json",
        "real_camera_capture_evidence.json",
        "real_camera_frame_capture_attempt.json",
        "real_camera_frame_acceptance_result.json",
        "usb_camera_capture_evidence.json",
        "usb_camera_acceptance_summary.md",
        "real_camera_acceptance_summary.md",
    }
    assert expected <= set(lab_files)
    assert "no_physical_command_generated=true" in lab_files["camera_host_blocker_report.md"].read_text(encoding="utf-8")

    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase29 phase30"})
    assert export.status_code == 200
    report_files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert expected <= set(report_files)
    ktr = report_files["ktr_4_3_interfaces.md"].read_text(encoding="utf-8")
    assert "Camera Host Discovery and Real Camera Acceptance Boundary" in ktr
    assert "Pico Read-Only Hardware Discovery Interface" in ktr
    assert "no_physical_command_generated=true" in ktr


def test_phase29_30_log_summaries_and_safety_boundary(client: TestClient) -> None:
    client.get("/api/pico/discovery/ports")
    client.post("/api/vision/camera-host/diagnose")
    client.post("/api/vision/real-camera/capture-evidence")
    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "pico.real_port_discovered" in text
    assert "vision.camera_host_diagnosed" in text
    assert "no_physical_command_generated=true" in text
    for line in text.splitlines():
        if any(token in line for token in ("pico.real_", "vision.camera_host_", "vision.real_camera_capture_")):
            sanitized = line.replace("no_physical_command_generated=true", "")
            assert "physical command generated" not in sanitized

    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False
