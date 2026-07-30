from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_named_setup_profile_saves_portable_paths_and_reapplies_runtime(client: TestClient, tmp_path: Path) -> None:
    runtime = client.app.state.runtime
    runtime.device_profiles.root = tmp_path / "device_profiles"
    runtime.device_profiles.root.mkdir(parents=True, exist_ok=True)
    model_path = Path(__file__).resolve().parents[2] / "models" / "incoming" / "legacy-balloon-yolo-0.1.0" / "model.pt"
    assert model_path.is_file()

    configured = client.put(
        "/api/vision/config",
        json={
            "vision_mode": "ultralytics_yolo",
            "body_model_path": None,
            "balloon_model_path": str(model_path),
            "body_conf_threshold": 0.35,
            "balloon_conf_threshold": 0.123,
        },
    )
    assert configured.status_code == 200

    saved = client.post(
        "/api/device-profiles/save",
        json={
            "display_name": "Laptop Kamera Testi",
            "command_profile": "DRY_RUN",
            "servo_release_deg": 32,
            "servo_fire_deg": 171,
            "servo_pulse_s": 0.8,
        },
    )
    assert saved.status_code == 200
    profile = saved.json()["profile"]
    assert profile["profile_id"] == "laptop-kamera-testi"
    assert profile["display_name"] == "Laptop Kamera Testi"
    assert profile["vision_config"]["balloon_model_path"] == "models/incoming/legacy-balloon-yolo-0.1.0/model.pt"
    assert profile["vision_config"]["balloon_conf_threshold"] == 0.123
    assert profile["servo_release_deg"] == 32
    assert profile["servo_fire_deg"] == 171

    client.put(
        "/api/vision/config",
        json={
            "vision_mode": "ultralytics_yolo",
            "body_model_path": None,
            "balloon_model_path": None,
            "body_conf_threshold": 0.8,
            "balloon_conf_threshold": 0.8,
        },
    )
    applied = client.post("/api/device-profiles/apply", json={"profile_id": "laptop-kamera-testi"})
    assert applied.status_code == 200
    assert applied.json()["accepted"] is True
    assert runtime.vision.balloon_model_path == str(model_path)
    assert runtime.vision.balloon_conf_threshold == 0.123

    listed = client.get("/api/device-profiles")
    assert listed.status_code == 200
    assert [item["display_name"] for item in listed.json()["profiles"]] == ["Laptop Kamera Testi"]
