from pathlib import Path

from fastapi.testclient import TestClient

from app.services.storage_paths import project_root


def test_release_preflight_endpoint(client: TestClient) -> None:
    response = client.get("/api/release/preflight")
    assert response.status_code == 200
    body = response.json()
    assert body["no_physical_command_generated"] is True
    assert body["hardware_command_enabled"] is False
    assert body["dry_run"] is True
    assert body["no_fire"] is True
    assert body["safety_invariant_ok"] is True
    assert "platform" in body
    assert "suggested_actions" in body


def test_first_run_release_candidate_profile(client: TestClient) -> None:
    response = client.post("/api/first-run/check")
    assert response.status_code == 200
    body = response.json()
    assert "release_candidate_ready" in body["profile_statuses"]
    assert body["profile_statuses"]["release_candidate_ready"] == "passed"
    assert body["profile_statuses"]["competition_rehearsal_ready"] in {"blocked", "failed"}
    steps = body["profile_checklists"]["release_candidate_ready"]
    assert any(step["step_id"] == "release_manifest" for step in steps)
    assert any(step["step_id"] == "no_physical_invariant" and step["status"] == "passed" for step in steps)
    competition_steps = body["profile_checklists"]["competition_rehearsal_ready"]
    assert any(step["step_id"] == "production_model_loaded" and step["status"] == "warning" and step["blocking"] is True for step in competition_steps)
    assert any(step["step_id"] == "pico_telemetry_verified" and step["blocking"] is True for step in competition_steps)
    assert any(step["step_id"] == "competition_camera_verified" and step["blocking"] is True for step in competition_steps)
    assert any(step["step_id"] == "self_test_completed" and step["blocking"] is True for step in competition_steps)


def test_release_check_generates_manifest(client: TestClient) -> None:
    response = client.post("/api/release/check")
    assert response.status_code == 200
    body = response.json()
    manifest = body["release_manifest_path"]
    assert manifest
    assert Path(manifest).exists()
    assert body["no_physical_command_generated"] is True


def test_release_cold_start_check_contract(client: TestClient) -> None:
    response = client.get("/api/release/cold-start-check")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"passed", "warning", "failed"}
    assert body["no_physical_command_generated"] is True
    assert body["safety_invariant_ok"] is True
    assert all("blocking" in item for item in body["checks"])
    evidence = body["cold_start_evidence"]
    assert "python_version" in evidence
    assert "uv_available" in evidence
    assert "frontend_dist_present" in evidence
    assert "active_model_kind" in evidence
    assert evidence["camera_source"] in {"mock", "laptop", "usb", "video_file", "replay"}
    assert evidence["pico_state"] in {"absent", "candidate", "verified"}
    assert evidence["no_physical_command_generated"] is True


def test_first_run_reset_and_mark_complete_status(client: TestClient) -> None:
    reset = client.post("/api/first-run/reset")
    assert reset.status_code == 200
    assert reset.json()["status"]["completed"] is False
    status = client.get("/api/first-run/status").json()
    assert status["completed"] is False

    check = client.post("/api/first-run/check")
    assert check.status_code == 200
    complete = client.post("/api/first-run/mark-complete")
    assert complete.status_code == 200
    assert complete.json()["accepted"] is True
    assert complete.json()["status"]["completed"] is True
    assert client.get("/api/first-run/status").json()["completed"] is True

    reset_again = client.post("/api/first-run/reset")
    assert reset_again.status_code == 200
    assert reset_again.json()["status"]["completed"] is False


def test_ktr_export_contains_cold_start_and_launcher_inspection(client: TestClient) -> None:
    response = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase16.4 cold-start evidence test"})
    assert response.status_code == 200
    body = response.json()
    files = {Path(path).name: Path(path) for path in body["files"]}
    assert "cold_start_summary.json" in files
    assert "cold_start_summary.md" in files
    assert "launcher_inspection.md" in files
    cold_text = files["cold_start_summary.md"].read_text(encoding="utf-8")
    assert "Release candidate readiness" in cold_text
    assert "Competition rehearsal readiness" in cold_text
    assert "No physical command generated" in cold_text
    launcher_text = files["launcher_inspection.md"].read_text(encoding="utf-8")
    assert "fiziksel komut yetkisi vermez" in launcher_text


def test_launcher_files_contain_safety_invariant() -> None:
    root = project_root()
    invariant = "DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false"
    for relative in ["release/linux/start_istiklal_c2.sh", "release/windows/start_istiklal_c2.bat"]:
        text = (root / relative).read_text(encoding="utf-8")
        assert invariant in text


def test_phase15_safety_invariant(client: TestClient) -> None:
    system = client.get("/api/system/state").json()
    hardware = client.get("/api/hardware/status").json()
    assert system["mode"] == "DISARMED"
    assert system["fire_policy"] == "NO_FIRE"
    assert system["dry_run"] is True
    assert system["hardware_enabled"] is False
    assert hardware["physical_command_enabled"] is False
