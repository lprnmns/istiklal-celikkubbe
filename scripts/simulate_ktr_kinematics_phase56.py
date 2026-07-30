#!/usr/bin/env python3
"""Simulate Phase 56 yaw/pitch preview transforms for anchor consistency."""

from __future__ import annotations

import json
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KINEMATICS_PATH = PROJECT_ROOT / "frontend/public/assets/digital-twin/ktr1_kinematics.json"
OUT_JSON = PROJECT_ROOT / "reports/phase56_kinematic_preview_simulation.json"
OUT_MD = PROJECT_ROOT / "reports/phase56_kinematic_preview_simulation.md"


def sub(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def rot_y(point: list[float], degrees: float) -> list[float]:
    c = math.cos(math.radians(degrees))
    s = math.sin(math.radians(degrees))
    x, y, z = point
    return [x * c + z * s, y, -x * s + z * c]


def rot_x(point: list[float], degrees: float) -> list[float]:
    c = math.cos(math.radians(degrees))
    s = math.sin(math.radians(degrees))
    x, y, z = point
    return [x, y * c - z * s, y * s + z * c]


def rotate_about(point: list[float], pivot: list[float], axis: str, degrees: float) -> list[float]:
    local = sub(point, pivot)
    rotated = rot_y(local, degrees) if axis == "yaw" else rot_x(local, degrees)
    return add(rotated, pivot)


def transform_anchor(point: list[float], yaw_pivot: list[float], pitch_pivot: list[float], yaw_deg: float, pitch_deg: float) -> list[float]:
    pitched = rotate_about(point, pitch_pivot, "pitch", pitch_deg)
    return rotate_about(pitched, yaw_pivot, "yaw", yaw_deg)


def main() -> None:
    kinematics = json.loads(KINEMATICS_PATH.read_text(encoding="utf-8"))
    yaw_pivot = kinematics["pivots"]["yaw_pivot"]["position"]
    pitch_pivot = kinematics["pivots"]["pitch_pivot"]["position"]
    camera = kinematics["anchors"]["camera_origin"]["position"]
    launcher = kinematics["anchors"]["launcher_origin"]["position"]
    baseline_distance = dist(camera, launcher)
    poses = [
        {"name": "neutral", "yawDeg": 0, "pitchDeg": 0},
        {"name": "yaw_left", "yawDeg": -30, "pitchDeg": 0},
        {"name": "yaw_right", "yawDeg": 30, "pitchDeg": 0},
        {"name": "pitch_down", "yawDeg": 0, "pitchDeg": -10},
        {"name": "pitch_up", "yawDeg": 0, "pitchDeg": 35},
        {"name": "combined", "yawDeg": 25, "pitchDeg": 25},
    ]
    results = []
    for pose in poses:
        camera_out = transform_anchor(camera, yaw_pivot, pitch_pivot, pose["yawDeg"], pose["pitchDeg"])
        launcher_out = transform_anchor(launcher, yaw_pivot, pitch_pivot, pose["yawDeg"], pose["pitchDeg"])
        results.append({
            **pose,
            "camera": [round(value, 5) for value in camera_out],
            "launcher": [round(value, 5) for value in launcher_out],
            "cameraLauncherDistance": round(dist(camera_out, launcher_out), 6),
            "distanceError": round(abs(dist(camera_out, launcher_out) - baseline_distance), 9),
        })

    max_error = max(item["distanceError"] for item in results)
    payload = {
        "schema": "phase56_kinematic_preview_simulation",
        "kinematicsPath": "/assets/digital-twin/ktr1_kinematics.json",
        "yawPivot": yaw_pivot,
        "pitchPivot": pitch_pivot,
        "baselineCameraLauncherDistance": round(baseline_distance, 6),
        "maxCameraLauncherDistanceError": max_error,
        "cameraLauncherRigid": max_error < 1e-6,
        "poses": results,
        "safety": {
            "physical_command_enabled": False,
            "serial_tx_enabled": False,
            "no_physical_command_generated": True,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "\n".join([
            "# Phase 56 Kinematic Preview Simulation",
            "",
            "This validates only browser-side digital twin preview math. It does not command hardware.",
            "",
            f"- Yaw pivot: `{yaw_pivot}`",
            f"- Pitch pivot: `{pitch_pivot}`",
            f"- Baseline camera-launcher distance: `{payload['baselineCameraLauncherDistance']}`",
            f"- Max distance error under preview poses: `{max_error}`",
            f"- Camera/launcher rigid under preview: `{payload['cameraLauncherRigid']}`",
            "",
            "## Poses",
            "",
            "| Pose | Yaw | Pitch | Camera | Launcher | Distance error |",
            "|---|---:|---:|---|---|---:|",
            *[
                f"| {item['name']} | {item['yawDeg']} | {item['pitchDeg']} | `{item['camera']}` | `{item['launcher']}` | {item['distanceError']} |"
                for item in results
            ],
            "",
            "## Safety",
            "",
            "- `physical_command_enabled=false`",
            "- `serial_tx_enabled=false`",
            "- `no_physical_command_generated=true`",
            "",
        ]),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
