#!/usr/bin/env python3
"""Capture Phase 54 model-fidelity screenshots from the real cockpit routes."""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/screenshots/phase54_model_fidelity_fix"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:8014")
GECKODRIVER = os.environ.get("GECKODRIVER", "/snap/bin/geckodriver")
PORT = int(os.environ.get("GECKODRIVER_PORT", "4444"))


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_driver() -> None:
    for _ in range(80):
        try:
            request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []}).get("value")


def navigate(session_id: str, route: str, wait_s: float = 5.5) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{route}"})
    for _ in range(30):
        ready = execute(session_id, "return document.readyState")
        if ready == "complete":
            break
        time.sleep(0.2)
    for _ in range(30):
        has_canvas = execute(session_id, "return !!document.querySelector('canvas') || !!document.querySelector('svg')")
        if has_canvas:
            break
        time.sleep(0.2)
    time.sleep(wait_s)


def set_viewport(session_id: str, width: int = 1920, height: int = 1080) -> None:
    request("POST", f"/session/{session_id}/window/rect", {"width": width, "height": height})


def screenshot(session_id: str, name: str) -> Path:
    raw = request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    return path


def scroll(session_id: str, y: int) -> None:
    execute(session_id, f"window.scrollTo(0, {y});")
    time.sleep(0.8)


def copy_reference() -> None:
    source = ROOT / "reports/screenshots/phase52_freecad_match_world/freecad_reference_user_view.png"
    if not source.exists():
        source = ROOT / "reports/screenshots/phase51_freecad_fidelity_reference/freecad_reference_operator.png"
    if source.exists():
        shutil.copyfile(source, OUT / "freecad_reference_user_angle.png")


def capture_all(session_id: str) -> list[Path]:
    routes: list[tuple[str, str, float]] = [
        ("browser_step_hifi_same_angle.png", "/cockpit/world?quality=ultra&mode=freecad&asset=step-hifi&view=freecad", 6.5),
        ("browser_stl_geometry_same_angle.png", "/cockpit/world?quality=ultra&mode=freecad&asset=stl&view=freecad", 4.0),
        ("browser_hybrid_same_angle.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=freecad", 7.0),
        ("selected_default_model_same_angle.png", "/cockpit/world?quality=ultra&mode=freecad&view=freecad", 7.0),
        ("weapon_focus_closeup.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=weapon", 6.5),
        ("front_weapon_closeup.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=weaponCloseup", 6.5),
        ("side_weapon_visibility.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=side", 6.0),
        ("top_weapon_visibility.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=top", 6.0),
        ("exploded_view_weapon_parts.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=weapon&exploded=1", 6.5),
        ("wireframe_weapon_debug.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=weapon&wireframe=1", 6.5),
        ("xray_weapon_debug.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=weapon&xray=1", 6.5),
        ("freecad_match_edges_on.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=freecad", 6.5),
        ("showcase_world_weapon_visible.png", "/cockpit/world?quality=ultra&mode=showcase&asset=hybrid&view=weapon", 6.5),
        ("tactical_overlay_weapon_visible.png", "/cockpit/world?quality=ultra&mode=tactical&asset=hybrid&labels=tactical&view=weapon", 6.5),
        ("cockpit_3d_hero_model_visible.png", "/cockpit?quality=ultra&asset=hybrid&view=weapon", 6.5),
        ("cockpit_world_fullscreen_model_visible.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=freecad", 6.5),
        ("asset_compare_selector_visible.png", "/cockpit/world?quality=ultra&mode=freecad&asset=hybrid&view=freecad", 6.5),
        ("previous_glb_vs_fixed_glb_comparison.png", "/cockpit/world?quality=ultra&mode=freecad&asset=previous&view=freecad", 5.5),
    ]
    paths: list[Path] = []
    for filename, route, wait_s in routes:
        navigate(session_id, route, wait_s)
        paths.append(screenshot(session_id, filename))
    navigate(session_id, "/cockpit?quality=ultra&asset=hybrid", 5.0)
    scroll(session_id, 2600)
    paths.append(screenshot(session_id, "safety_no_physical_command.png"))
    return paths


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    copy_reference()
    driver = subprocess.Popen([GECKODRIVER, "--port", str(PORT)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        wait_driver()
        session = request("POST", "/session", {
            "capabilities": {
                "alwaysMatch": {
                    "browserName": "firefox",
                    "moz:firefoxOptions": {"args": ["-headless"]},
                },
            },
        })
        session_id = session["value"]["sessionId"]
        try:
            set_viewport(session_id)
            paths = capture_all(session_id)
            manifest = {
                "phase": 54,
                "folder": str(OUT.relative_to(ROOT)),
                "screenshots": [path.name for path in sorted(OUT.glob("*.png"))],
                "safety_note": "Screenshots are UI evidence only; no physical command is generated.",
                "physical_command_enabled": False,
                "serial_tx_enabled": False,
                "no_physical_command_generated": True,
            }
            (OUT / "screenshot_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"captured": len(paths) + (1 if (OUT / "freecad_reference_user_angle.png").exists() else 0), "folder": str(OUT)}))
        finally:
            request("DELETE", f"/session/{session_id}")
    finally:
        driver.terminate()
        try:
            driver.wait(timeout=5)
        except subprocess.TimeoutExpired:
            driver.kill()


if __name__ == "__main__":
    main()
