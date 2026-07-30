import time

from fastapi.testclient import TestClient

from app.schemas.vision import BBox, BodyDetection, BalloonDetection, VisionEvent


def _stage3_event() -> VisionEvent:
    return VisionEvent(
        frame_id=1, timestamp_ms=int(time.time() * 1000), source="stage3_readiness",
        frame_width=640, frame_height=360, fps=30, preprocess_ms=1, inference_ms=1, postprocess_ms=1, total_latency_ms=3,
        body_detections=[BodyDetection(id=1, class_name="f16", class_id=0, confidence=0.9, bbox=BBox(x=100, y=100, w=60, h=60), target_team="enemy", range_m=12)],
        balloon_detections=[BalloonDetection(id=1, confidence=0.9, bbox=BBox(x=120, y=120, w=30, h=30), center_x=135, center_y=135)],
    )


def test_stage3_decision_exposes_real_model_iff_and_range_reason_codes(client: TestClient) -> None:
    runtime = client.app.state.runtime
    assert client.put("/api/mission/status", json={"active_stage": "stage3"}).status_code == 200
    runtime.vision.latest_event = _stage3_event()

    decision = runtime.decision_engine.evaluate(runtime)

    assert "a3_body_model_missing_or_unverified" in decision.blocking_reasons
    assert "a3_iff_real_roi_unavailable" in decision.blocking_reasons
    assert "a3_range_calibration_unavailable" in decision.blocking_reasons
