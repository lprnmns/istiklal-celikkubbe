import shutil
from pathlib import Path

import yaml
from app.main import create_app
from app.services.storage_paths import project_root
from fastapi.testclient import TestClient


def test_first_run_status_and_check(client: TestClient) -> None:
    status = client.get("/api/first-run/status")
    assert status.status_code == 200
    body = status.json()
    assert body["no_physical_command_generated"] is True

    check = client.post("/api/first-run/check")
    assert check.status_code == 200
    result = check.json()
    assert result["no_physical_command_generated"] is True
    assert any(step["step_id"] == "no_physical_invariant" for step in result["steps"])


def test_interface_inventory_and_ktr_section(client: TestClient) -> None:
    inventory = client.get("/api/interfaces/inventory")
    assert inventory.status_code == 200
    body = inventory.json()
    assert body["no_physical_command_generated"] is True
    assert len(body["interfaces"]) >= 10
    assert any(item["interface_id"] == "portable_launcher" for item in body["interfaces"])

    section = client.get("/api/interfaces/ktr-section")
    assert section.status_code == 200
    markdown = section.json()["markdown"]
    assert "KTR 4.3 Arayüzler" in markdown
    assert "Kullanıcı Arayüzü" in markdown
    assert "Güvenlik Arayüzleri" in markdown


def test_ktr_export_contains_interface_section(client: TestClient) -> None:
    response = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase 13 test"})
    assert response.status_code == 200
    body = response.json()
    files = [Path(path).name for path in body["files"]]
    assert "interface_inventory.md" in files
    assert "ktr_4_3_interfaces.md" in files
    assert body["no_physical_command_generated"] is True


def test_static_frontend_spa_fallback(tmp_path: Path, config_data) -> None:
    dist = project_root() / "frontend" / "dist"
    old_index = dist / "index.html"
    backup = dist / "index.html.phase13_test_backup"
    had_old = old_index.exists()
    dist.mkdir(parents=True, exist_ok=True)
    if had_old:
        shutil.copy2(old_index, backup)
    try:
        old_index.write_text("<html><body>phase13</body></html>", encoding="utf-8")
        config_data["models"]["root_dir"] = str(tmp_path / "models")
        config_data["models"]["active_models_file"] = str(tmp_path / "models" / "active" / "active_models.json")
        config_data["dataset"]["root_dir"] = str(tmp_path / "data")
        config_data["reports"]["root_dir"] = str(tmp_path / "exports" / "reports")
        config_data["runtime_mode"]["frontend_static_enabled"] = True
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
        app = create_app(config_path=config_path, log_dir=tmp_path / "logs")
        with TestClient(app) as local_client:
            response = local_client.get("/interfaces")
            assert response.status_code == 200
            assert "phase13" in response.text
            api_response = local_client.get("/api/health")
            assert api_response.status_code == 200
    finally:
        if backup.exists():
            shutil.move(str(backup), str(old_index))
        elif not had_old:
            old_index.unlink(missing_ok=True)


def test_launcher_config_validation(config_data) -> None:
    runtime_mode = config_data["runtime_mode"]
    assert runtime_mode["mode"] in {"development", "portable", "demo", "field_dry_run"}
    assert "frontend_static_enabled" in runtime_mode
    assert "dependency_check_enabled" in runtime_mode


def test_logs_jsonl_export(client: TestClient) -> None:
    response = client.post(
        "/api/logs/export-client-events",
        json={"events": [{"type": "phase13.test", "summary": "ok", "seq": 1}], "source": "pytest"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["count"] == 1
    assert body["no_physical_command_generated"] is True
    assert Path(body["path"]).exists()


def test_phase13_safety_invariant(client: TestClient) -> None:
    state = client.get("/api/system/state").json()
    hardware = client.get("/api/hardware/status").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False
    assert hardware["physical_command_enabled"] is False
