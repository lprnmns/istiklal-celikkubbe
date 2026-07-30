from pathlib import Path

from fastapi.testclient import TestClient

from app.schemas.vision import BBox, BodyDetection, VisionEvent


def _vision_event(body_detections: list[BodyDetection]) -> VisionEvent:
    return VisionEvent(
        frame_id=34,
        timestamp_ms=1_779_530_000_000,
        source="person_safety_unit_fixture",
        fps=30.0,
        preprocess_ms=1.0,
        inference_ms=12.0,
        postprocess_ms=1.0,
        total_latency_ms=14.0,
        body_detections=body_detections,
        balloon_detections=[],
        warnings=["no_physical_command_generated=true"],
    )


def _body(class_name: str, confidence: float, detection_id: int = 1) -> BodyDetection:
    return BodyDetection(
        id=detection_id,
        class_name=class_name,
        class_id=detection_id,
        confidence=confidence,
        bbox=BBox(x=20, y=20, w=80, h=180),
        source="unit_fixture",
        stable_frames=6,
        target_team="unknown",
    )


def test_person_detection_blocks_fire_gate(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _vision_event([_body("person", 0.91)])

    response = client.get("/api/decision/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["person_safety"]["person_detected"] is True
    assert payload["person_safety"]["fire_gate_blocked_reason"] == "PERSON_DETECTED"
    assert "PERSON_DETECTED" in payload["blocking_reasons"]
    assert payload["decision_state"] == "NO_FIRE"


def test_no_person_detection_does_not_block_by_itself(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _vision_event([_body("f16", 0.91)])

    response = client.get("/api/decision/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["person_safety"]["person_detected"] is False
    assert "PERSON_DETECTED" not in payload["blocking_reasons"]


def test_low_confidence_person_below_threshold_does_not_block(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.config.person_safety.confidence_threshold = 0.8
    runtime.vision.latest_event = _vision_event([_body("insan", 0.42)])

    response = client.get("/api/decision/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["person_safety"]["person_detected"] is False
    assert "PERSON_DETECTED" not in payload["blocking_reasons"]


def test_stale_person_detection_clears_after_configured_timeout(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.config.person_safety.hold_ms = 100
    runtime.config.person_safety.clear_after_ms = 200
    event = _vision_event([_body("human", 0.93)])

    active = runtime.person_safety.evaluate(event, now_ms=1000)
    stale = runtime.person_safety.evaluate(_vision_event([]), now_ms=1301)

    assert active.person_detected is True
    assert active.fire_gate_blocked_reason == "PERSON_DETECTED"
    assert stale.person_detected is False
    assert stale.fire_gate_blocked_reason is None


def test_person_safety_endpoint_and_reports_use_canonical_wording(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _vision_event([_body("person", 0.88)])
    decision = client.get("/api/decision/state")
    status = client.get("/api/person-safety/status")

    assert decision.status_code == 200
    assert status.status_code == 200
    assert status.json()["no_physical_command_generated"] is True
    assert runtime.person_safety.last_event is not None
    assert runtime.person_safety.last_event[1]["no_physical_command_generated"] is True
    assert "no_physical_command_generated=true" in runtime.person_safety.last_event[1]["canonical_safety_wording"]

    root = Path(__file__).resolve().parents[2]
    report_paths = [
        root / "reports" / "person_safety_gate_summary.md",
        root / "reports" / "person_safety_gate_contract.json",
        root / "reports" / "safety_layered_architecture.md",
        root / "reports" / "ktr_autonomous_balloon_test_summary.md",
    ]
    for path in report_paths:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "no_physical_command_generated=true" in text
        assert "PERSON_DETECTED" in text
