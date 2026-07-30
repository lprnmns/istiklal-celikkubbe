import zipfile
from pathlib import Path

from fastapi.testclient import TestClient


def test_cleanroom_verification_runs_from_extracted_package(client: TestClient) -> None:
    package = client.post("/api/release/package/build")
    assert package.status_code == 200
    response = client.post("/api/release/clean-room/run")
    assert response.status_code == 200
    body = response.json()
    assert body["smoke_status"] == "passed"
    assert body["endpoints_passed"] == body["endpoints_total"]
    assert body["frontend_dist_present"] is True
    assert body["backend_present"] is True
    assert body["forbidden_entries"] == []
    assert body["secrets_or_tokens"] == []
    assert body["launcher_hardcoded_repo_path"] is False
    assert body["release_demo_ready"] is True
    assert body["competition_ready"] is False
    assert body["no_physical_command_generated"] is True
    assert Path("reports/phase23_cleanroom_smoke_results.json").exists()
    assert Path("reports/phase23_cleanroom_smoke_summary.md").exists()


def test_cleanroom_zip_forbidden_entries_guard(client: TestClient) -> None:
    body = client.post("/api/release/package/build").json()
    with zipfile.ZipFile(body["zip_path"]) as archive:
        names = archive.namelist()
    forbidden = [".git", "node_modules", ".venv", "__pycache__"]
    assert not any(any(part in name.split("/") for part in forbidden) for name in names)
    assert not any("secret" in name.lower() or "token" in name.lower() for name in names)


def test_jury_rehearsal_keeps_split_verdict_and_safety(client: TestClient) -> None:
    client.post("/api/release/package/build")
    client.post("/api/release/clean-room/run")
    response = client.post("/api/demo/jury-rehearsal/run")
    assert response.status_code == 200
    body = response.json()
    verdict = body["verdict"]
    assert verdict["release_demo_ready"] is True
    assert verdict["competition_ready"] is False
    assert "Competition rehearsal requires production YOLO model." in verdict["competition_blockers"]
    assert body["cleanroom_verified"] is True
    assert body["no_physical_command_generated"] is True


def test_reports_include_cleanroom_and_jury_rehearsal_files(client: TestClient) -> None:
    client.post("/api/release/package/build")
    client.post("/api/release/clean-room/run")
    client.post("/api/demo/jury-rehearsal/run")
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase23 phase24"})
    assert export.status_code == 200
    files = {Path(path).name: Path(path) for path in export.json()["files"]}
    expected = {
        "release_portability_audit.md",
        "cleanroom_smoke_results.json",
        "cleanroom_launch_notes.md",
        "portable_runtime_requirements.md",
        "jury_rehearsal_summary.md",
        "jury_rehearsal_verdict.json",
        "jury_rehearsal_timeline.md",
        "jury_rehearsal_operator_script.md",
        "jury_rehearsal_limitations.md",
        "jury_rehearsal_cleanroom_status.md",
    }
    assert expected <= set(files)
    assert "no_physical_command_generated=true" in files["release_portability_audit.md"].read_text(encoding="utf-8")
    assert "no_physical_command_generated=true" in files["jury_rehearsal_operator_script.md"].read_text(encoding="utf-8")
