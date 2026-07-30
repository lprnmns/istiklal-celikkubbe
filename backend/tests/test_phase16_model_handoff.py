from pathlib import Path
import json

from fastapi.testclient import TestClient


FIXTURE = Path("backend/tests/fixtures/model_packages/opencv_test_adapter_package")
KTR_TEST_ADAPTER_SENTENCE = "Test adaptörü veya fixture model paketi, yalnızca arayüz ve veri akışı doğrulaması için kullanılır; yarışma tespit modeli olarak değerlendirilmez."


def import_fixture(client: TestClient) -> dict:
    response = client.post("/api/models/packages/import", json={"source_path": str(FIXTURE)})
    assert response.status_code == 200
    return response.json()


def model_logs(client: TestClient) -> list[dict]:
    path = client.app.state.runtime.logger.path
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def create_production_package(tmp_path: Path) -> Path:
    package = tmp_path / "production_model_package"
    package.mkdir()
    (package / "model.onnx").write_bytes(b"fixture-production-model")
    metadata = {
        "model_id": "production-yolo-fixture",
        "model_name": "Production YOLO Fixture",
        "version": "1.0.0",
        "created_by": "vision_team",
        "created_at": "2026-05-10T00:00:00Z",
        "model_format": "onnx",
        "task_type": "detection",
        "input_size": 640,
        "expected_classes": ["f16", "helicopter", "ballistic_missile", "mini_micro_uav", "balloon"],
        "class_id_to_name": {
            "0": "f16",
            "1": "helicopter",
            "2": "ballistic_missile",
            "3": "mini_micro_uav",
            "4": "balloon",
        },
        "recommended_conf": 0.35,
        "recommended_iou": 0.45,
        "recommended_imgsz": 640,
        "recommended_device": "cpu",
        "notes": "Test-only production semantics fixture for API contract validation.",
        "safety_note": "advisory_only",
        "provided_by": "vision_team",
        "production_ready": True,
    }
    thresholds = {"default_conf": 0.35, "default_iou": 0.45, "max_det": 20, "recommended_runtime_preset": "balanced"}
    (package / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (package / "thresholds.json").write_text(json.dumps(thresholds), encoding="utf-8")
    return package


def test_model_package_import_validate_activate_test_and_deactivate(client: TestClient) -> None:
    package = import_fixture(client)
    assert package["model_id"] == "fixture-opencv-test-adapter"
    assert package["checksum_sha256"]
    assert package["validation"]["valid"] is True
    assert package["validation"]["class_mapping_status"] == "complete"
    assert "fixture_or_non_production_package" in package["warnings"]

    listed = client.get("/api/models/packages")
    assert listed.status_code == 200
    assert any(item["model_id"] == package["model_id"] for item in listed.json())

    validation = client.post(f"/api/models/packages/{package['model_id']}/validate")
    assert validation.status_code == 200
    assert validation.json()["can_activate"] is True
    assert validation.json()["no_physical_command_generated"] is True

    activated = client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    assert activated.status_code == 200
    assert activated.json()["active"]["active_combined_model_id"] == package["model_id"]

    test = client.post(f"/api/models/packages/{package['model_id']}/test", json={"source": "mock"})
    assert test.status_code == 200
    assert test.json()["no_physical_command_generated"] is True
    assert test.json()["advisory_only"] is True

    benchmark = client.post(f"/api/models/packages/{package['model_id']}/benchmark")
    assert benchmark.status_code == 200
    assert benchmark.json()["no_physical_command_generated"] is True

    deactivated = client.post(f"/api/models/packages/{package['model_id']}/deactivate")
    assert deactivated.status_code == 200
    assert deactivated.json()["no_physical_command_generated"] is True


def test_duplicate_model_package_import_warns(client: TestClient) -> None:
    import_fixture(client)
    duplicate = import_fixture(client)
    assert "same_model_id_version_already_imported" in duplicate["warnings"]


def test_missing_metadata_package_rejected(client: TestClient, tmp_path: Path) -> None:
    package = tmp_path / "bad_package"
    package.mkdir()
    (package / "thresholds.json").write_text('{"default_conf":0.25,"default_iou":0.45,"max_det":20}', encoding="utf-8")
    response = client.post("/api/models/packages/import", json={"source_path": str(package)})
    assert response.status_code == 400
    assert "metadata.json is required" in response.json()["detail"]


def test_model_package_recommended_settings_and_active_endpoint(client: TestClient) -> None:
    package = import_fixture(client)
    client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    result = client.post(f"/api/models/packages/{package['model_id']}/apply-recommended-settings")
    assert result.status_code == 200
    body = result.json()
    assert body["no_physical_command_generated"] is True
    assert body["recommended_settings"]["imgsz"] == 640
    active = client.get("/api/models/active").json()
    assert active["active_combined_model_id"] == package["model_id"]
    assert active["package_kind"] == "fixture"
    assert active["package_schema_valid"] is True
    assert active["production_ready"] is False
    assert active["competition_ready"] is False
    assert active["production_readiness"] == "test_adapter_only"
    assert active["competition_readiness"] == "limited_demo_only"


def test_fixture_validation_passes_but_never_sets_production_ready(client: TestClient) -> None:
    package = import_fixture(client)
    assert package["validation"]["valid"] is True
    assert package["validation"]["production_ready"] is False
    client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    active = client.get("/api/models/active").json()
    assert active["active_model_state"] in {"fixture_model_active", "test_adapter_active"}
    assert active["package_schema_validation"] == "passed"
    assert active["production_model"] is False
    assert active["production_ready"] is False
    assert active["competition_ready"] is False
    assert "production_model_not_loaded" in active["blockers"]


def test_vision_runtime_status_does_not_report_yolo_for_fixture(client: TestClient) -> None:
    package = import_fixture(client)
    client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    client.post(f"/api/models/packages/{package['model_id']}/apply-recommended-settings")
    status = client.get("/api/vision/runtime/status")
    assert status.status_code == 200
    body = status.json()
    assert body["selected_adapter"] == "opencv_circle_test"
    assert body["effective_adapter"] == "test_adapter"
    assert body["production_yolo_loaded"] is False
    assert body["test_adapter_active"] is True
    assert body["advisory_only"] is True


def test_runtime_recommended_apply_does_not_change_safety_state(client: TestClient) -> None:
    before = client.get("/api/system/state").json()
    package = import_fixture(client)
    client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    result = client.post(f"/api/models/packages/{package['model_id']}/apply-recommended-settings")
    after = client.get("/api/system/state").json()
    assert result.status_code == 200
    assert result.json()["no_physical_command_generated"] is True
    assert before["armed"] is False and after["armed"] is False
    assert before["fire_policy"] == after["fire_policy"] == "NO_FIRE"
    assert before["dry_run"] is True and after["dry_run"] is True
    assert before["hardware_enabled"] is False and after["hardware_enabled"] is False


def test_model_event_summaries_are_human_readable(client: TestClient) -> None:
    package = import_fixture(client)
    client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    activated_logs = model_logs(client)
    activated_events = [item for item in activated_logs if item["subsystem"] == "MODEL" and item["details"].get("summary") == "Test adapter activated; production readiness remains blocked."]
    assert activated_events
    activated_payload = activated_events[-1]["details"]
    assert activated_payload["package_kind"] == "fixture"
    assert activated_payload["production_ready"] is False
    assert activated_payload["competition_ready"] is False
    assert activated_payload["no_physical_command_generated"] is True
    assert not any(item["subsystem"] == "MODEL" and item["details"].get("summary") == "Model activated" for item in activated_logs)
    client.post(f"/api/models/packages/{package['model_id']}/test", json={"source": "mock"})
    client.post(f"/api/models/packages/{package['model_id']}/apply-recommended-settings")
    logs = model_logs(client)
    assert any("Model dry-run test completed; no physical command generated." in item["message"] for item in logs)
    assert any("Recommended vision runtime settings applied; safety state unchanged." in item["message"] for item in logs)
    model_details = [item["details"] for item in logs if item["subsystem"] == "MODEL"]
    assert any(details.get("package_kind") == "fixture" and details.get("competition_ready") is False for details in model_details)
    assert all(details.get("no_physical_command_generated") is True for details in model_details)


def test_production_model_activation_summary_and_payload(client: TestClient, tmp_path: Path) -> None:
    package_path = create_production_package(tmp_path)
    response = client.post("/api/models/packages/import", json={"source_path": str(package_path)})
    assert response.status_code == 200
    model_id = response.json()["model_id"]
    activated = client.post(f"/api/models/packages/{model_id}/activate", json={"slot": "combined"})
    assert activated.status_code == 200
    logs = model_logs(client)
    production_events = [item for item in logs if item["subsystem"] == "MODEL" and item["details"].get("summary") == "Production model activated."]
    assert production_events
    payload = production_events[-1]["details"]
    assert payload["package_kind"] == "production"
    assert payload["production_ready"] is False
    assert payload["competition_ready"] is False
    assert payload["no_physical_command_generated"] is True


def test_production_package_without_real_golden_inference_stays_blocked(client: TestClient, tmp_path: Path) -> None:
    package_path = create_production_package(tmp_path)
    imported = client.post("/api/models/packages/import", json={"source_path": str(package_path)})
    assert imported.status_code == 200
    model_id = imported.json()["model_id"]
    assert client.post(f"/api/models/packages/{model_id}/activate", json={"slot": "combined"}).status_code == 200

    tested = client.post(f"/api/models/packages/{model_id}/test", json={"source": "replay"})
    assert tested.status_code == 200
    assert tested.json()["accepted"] is False
    assert tested.json()["evidence_kind"] == "not_executed"
    assert "production_golden_manifest_missing" in tested.json()["errors"]
    active = client.get("/api/models/active").json()
    assert active["production_ready"] is False
    assert "production_model_test_not_passed" in active["blockers"]


def test_first_run_competition_blocks_non_production_fixture(client: TestClient) -> None:
    package = import_fixture(client)
    client.post(f"/api/models/packages/{package['model_id']}/activate", json={"slot": "combined"})
    client.post(f"/api/models/packages/{package['model_id']}/test", json={"source": "mock"})
    first_run = client.post("/api/first-run/check")
    assert first_run.status_code == 200
    body = first_run.json()
    assert body["profile_statuses"]["release_candidate_ready"] == "passed"
    assert body["profile_statuses"]["competition_rehearsal_ready"] in {"blocked", "warning", "failed"}
    competition_steps = body["profile_checklists"]["competition_rehearsal_ready"]
    assert any(step["step_id"] == "production_model_loaded" and step["blocking"] is True for step in competition_steps)


def test_self_test_model_package_steps_and_safety_invariant(client: TestClient) -> None:
    response = client.post("/api/self-test/run")
    assert response.status_code == 200
    body = response.json()
    step_ids = {step["step_id"] for step in body["steps"]}
    assert "model_package_service" in step_ids
    assert "model_no_physical" in step_ids
    assert "competition_model_blocker" in step_ids
    assert body["no_physical_command_generated"] is True


def test_ktr_report_contains_model_package_interface(client: TestClient) -> None:
    response = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase16 pytest"})
    assert response.status_code == 200
    body = response.json()
    assert body["no_physical_command_generated"] is True
    output_dir = Path(body["output_dir"])
    ktr = (output_dir / "ktr_4_3_interfaces.md").read_text(encoding="utf-8")
    assert "Görüntü İşleme Model Paketi Arayüzü" in ktr
    assert "Test adaptörü" in ktr
    assert KTR_TEST_ADAPTER_SENTENCE in ktr
    assert "Production model paketi" in ktr
    assert "bu metadata tek başına fiziksel atış veya hareket komutu üretmez" in ktr
    assert (output_dir / "model_package_inventory.json").exists()
    assert (output_dir / "active_model_summary.json").exists()
    active_summary = (output_dir / "active_model_summary.json").read_text(encoding="utf-8")
    assert "package_kind" in active_summary
    assert "production_ready" in active_summary
    assert "competition_ready" in active_summary
    assert "no_physical_command_generated" in active_summary
