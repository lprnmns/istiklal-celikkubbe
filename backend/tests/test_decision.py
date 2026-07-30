from fastapi.testclient import TestClient

from app.schemas.vision import BalloonDetection, BBox, BodyDetection, VisionEvent


def make_event(
    class_name: str = "helicopter",
    team: str = "enemy",
    range_m: float | None = 8.0,
    stable_frames: int = 5,
    balloon: bool = True,
) -> VisionEvent:
    body = BodyDetection(
        id=1,
        class_name=class_name,
        class_id=1,
        confidence=0.9,
        bbox=BBox(x=10, y=10, w=100, h=80),
        target_team=team,
        range_m=range_m,
        stable_frames=stable_frames,
    )
    balloons = [
        BalloonDetection(
            id=1,
            confidence=0.9,
            bbox=BBox(x=120, y=120, w=30, h=30),
            center_x=135,
            center_y=135,
        )
    ] if balloon else []
    return VisionEvent(
        frame_id=1,
        timestamp_ms=1,
        source="test",
        fps=15,
        preprocess_ms=1,
        inference_ms=1,
        postprocess_ms=1,
        total_latency_ms=3,
        body_detections=[body],
        balloon_detections=balloons,
    )


def evaluate(client: TestClient, event: VisionEvent | None):
    client.app.state.runtime.vision.latest_event = event
    return client.get("/api/decision/state").json()


def test_default_decision_no_fire(client: TestClient) -> None:
    decision = client.get("/api/decision/state").json()

    assert decision["fire_policy"] == "NO_FIRE_DEFAULT"
    assert "hardware_disabled" in decision["blocking_reasons"]


def test_no_target_no_target(client: TestClient) -> None:
    decision = evaluate(client, None)

    assert decision["decision_state"] == "NO_TARGET"
    assert "body_not_detected" in decision["blocking_reasons"]


def test_friend_target_no_fire(client: TestClient) -> None:
    decision = evaluate(client, make_event(team="friend"))

    assert decision["decision_state"] == "NO_FIRE"
    assert "target_is_friend" in decision["blocking_reasons"]
    assert decision["decision_reason"] == "NO_FIRE: target classified as friend."


def test_unknown_team_wait(client: TestClient) -> None:
    decision = evaluate(client, make_event(team="unknown"))

    assert decision["decision_state"] == "WAIT"
    assert "team_unknown" in decision["blocking_reasons"]


def test_enemy_no_balloon_rejected(client: TestClient) -> None:
    decision = evaluate(client, make_event(balloon=False))

    assert "balloon_not_detected" in decision["blocking_reasons"]


def test_enemy_invalid_range_rejected(client: TestClient) -> None:
    decision = evaluate(client, make_event(class_name="helicopter", range_m=20))

    assert "range_invalid" in decision["blocking_reasons"]


def test_f16_range_under_10_rejected(client: TestClient) -> None:
    decision = evaluate(client, make_event(class_name="f16", range_m=9.9))

    assert "range_invalid" in decision["blocking_reasons"]


def test_f16_range_10_15_pass(client: TestClient) -> None:
    decision = evaluate(client, make_event(class_name="f16", range_m=12))

    gate = next(g for g in decision["gates"] if g["name"] == "range_valid_gate")
    assert gate["status"] == "pass"


def test_helicopter_range_5_15_pass(client: TestClient) -> None:
    decision = evaluate(client, make_event(class_name="helicopter", range_m=5))
    gate = next(g for g in decision["gates"] if g["name"] == "range_valid_gate")
    assert gate["status"] == "pass"


def test_mini_micro_uav_range_0_15_pass(client: TestClient) -> None:
    decision = evaluate(client, make_event(class_name="mini_micro_uav", range_m=0))
    gate = next(g for g in decision["gates"] if g["name"] == "range_valid_gate")
    assert gate["status"] == "pass"


def test_stable_frames_missing_rejected(client: TestClient) -> None:
    decision = evaluate(client, make_event(stable_frames=2))

    assert "track_not_stable" in decision["blocking_reasons"]


def test_stable_frames_pass(client: TestClient) -> None:
    decision = evaluate(client, make_event(stable_frames=5))
    gate = next(g for g in decision["gates"] if g["name"] == "stable_track_gate")
    assert gate["status"] == "pass"


def test_forbidden_zone_disabled_not_applicable(client: TestClient) -> None:
    decision = evaluate(client, make_event())
    gate = next(g for g in decision["gates"] if g["name"] == "forbidden_zone_gate")
    assert gate["status"] == "not_applicable"


def test_arm_precondition_and_disarm(client: TestClient) -> None:
    arm = client.post("/api/safety/arm").json()
    assert arm["accepted"] is True
    assert arm["armed"] is True

    disarm = client.post("/api/safety/disarm").json()
    assert disarm["accepted"] is True
    assert disarm["armed"] is False


def test_fire_request_default_reject_and_no_command(client: TestClient) -> None:
    before = client.get("/api/serial/logs").json()
    response = client.post("/api/safety/fire-request", json={"operator_confirmed": True})
    after = client.get("/api/serial/logs").json()

    assert response.status_code == 403
    assert response.json()["accepted"] is False
    assert before == after


def test_websocket_decision_updated_smoke(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        messages = [websocket.receive_json() for _ in range(16)]

    assert "decision.updated" in {message["type"] for message in messages}
