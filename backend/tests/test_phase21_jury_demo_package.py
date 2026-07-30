from pathlib import Path

from app.schemas.vision_runtime_settings import VisionRuntimeProfile
from fastapi.testclient import TestClient


def _enable_surrogate(client: TestClient) -> None:
    response = client.post(
        "/api/vision/runtime/apply-settings",
        json=VisionRuntimeProfile(inference_adapter="opencv_live_circle_surrogate").model_dump(mode="json"),
    )
    assert response.status_code == 200


def test_jury_demo_run_exports_verdict_and_keeps_safety(client: TestClient) -> None:
    _enable_surrogate(client)
    response = client.post("/api/demo/run")
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]["release_demo_ready"] is True
    assert body["verdict"]["competition_ready"] is False
    assert body["verdict"]["dataset_ready_for_training"] is False
    assert body["no_physical_command_generated"] is True
    assert body["report_export_id"]

    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False


def test_ktr_export_contains_jury_demo_package_files(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/demo/run")
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase21 jury demo package"})
    assert export.status_code == 200
    files = {Path(path).name: Path(path) for path in export.json()["files"]}
    expected = {
        "jury_demo_summary.md",
        "release_demo_verdict.json",
        "evidence_index.md",
        "known_limitations.md",
        "demo_operator_script.md",
    }
    assert expected <= set(files)
    assert "Production YOLO modeli henüz yüklenmedi." in files["known_limitations.md"].read_text(encoding="utf-8")
    assert "Dashboard açılır" in files["demo_operator_script.md"].read_text(encoding="utf-8")
    assert "demo_timeline.md" in files["evidence_index.md"].read_text(encoding="utf-8")
    assert '"no_physical_command_generated": true' in files["release_demo_verdict.json"].read_text(encoding="utf-8")
    assert "no_physical_command_generated=true" in files["jury_demo_summary.md"].read_text(encoding="utf-8")


def test_demo_jury_package_logs_are_human_readable(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/demo/run")
    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "demo.jury_package_generated" in text
    assert "Jury demo package generated; export_id=" in text
    assert "demo.evidence_index_generated" in text
    assert "Demo evidence index generated; files=" in text
    assert "demo.operator_script_generated" in text
    assert "Demo operator script generated; no_physical_command_generated=true." in text
    assert "telemetry update" not in text.lower()


def test_interface_inventory_mentions_jury_demo_center(client: TestClient) -> None:
    response = client.get("/api/interfaces/ktr-section")
    assert response.status_code == 200
    text = response.text
    assert "Jury Demo Center" in text
    assert "jury_demo_summary.md" in text
    assert "fiziksel komut üretmez" in text
