import time

from fastapi.testclient import TestClient

from app.schemas.command_gateway import CommandProfile
from app.schemas.vision import BBox, BalloonDetection, VisionEvent


def _fresh_balloon_event() -> VisionEvent:
    return VisionEvent(
        frame_id=79,
        timestamp_ms=int(time.time() * 1000),
        source="safety-zone-contract",
        frame_width=640,
        frame_height=360,
        fps=30,
        preprocess_ms=1,
        inference_ms=2,
        postprocess_ms=1,
        total_latency_ms=4,
        body_detections=[],
        balloon_detections=[
            BalloonDetection(
                id=1,
                confidence=0.95,
                bbox=BBox(x=290, y=150, w=60, h=60),
                center_x=320,
                center_y=180,
            )
        ],
    )


def _arm_live_test(client: TestClient):
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _fresh_balloon_event()
    response = client.post("/api/safety/command-profile", json={"profile": "LIVE_TEST", "actuator_arm": True})
    assert response.status_code == 200
    assert response.json()["ready"] is True
    return runtime


def _sector(name: str) -> dict:
    return {
        "name": name,
        "pan_min_deg": -2,
        "pan_max_deg": 2,
        "tilt_min_deg": -2,
        "tilt_max_deg": 2,
        "enabled": True,
    }


def _raw_commands(runtime) -> list[str]:
    return [entry.raw for entry in runtime.serial.logs if entry.direction.value == "tx"]


def test_operator_profile_is_persisted_separated_and_invalidates_live_authority(client: TestClient) -> None:
    runtime = _arm_live_test(client)
    response = client.put(
        "/api/safety-zones/profile",
        json={"motion_zones": [_sector("camera_tripod")], "fire_zones": [_sector("operator_sector")]},
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["source"] == "runtime_persisted"
    assert profile["profile_hash"]
    assert [item["name"] for item in profile["motion_zones"]] == ["camera_tripod"]
    assert [item["name"] for item in profile["fire_zones"]] == ["operator_sector"]
    assert runtime.safety_zones.path.exists()
    assert runtime.command_gateway.last_preflight.ready is False
    assert "SAFETY_ZONE_PROFILE_CHANGED" in runtime.command_gateway.last_preflight.reason_codes
    assert runtime.force_armed is False
    assert {"LZR,0", "STP", "DRV,0"}.issubset(set(_raw_commands(runtime)))

    # Profile update is deliberately followed by the normal visible preflight
    # flow.  The separate sectors then produce separate, stable reason codes.
    runtime.vision.latest_event = _fresh_balloon_event()
    rearmed = client.post("/api/safety/command-profile", json={"profile": "LIVE_TEST", "actuator_arm": True})
    assert rearmed.status_code == 200 and rearmed.json()["ready"] is True
    motion = runtime.command_gateway.send_motion(runtime, 20, 0)
    fire = runtime.command_gateway.fire_from_tracking(runtime, {"frame_id": 79})
    assert motion.accepted is False and "MOTION_FORBIDDEN_ZONE" in motion.reason_codes
    assert fire.accepted is False and "FIRE_FORBIDDEN_ZONE" in fire.reason_codes
    assert "LZR,1" not in _raw_commands(runtime)


def test_zone_profile_rejects_outside_soft_limits_and_stage3_profile_edits(client: TestClient) -> None:
    outside = client.put(
        "/api/safety-zones/profile",
        json={"motion_zones": [{**_sector("outside"), "pan_min_deg": -99}], "fire_zones": []},
    )
    assert outside.status_code == 409
    assert outside.json()["detail"] == "SAFETY_ZONE_OUTSIDE_SOFT_LIMITS:outside"

    runtime = client.app.state.runtime
    runtime.command_gateway.profile = CommandProfile.COMPETITION
    runtime.mission.state = runtime.mission.state.model_copy(update={"active_stage": "stage3"})
    locked = client.put("/api/safety-zones/profile", json={"motion_zones": [], "fire_zones": []})
    assert locked.status_code == 409
    assert locked.json()["detail"] == "A3_PROFILE_LOCKED"
