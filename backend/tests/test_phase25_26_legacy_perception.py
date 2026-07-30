import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_legacy_perception_presets_are_advisory_only(client: TestClient) -> None:
    response = client.get("/api/vision/legacy-presets")
    assert response.status_code == 200
    body = response.json()
    assert body["presets"]
    assert body["no_physical_command_generated"] is True
    assert body["forbidden_runtime_tokens_present"] is False
    for preset in body["presets"]:
        assert preset["advisory_only"] is True
        assert preset["no_physical_command_generated"] is True
        forbidden = {"SPD", "STP", "HOM", "LZR", "TMC_CURRENT", "STEP", "DIR", "PWM", "GPIO", "FIRE", "TRIGGER", "SHOOT"}
        runtime_text = json.dumps(preset, ensure_ascii=False).upper()
        assert not any(token in runtime_text for token in forbidden)


def test_real_camera_status_and_capture_keep_physical_commands_disabled(client: TestClient) -> None:
    status = client.get("/api/vision/real-camera/status")
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["no_physical_command_generated"] is True
    assert status_body["physical_command_enabled"] is False

    capture = client.post("/api/vision/real-camera/capture-evidence")
    assert capture.status_code == 200
    body = capture.json()
    assert body["status"] in {"real_camera_not_available", "real_camera_frame_unavailable", "blocked_by_host_os", "partial", "recorded"}
    assert body["advisory_only"] is True
    assert body["no_physical_command_generated"] is True
    assert body["physical_command_enabled"] is False
    assert body["frame_origin"] != "mock_frame"

    latest = client.get("/api/vision/real-camera/latest")
    assert latest.status_code == 200
    assert latest.json()["evidence_id"] == body["evidence_id"]


def test_data_lab_and_report_exports_include_legacy_perception_files(client: TestClient) -> None:
    client.post("/api/vision/real-camera/capture-evidence")
    lab = client.post("/api/data-lab/export")
    assert lab.status_code == 200
    lab_files = {Path(path).name: Path(path) for path in lab.json()["files"]}
    expected = {
        "real_camera_evidence_summary.md",
        "real_camera_evidence_latest.json",
        "legacy_perception_presets.json",
        "legacy_perception_migration_summary.md",
    }
    assert expected <= set(lab_files)
    latest = json.loads(lab_files["real_camera_evidence_latest.json"].read_text(encoding="utf-8"))
    assert latest["no_physical_command_generated"] is True
    assert latest["physical_command_enabled"] is False

    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase25 phase26 perception evidence"})
    assert export.status_code == 200
    report_files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert expected <= set(report_files)
    ktr = report_files["ktr_4_3_interfaces.md"].read_text(encoding="utf-8")
    assert "Legacy Perception and Real Camera Evidence Interface" in ktr
    assert "no_physical_command_generated=true" in ktr


def test_legacy_perception_log_summaries_are_canonical(client: TestClient) -> None:
    client.get("/api/vision/legacy-presets")
    client.get("/api/vision/real-camera/status")
    client.post("/api/vision/real-camera/capture-evidence")
    client.post("/api/data-lab/export")
    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "vision.legacy_presets_loaded" in text
    assert "vision.real_camera_status_checked" in text
    assert "vision.real_camera_evidence_recorded" in text
    assert "data_lab.legacy_perception_exported" in text
    assert "no_physical_command_generated=true" in text
    for line in text.splitlines():
        if any(name in line for name in ("vision.legacy_presets_loaded", "vision.real_camera_status_checked", "vision.real_camera_evidence_recorded", "data_lab.legacy_perception_exported")):
            sanitized = line.replace("no_physical_command_generated=true", "")
            assert "physical command generated" not in sanitized


def test_phase25_26_safety_invariant(client: TestClient) -> None:
    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False
    assert client.get("/api/vision/real-camera/latest").json()["physical_command_enabled"] is False
