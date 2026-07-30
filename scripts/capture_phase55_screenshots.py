#!/usr/bin/env python3
"""Capture Phase 55 kinematic digital twin screenshots from real routes."""

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
OUT = ROOT / "reports/screenshots/phase55_kinematic_digital_twin"
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
    for _ in range(90):
        try:
            request("GET", "/status")
            return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("geckodriver did not start")


def execute(session_id: str, script: str):
    return request("POST", f"/session/{session_id}/execute/sync", {"script": script, "args": []}).get("value")


def set_viewport(session_id: str, width: int = 1920, height: int = 1080) -> None:
    request("POST", f"/session/{session_id}/window/rect", {"width": width, "height": height})


def navigate(session_id: str, route: str, wait_s: float = 6.5) -> None:
    request("POST", f"/session/{session_id}/url", {"url": f"{BASE}{route}"})
    for _ in range(40):
        if execute(session_id, "return document.readyState") == "complete":
            break
        time.sleep(0.2)
    for _ in range(60):
        if execute(session_id, "return !!document.querySelector('canvas') || !!document.querySelector('svg')"):
            break
        time.sleep(0.2)
    time.sleep(wait_s)


def screenshot(session_id: str, name: str) -> Path:
    raw = request("GET", f"/session/{session_id}/screenshot")["value"]
    path = OUT / name
    path.write_bytes(base64.b64decode(raw))
    return path


def click_canvas(session_id: str) -> None:
    execute(session_id, """
      const canvas = document.querySelector('canvas');
      if (!canvas) return false;
      const r = canvas.getBoundingClientRect();
      canvas.dispatchEvent(new PointerEvent('pointermove', {clientX: r.left + r.width * 0.52, clientY: r.top + r.height * 0.48, bubbles: true}));
      canvas.dispatchEvent(new MouseEvent('click', {clientX: r.left + r.width * 0.52, clientY: r.top + r.height * 0.48, bubbles: true}));
      return true;
    """)
    time.sleep(1.0)


def scroll(session_id: str, y: int) -> None:
    execute(session_id, f"window.scrollTo(0, {y});")
    time.sleep(0.9)


def copy_reference() -> None:
    source = ROOT / "reports/screenshots/phase54_model_fidelity_fix/freecad_reference_user_angle.png"
    if not source.exists():
        source = ROOT / "reports/screenshots/phase52_freecad_match_world/freecad_reference_user_view.png"
    if source.exists():
        shutil.copyfile(source, OUT / "freecad_reference.png")


def capture_all(session_id: str) -> list[Path]:
    routes: list[tuple[str, str, float, bool]] = [
        ("browser_freecad_match.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&view=freecad", 7.0, False),
        ("browser_operator_view.png", "/cockpit/world?quality=ultra&mode=showcase&asset=phase55-kinematic&view=operator", 7.0, False),
        ("browser_front_weapon_closeup.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&view=weaponCloseup", 7.0, False),
        ("browser_yaw_preview_left.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&view=operator&yaw=-30", 7.0, False),
        ("browser_yaw_preview_right.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&view=operator&yaw=30", 7.0, False),
        ("browser_pitch_preview_up.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&view=weapon&pitch=35", 7.0, False),
        ("browser_pitch_preview_down.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&view=weapon&pitch=-8", 7.0, False),
        ("browser_clean_mode.png", "/cockpit/world?quality=ultra&mode=freecad&asset=phase55-kinematic&labels=clean", 7.0, False),
        ("browser_debug_inspector.png", "/cockpit/world?quality=ultra&mode=tactical&asset=phase55-kinematic&labels=debug&fov=1&target=1", 7.0, True),
        ("browser_tactical_overlay.png", "/cockpit/world?quality=ultra&mode=tactical&asset=phase55-kinematic&labels=tactical&fov=1&target=1", 7.0, False),
    ]
    paths: list[Path] = []
    for filename, route, wait_s, click in routes:
        navigate(session_id, route, wait_s)
        if click:
            click_canvas(session_id)
        paths.append(screenshot(session_id, filename))
    navigate(session_id, "/cockpit?quality=ultra&asset=phase55-kinematic", 7.0)
    scroll(session_id, 2800)
    paths.append(screenshot(session_id, "browser_safety_strip.png"))
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
                "phase": 55,
                "folder": str(OUT.relative_to(ROOT)),
                "screenshots": [path.name for path in sorted(OUT.glob("*.png"))],
                "safety_note": "Screenshots are UI evidence only; yaw/pitch controls are read-only preview controls and no physical command is generated.",
                "physical_command_enabled": False,
                "serial_tx_enabled": False,
                "no_physical_command_generated": True,
            }
            (OUT / "screenshot_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"captured": len(paths) + (1 if (OUT / "freecad_reference.png").exists() else 0), "folder": str(OUT)}))
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
