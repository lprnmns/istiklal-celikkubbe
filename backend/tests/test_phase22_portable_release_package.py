import zipfile
import json
from pathlib import Path

from app.schemas.vision_runtime_settings import VisionRuntimeProfile
from fastapi.testclient import TestClient


def _enable_surrogate(client: TestClient) -> None:
    response = client.post(
        "/api/vision/runtime/apply-settings",
        json=VisionRuntimeProfile(inference_adapter="opencv_live_circle_surrogate").model_dump(mode="json"),
    )
    assert response.status_code == 200


def test_release_package_build_creates_manifest_zip_and_checksums(client: TestClient) -> None:
    _enable_surrogate(client)
    response = client.post("/api/release/package/build")
    assert response.status_code == 200
    body = response.json()
    assert body["package_id"].startswith("istiklal_c2_release_")
    assert body["no_physical_command_generated"] is True
    assert body["release_demo_ready"] is True
    assert body["competition_ready"] is False
    assert body["dataset_ready_for_training"] is False
    assert Path(body["manifest_path"]).exists()
    assert Path(body["checksums_path"]).exists()
    assert Path(body["zip_path"]).exists()
    assert body["source_commit"] == "b82c434"
    assert body["package_workflow_commit"] == "b82c434"
    assert body["package_generated_commit"] not in {"", "unknown", "045ebb3"}
    assert body["report_commit"] not in {"", "unknown", "045ebb3"}
    manifest = json.loads(Path(body["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["commit_hash"] == body["package_generated_commit"]
    assert manifest["source_commit"] == "b82c434"
    assert manifest["package_workflow_commit"] == "b82c434"
    assert manifest["package_generated_commit"] not in {"", "unknown", "045ebb3"}
    assert manifest["report_commit"] not in {"", "unknown", "045ebb3"}
    assert manifest["no_physical_command_generated"] is True

    latest = client.get("/api/release/package/latest")
    assert latest.status_code == 200
    assert latest.json()["package_id"] == body["package_id"]


def test_release_zip_excludes_runtime_and_secret_like_paths(client: TestClient) -> None:
    _enable_surrogate(client)
    body = client.post("/api/release/package/build").json()
    with zipfile.ZipFile(body["zip_path"]) as archive:
        names = archive.namelist()
    forbidden = [".git", "node_modules", ".venv", "__pycache__"]
    assert not any(any(part in name.split("/") for part in forbidden) for name in names)
    assert not any("secret" in name.lower() or "token" in name.lower() for name in names)
    assert any(name.endswith("package_manifest.json") for name in names)
    assert any(name.endswith("checksums.json") for name in names)
    assert any(name.endswith("README_RELEASE.md") for name in names)
    assert any(name.endswith("RUNBOOK_DEMO.md") for name in names)


def test_release_package_report_files_and_safety_invariant(client: TestClient) -> None:
    _enable_surrogate(client)
    client.post("/api/release/package/build")
    export = client.post("/api/reports/generate-ktr-summary", json={"notes": "phase22 release package"})
    files = {Path(path).name: Path(path) for path in export.json()["files"]}
    assert {"release_package_summary.md", "release_package_manifest.json", "release_zip_check.md"} <= set(files)
    summary = files["release_package_summary.md"].read_text(encoding="utf-8")
    assert "Portable release package is a demo/evidence package" in summary
    assert "Source commit: b82c434" in summary
    assert "Package workflow commit: b82c434" in summary
    assert "045ebb3" not in summary
    zip_check = files["release_zip_check.md"].read_text(encoding="utf-8")
    assert "Checksum status: passed" in zip_check
    assert "no_physical_command_generated=true" in zip_check
    manifest = json.loads(files["release_package_manifest.json"].read_text(encoding="utf-8"))
    assert manifest["source_commit"] == "b82c434"
    assert manifest["package_workflow_commit"] == "b82c434"
    assert manifest["package_generated_commit"] not in {"", "unknown", "045ebb3"}

    state = client.get("/api/system/state").json()
    assert state["mode"] == "DISARMED"
    assert state["fire_policy"] == "NO_FIRE"
    assert state["dry_run"] is True
    assert state["hardware_enabled"] is False


def test_launcher_scripts_do_not_contain_physical_command_patterns() -> None:
    forbidden = ["/api/safety/fire-request", "/api/motion/jog", "/api/motion/go-to", "hardware_enabled=true", "physical_command_enabled=true", "allow_physical_fire=true"]
    for path in [Path("release/linux/start_istiklal_c2.sh"), Path("start_linux.sh")]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden:
            assert pattern not in text


def test_known_limitations_layout_uses_overlap_safe_rows() -> None:
    source = Path("frontend/src/views/DemoView.vue").read_text(encoding="utf-8")
    assert "sm:grid-cols-[minmax(0,1fr)_max-content]" in source
    assert "whitespace-normal break-words" in source
    assert "whitespace-nowrap" in source
    assert "competition blocker / demo limitation" in source
