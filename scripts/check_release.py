#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import os
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SAFETY_TEXT = "DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false"


def check(name: str, ok: bool, message: str, blocking: bool = False, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": "passed" if ok else ("failed" if blocking else "warning"),
        "message": message,
        "blocking": blocking,
        "detail": detail or {},
    }


def writable(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".release_check_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return check(f"writable {path.name}", True, str(path), True)
    except OSError as exc:
        return check(f"writable {path.name}", False, str(exc), True)


def git_short_hash() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True)
        return result.stdout.strip() or "dev-local"
    except (OSError, subprocess.CalledProcessError):
        return "dev-local"


def launcher_has_safety_text(path: Path) -> bool:
    return path.exists() and SAFETY_TEXT in path.read_text(encoding="utf-8", errors="ignore")


def launcher_inspection(path: Path) -> dict[str, Any]:
    forbidden = [
        "/api/safety/fire-request",
        "/api/motion/jog",
        "/api/motion/go-to",
        "/api/motion/home",
        "/api/motion/scan/start",
        "physical_command_enabled=true",
        "hardware_enabled=true",
    ]
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    matches = [item for item in forbidden if item in text]
    return {
        "path": str(path),
        "exists": path.exists(),
        "contains_safety_invariant": SAFETY_TEXT in text,
        "forbidden_endpoint_calls": matches,
        "safe": path.exists() and not matches,
    }


def config_checks() -> list[dict[str, Any]]:
    path = ROOT / "config" / "config.yaml"
    if not path.exists():
        return [check("config exists", False, "config/config.yaml missing", True)]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    system = data.get("system", {})
    hardware = data.get("hardware", {})
    return [
        check("config exists", True, "config/config.yaml", True),
        check("hardware_enabled false", system.get("hardware_enabled") is False, str(system.get("hardware_enabled")), True),
        check("physical_command_enabled false", hardware.get("physical_command_enabled") is False, str(hardware.get("physical_command_enabled")), True),
        check("dry_run true", system.get("dry_run") is True, str(system.get("dry_run")), True),
        check("NO_FIRE default", system.get("default_fire_policy") == "NO_FIRE", str(system.get("default_fire_policy")), True),
    ]


def endpoint_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    sys.path.insert(0, str(BACKEND))
    try:
        from fastapi.testclient import TestClient
        from app.main import create_app
    except Exception as exc:  # pragma: no cover - release diagnostics
        return [check("backend import", False, str(exc), True)]

    checks.append(check("backend import", True, "app.main imported", True))
    app = create_app()
    with TestClient(app) as client:
        release = client.post("/api/release/check")
        checks.append(check("release check endpoint", release.status_code == 200, f"HTTP {release.status_code}", True, release.json() if release.status_code == 200 else {}))

        cold = client.get("/api/release/cold-start-check")
        cold_body = cold.json() if cold.status_code == 200 else {}
        checks.append(
            check(
                "cold-start release check endpoint",
                cold.status_code == 200 and cold_body.get("safety_invariant_ok") is True,
                f"HTTP {cold.status_code}",
                True,
                cold_body,
            )
        )

        reports = client.post("/api/reports/generate-readiness-pack", json={"notes": "phase16 release check"})
        checks.append(check("reports export works", reports.status_code == 200, f"HTTP {reports.status_code}", True, reports.json() if reports.status_code == 200 else {}))

        interfaces = client.post("/api/interfaces/export")
        checks.append(check("interfaces export works", interfaces.status_code == 200, f"HTTP {interfaces.status_code}", True, interfaces.json() if interfaces.status_code == 200 else {}))

        logs = client.post(
            "/api/logs/export-client-events",
            json={"events": [{"type": "release.check", "summary": "release check event", "seq": 1}], "source": "release_check"},
        )
        checks.append(check("logs export works", logs.status_code == 200 and logs.json().get("accepted"), f"HTTP {logs.status_code}", True, logs.json() if logs.status_code == 200 else {}))

        first_run = client.post("/api/first-run/check")
        body = first_run.json() if first_run.status_code == 200 else {}
        release_status = body.get("profile_statuses", {}).get("release_candidate_ready")
        checks.append(
            check(
                "first-run release_candidate_ready",
                first_run.status_code == 200 and release_status in {"passed", "warning"},
                f"HTTP {first_run.status_code}, status={release_status}",
                True,
                body,
            )
        )
    return checks


def write_outputs(payload: dict[str, Any]) -> tuple[Path, Path]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    json_dir = ROOT / "exports" / "release"
    md_dir = ROOT / "reports" / "release"
    json_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / f"release_check_{timestamp}.json"
    md_path = md_dir / f"release_check_{timestamp}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        f"# Release Check {timestamp}",
        "",
        f"- Commit: {payload['commit_hash']}",
        f"- Overall: {payload['status']}",
        f"- Safety invariant: {payload['safety_invariant']}",
        f"- No physical command generated: {payload['no_physical_command_generated']}",
        "",
        "## Checks",
        "",
    ]
    for item in payload["checks"]:
        lines.append(f"- [{item['status']}] {item['name']}: {item['message']}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    if os.environ.get("ISTIKLAL_RELEASE_CHECK_UV") != "1" and shutil.which("uv") is not None:
        env = os.environ.copy()
        env["ISTIKLAL_RELEASE_CHECK_UV"] = "1"
        return subprocess.run(["uv", "run", "python", str(Path(__file__).resolve())], cwd=ROOT, env=env).returncode

    linux_launcher = ROOT / "release" / "linux" / "start_istiklal_c2.sh"
    windows_launcher = ROOT / "release" / "windows" / "start_istiklal_c2.bat"
    checks = [
        check("python version", sys.version_info >= (3, 12), sys.version.split()[0], True),
        check("uv availability", shutil.which("uv") is not None, shutil.which("uv") or "uv not found", False),
        check("frontend dist", (ROOT / "frontend" / "dist" / "index.html").exists(), "frontend/dist/index.html", True),
        check("linux launcher exists", linux_launcher.exists(), str(linux_launcher), True),
        check("windows launcher exists", windows_launcher.exists(), str(windows_launcher), True),
        check("linux launcher safety invariant text", launcher_has_safety_text(linux_launcher), str(linux_launcher), True),
        check("windows launcher safety invariant text", launcher_has_safety_text(windows_launcher), str(windows_launcher), True),
        check("linux launcher static inspection", launcher_inspection(linux_launcher)["safe"], str(linux_launcher), True, launcher_inspection(linux_launcher)),
        check("windows launcher static inspection", launcher_inspection(windows_launcher)["safe"], str(windows_launcher), True, launcher_inspection(windows_launcher)),
        writable(ROOT / "logs"),
        writable(ROOT / "exports"),
        check("model dir exists", (ROOT / "models").exists(), "models/", False),
        check("firmware dir exists", (ROOT / "firmware").exists(), "firmware/", False),
    ]
    checks.extend(config_checks())
    checks.extend(endpoint_checks())
    failed = [item for item in checks if item["status"] == "failed"]
    warnings = [item for item in checks if item["status"] == "warning"]
    status = "failed" if failed else ("warning" if warnings else "passed")
    payload = {
        "commit_hash": git_short_hash(),
        "phase": "Phase 22",
        "status": status,
        "generated_at": time.time(),
        "checks": checks,
        "safety_invariant": SAFETY_TEXT,
        "no_physical_command_generated": True,
    }
    json_path, md_path = write_outputs(payload)
    payload["json_report"] = str(json_path)
    payload["markdown_report"] = str(md_path)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
