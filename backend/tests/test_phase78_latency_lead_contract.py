import time

from fastapi.testclient import TestClient

from app.schemas.tracking import TrackingConfigUpdate
from app.schemas.vision import BBox, BalloonDetection, VisionEvent


def _event(frame_id: int, timestamp_ms: int, x: int, latency_ms: float = 80.0) -> VisionEvent:
    balloon = BalloonDetection(
        id=1,
        confidence=0.95,
        bbox=BBox(x=x - 15, y=165, w=30, h=30),
        center_x=x,
        center_y=180,
    )
    return VisionEvent(
        frame_id=frame_id,
        timestamp_ms=timestamp_ms,
        source="latency-lead-contract",
        frame_width=640,
        frame_height=360,
        fps=30,
        preprocess_ms=1,
        inference_ms=latency_ms,
        postprocess_ms=1,
        total_latency_ms=latency_ms,
        body_detections=[],
        balloon_detections=[balloon],
    )


def test_measured_latency_lead_is_visible_bounded_and_disabled_by_default(client: TestClient) -> None:
    tracker = client.app.state.runtime.auto_tracker
    now_ms = int(time.time() * 1000)
    tracker.start_tracking()
    tracker.update(_event(1, now_ms, 200), 640, 360)
    baseline = tracker.update(_event(2, now_ms + 100, 230), 640, 360)

    assert baseline.using_kalman_prediction is False
    assert baseline.target_center_x == 230
    assert baseline.lead_horizon_ms == 0

    tracker.update_config(TrackingConfigUpdate(lead_enabled=True, lead_latency_multiplier=1.0, lead_max_horizon_ms=120))
    led = tracker.update(_event(3, now_ms + 200, 260), 640, 360)

    assert led.using_kalman_prediction is True
    assert 0 < led.lead_horizon_ms <= 120
    assert led.predicted_target_center_x is not None
    assert led.target_center_x == led.predicted_target_center_x
    assert led.target_center_x >= 260

    tracker.update_config(TrackingConfigUpdate(lead_enabled=False))
    disabled = tracker.update(_event(4, now_ms + 300, 290), 640, 360)
    assert disabled.using_kalman_prediction is False
    assert disabled.target_center_x == 290
