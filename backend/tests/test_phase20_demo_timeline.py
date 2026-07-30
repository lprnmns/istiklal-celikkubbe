from pathlib import Path

from app.schemas.vision_runtime_settings import VisionRuntimeProfile
from fastapi.testclient import TestClient


def _enable_surrogate(client: TestClient) -> None:
    response = client.post(
        "/api/vision/runtime/apply-settings",
        json=VisionRuntimeProfile(inference_adapter="opencv_live_circle_surrogate").model_dump(mode="json"),
    )
    assert response.status_code == 200


def test_demo_timeline_run_creates_evidence_and_keeps_safety(client: TestClient) -> None:
    _enable_surrogate(client)
    response = client.post("/api/demo/run")
    assert response.status_code == 200
    body = response.json()
    steps = {event["step"] for event in body["events"]}
    assert {"safety_lock", "first_run", "vision_evidence", "data_lab_session", "replay", "annotation_review", "dataset_health", "report_export"} <= steps
    assert body["verdict"]["release_demo_ready"] is True
    assert body["verdict"]["release_demo_blockers"] == []
    assert body["verdict"]["release_demo_warnings"]
    assert body["verdict"]["competition_ready"] is False
    assert "Competition rehearsal requires production YOLO model." in body["verdict"]["competition_blockers"]
    assert "Competition rehearsal requires verified Pico telemetry." in body["verdict"]["competition_blockers"]
    assert "Competition rehearsal requires real camera evidence." in body["verdict"]["competition_blockers"]
    assert "Competition rehearsal requires completed self-test." in body["verdict"]["competition_blockers"]
    assert body["verdict"]["dataset_ready_for_training"] is False
    assert body["verdict"]["dataset_blockers"]
    assert body["no_physical_command_generated"] is True

    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False


def test_demo_readiness_and_latest_endpoints(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/demo/run")
    latest = client.get("/api/demo/latest")
    assert latest.status_code == 200
    assert latest.json()["run_id"].startswith("demo_timeline_")
    readiness = client.get("/api/demo/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["release_demo_ready"] is True
    assert readiness.json()["release_demo_blockers"] == []
    assert readiness.json()["competition_ready"] is False
    assert "Competition rehearsal requires production YOLO model." in readiness.json()["competition_blockers"]
    assert "Competition rehearsal requires verified Pico telemetry." in readiness.json()["competition_blockers"]
    assert "Competition rehearsal requires real camera evidence." in readiness.json()["competition_blockers"]
    assert "Competition rehearsal requires completed self-test." in readiness.json()["competition_blockers"]
    assert readiness.json()["dataset_ready_for_training"] is False
    assert readiness.json()["dataset_blockers"]
    assert readiness.json()["no_physical_command_generated"] is True


def test_report_export_contains_demo_timeline_files(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/demo/run")
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase20 demo timeline"})
    assert export.status_code == 200
    files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert {"demo_timeline.json", "demo_timeline.md", "demo_readiness_summary.md", "demo_runbook.md"} <= set(files)
    assert "No physical command generated: true" in files["demo_timeline.md"].read_text(encoding="utf-8")
    assert "Release demo blockers: 0" in files["demo_timeline.md"].read_text(encoding="utf-8")
    assert "## Competition Blockers" in files["demo_readiness_summary.md"].read_text(encoding="utf-8")
    assert "## Dataset Blockers" in files["demo_readiness_summary.md"].read_text(encoding="utf-8")
    assert "no_physical_command_generated: true" in files["demo_readiness_summary.md"].read_text(encoding="utf-8")
    assert "Legacy Log Format Note" in files["demo_readiness_summary.md"].read_text(encoding="utf-8")
    assert "Confirm no physical command generated" in files["demo_runbook.md"].read_text(encoding="utf-8")


def test_demo_logs_are_human_readable(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/demo/run")
    client.get("/api/demo/readiness")
    text = client.app.state.runtime.logger.path.read_text(encoding="utf-8")
    assert "demo.timeline_generated" in text
    assert "Demo evidence timeline generated; steps=" in text
    assert "demo.run_completed" in text
    assert "End-to-end demo run completed; release_demo_ready=" in text
    assert "demo.readiness_checked" in text
    assert "release_blockers=0" in text
    assert "competition_blockers=4" in text
    assert "dataset_blockers=1" in text
    assert "no_physical_command_generated=true." in text
    assert "Demo readiness checked; blockers=4; no physical command generated." not in text
    assert "telemetry update" not in text.lower()


def test_frontend_demo_readiness_log_renderer_handles_legacy_contract() -> None:
    source = Path("frontend/src/stores/systemStore.ts").read_text(encoding="utf-8")
    assert "Legacy demo readiness event; old combined blockers=" in source
    assert "see newer split readiness events for release/competition/dataset semantics" in source
    assert "no_physical_command_generated=true." in source
    demo_block = source[source.index("if (event.type.startsWith('demo.'))") :]
    readiness_idx = demo_block.index("if (event.type === 'demo.readiness_checked')")
    payload_summary_idx = demo_block.index("if (payload.summary) return payload.summary")
    assert readiness_idx < payload_summary_idx
    assert "Demo readiness checked; release_demo_ready=" in demo_block
    assert "release_blockers=" in demo_block
    assert "competition_blockers=" in demo_block
    assert "dataset_blockers=" in demo_block
    assert "dataset_blockers=${payload.dataset_blockers?.length ?? 0}; no physical command generated." not in demo_block
    assert "semantics; no physical command generated." not in demo_block
    assert not demo_block.strip().endswith("physical command generated.")


def test_logs_view_marks_legacy_demo_readiness_events() -> None:
    source = Path("frontend/src/views/LogsView.vue").read_text(encoding="utf-8")
    assert "LEGACY FORMAT" in source
    assert "OLD READINESS CONTRACT" in source
    assert "Legacy readiness log: compare with newer split release/competition/dataset readiness events." in source
    assert "whitespace-normal break-words" in source
