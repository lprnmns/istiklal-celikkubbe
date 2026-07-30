import time

from fastapi.testclient import TestClient

from app.schemas.command_gateway import CommandProfile
from app.schemas.vision import BBox, BalloonDetection, VisionEvent


def _fresh_event() -> VisionEvent:
    balloon = BalloonDetection(id=1, confidence=0.95, bbox=BBox(x=290, y=150, w=60, h=60), center_x=320, center_y=180, source="stage1")
    return VisionEvent(
        frame_id=1, timestamp_ms=int(time.time() * 1000), source="stage1", frame_width=640, frame_height=360,
        fps=30.0, preprocess_ms=1.0, inference_ms=1.0, postprocess_ms=1.0, total_latency_ms=3.0,
        body_detections=[], balloon_detections=[balloon],
    )


def test_locked_stage1_blocks_tracking_originated_fire(client: TestClient) -> None:
    runtime = client.app.state.runtime
    assert client.post("/api/mission/reset").status_code == 200
    runtime.vision.latest_event = _fresh_event()
    assert client.post("/api/safety/command-profile", json={"profile": "COMPETITION", "actuator_arm": True}).json()["ready"] is True
    assert client.post("/api/mission/stage1/start").status_code == 200

    result = runtime.command_gateway.fire_from_tracking(runtime, {"frame_id": 1})

    assert result.accepted is False
    assert result.reason_codes == ["MANUAL_OPERATOR_COMMAND_REQUIRED"]
    assert all(entry.raw != "LZR,1" for entry in runtime.serial.logs)

    motion = runtime.command_gateway.send_motion(runtime, 100, 0, origin="tracking")
    assert motion.accepted is False
    assert motion.reason_codes == ["MANUAL_TRACKING_MOTION_BLOCKED"]
    assert all(entry.raw != "SPD,100,0" for entry in runtime.serial.logs)


def test_manual_stop_is_always_a_gateway_safe_command(client: TestClient) -> None:
    runtime = client.app.state.runtime

    response = client.post("/api/hardware/manual-stop")

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert any(entry.raw == "STP" for entry in runtime.serial.logs)


def test_stage1_manual_motion_requires_locked_timed_mission_and_uses_gateway(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _fresh_event()
    assert client.post("/api/safety/command-profile", json={"profile": "LIVE_TEST", "actuator_arm": True}).json()["ready"] is True
    live = client.post("/api/mission/manual-motion", json={"speed_x": 100, "speed_y": 0, "duration_ms": 50})
    assert live.json()["accepted"] is True

    assert client.post("/api/mission/reset").status_code == 200
    runtime.vision.latest_event = _fresh_event()
    assert client.post("/api/safety/command-profile", json={"profile": "COMPETITION", "actuator_arm": True}).json()["ready"] is True
    blocked = client.post("/api/mission/manual-motion", json={"speed_x": 100, "speed_y": 0, "duration_ms": 50})
    assert blocked.json()["reason_codes"] == ["STAGE1_PLAN_NOT_STARTED"]
    assert client.post("/api/mission/stage1/start").status_code == 200
    accepted = client.post("/api/mission/manual-motion", json={"speed_x": 100, "speed_y": 0, "duration_ms": 50})
    assert accepted.json()["accepted"] is True
    assert any(entry.raw == "SPD,0,100" for entry in runtime.serial.logs)
    assert any(entry.raw == "STP" for entry in runtime.serial.logs)


def test_mission_stage_transition_safes_gateway_and_tracker(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.auto_tracker.start_tracking()
    runtime.command_gateway.driver_enabled = True

    response = client.put("/api/mission/status", json={"active_stage": "stage2"})

    assert response.status_code == 200
    assert runtime.auto_tracker.tracking_active is False
    assert runtime.command_gateway.driver_enabled is False
    assert any(entry.raw == "STP" for entry in runtime.serial.logs)


def test_locked_stage1_accepts_explicit_manual_fire_through_gateway(client: TestClient) -> None:
    runtime = client.app.state.runtime
    assert client.post("/api/mission/reset").status_code == 200
    runtime.vision.latest_event = _fresh_event()
    assert client.post("/api/safety/command-profile", json={"profile": "COMPETITION", "actuator_arm": True}).json()["ready"] is True
    assert client.post("/api/mission/stage1/start").status_code == 200

    response = client.post("/api/safety/fire-request", json={"operator_confirmed": True})

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert any(entry.raw == "LZR,1" for entry in runtime.serial.logs)


def test_live_test_manual_fire_needs_only_gateway_preflight_not_stage1_plan_or_timer(client: TestClient) -> None:
    runtime = client.app.state.runtime
    assert client.post("/api/mission/reset").status_code == 200
    runtime.vision.latest_event = _fresh_event().model_copy(update={"balloon_detections": []})
    preflight = client.post("/api/safety/command-profile", json={"profile": "LIVE_TEST", "actuator_arm": True})
    assert preflight.json()["ready"] is True

    response = client.post("/api/safety/fire-request", json={"operator_confirmed": True})

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert any(entry.raw == "LZR,1" for entry in runtime.serial.logs)


def test_video_demo_profile_is_manual_and_independent_from_stage1_timer(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _fresh_event().model_copy(update={"balloon_detections": []})

    profile = client.post("/api/safety/command-profile", json={"profile": "VIDEO_DEMO", "actuator_arm": True})
    fire = client.post("/api/safety/fire-request", json={"operator_confirmed": True})

    assert profile.json()["ready"] is True
    assert runtime.config.system.mode.value == "MANUAL"
    assert fire.status_code == 200
    assert fire.json()["accepted"] is True


def test_stage2_and_stage3_competition_are_independent_from_stage1_plan_and_timer(client: TestClient) -> None:
    runtime = client.app.state.runtime
    for stage in ("stage2", "stage3"):
        assert client.post("/api/mission/reset").status_code == 200
        assert client.put("/api/mission/status", json={"active_stage": stage}).status_code == 200
        runtime.vision.latest_event = _fresh_event()
        profile = client.post("/api/safety/command-profile", json={"profile": "COMPETITION", "actuator_arm": True})
        motion = runtime.command_gateway.send_motion(runtime, 100, 0, origin="tracking")

        assert profile.json()["ready"] is True
        assert runtime.mission.state.stage1_order_locked is False
        assert runtime.mission.state.timer_running is False
        assert motion.accepted is True


def test_stage_transition_clears_stage1_timer_before_stage2(client: TestClient) -> None:
    assert client.post("/api/mission/reset").status_code == 200
    assert client.post("/api/mission/stage1/start").status_code == 200

    transition = client.put("/api/mission/status", json={"active_stage": "stage2"})

    assert transition.status_code == 200
    assert transition.json()["state"]["timer_running"] is False
