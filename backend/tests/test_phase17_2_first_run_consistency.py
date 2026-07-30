from fastapi.testclient import TestClient


def test_reset_clears_current_first_run_and_profile_evaluation(client: TestClient) -> None:
    client.post("/api/first-run/check")
    client.post("/api/first-run/mark-complete")
    reset = client.post("/api/first-run/reset")
    assert reset.status_code == 200
    status = client.get("/api/first-run/status").json()
    assert status["current_first_run_status"] == "open"
    assert status["current_profile_id"] == "release_candidate_ready"
    assert status["current_profile_evaluation_status"] == "not_evaluated"
    assert status["latest_report"] is None
    assert status["checks_count"] == 0
    assert status["last_successful_first_run"] is not None
    assert status["stale_evidence"] is True


def test_acceptance_updates_current_profile_snapshot(client: TestClient) -> None:
    client.post("/api/first-run/reset")
    check = client.post("/api/first-run/check")
    assert check.status_code == 200
    status = client.get("/api/first-run/status").json()
    assert status["current_first_run_status"] in {"passed", "warning", "failed"}
    assert status["current_profile_id"] == "release_candidate_ready"
    assert status["current_profile_evaluation_status"] == check.json()["profile_statuses"]["release_candidate_ready"]
    assert status["current_profile_evaluation_status"] != "not_evaluated"
    assert status["latest_report"]["run_id"] == check.json()["run_id"]


def test_report_export_separates_current_and_previous_first_run_evidence(client: TestClient) -> None:
    client.post("/api/first-run/check")
    client.post("/api/first-run/mark-complete")
    client.post("/api/first-run/reset")
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase17.2 first-run consistency"})
    assert export.status_code == 200
    summary = export.json()["summary"]
    assert summary["current_first_run_status"] == "open"
    assert summary["current_profile_evaluation_status"] == "not_evaluated"
    assert summary["stale_evidence"] is True
    assert summary["last_successful_first_run_run_id"]
    metadata_path = next(path for path in export.json()["files"] if path.endswith("export_metadata.json"))
    metadata = __import__("json").loads(__import__("pathlib").Path(metadata_path).read_text(encoding="utf-8"))
    assert metadata["current_first_run_status"] == "open"
    assert metadata["current_profile_evaluation_status"] == "not_evaluated"
    assert metadata["stale_evidence"] is True
