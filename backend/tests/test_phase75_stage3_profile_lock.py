import time

from fastapi.testclient import TestClient

from app.schemas.vision import BBox, BalloonDetection, VisionEvent


def _fresh_event() -> VisionEvent:
    return VisionEvent(
        frame_id=1,
        timestamp_ms=int(time.time() * 1000),
        source="a3-profile-lock",
        frame_width=640,
        frame_height=360,
        fps=30,
        preprocess_ms=1,
        inference_ms=1,
        postprocess_ms=1,
        total_latency_ms=3,
        body_detections=[],
        balloon_detections=[BalloonDetection(id=1, confidence=0.9, bbox=BBox(x=300, y=160, w=30, h=30), center_x=315, center_y=175)],
    )


def test_stage3_competition_locks_color_range_camera_and_model_profile_mutations(client: TestClient) -> None:
    runtime = client.app.state.runtime
    runtime.vision.latest_event = _fresh_event()
    assert client.put("/api/mission/status", json={"active_stage": "stage3"}).status_code == 200
    # Profile selection is intentionally visible; readiness itself can still
    # be red until a real model/calibration exists.
    assert client.post("/api/safety/command-profile", json={"profile": "COMPETITION", "actuator_arm": True}).status_code == 200

    color = client.get("/api/color/config").json()
    settings = client.get("/api/vision/runtime/settings").json()
    assert client.put("/api/color/config", json=color).status_code == 409
    assert client.post("/api/stage3/range/observations", json={"class_name": "f16", "distance_m": 10, "bbox_height_px": 100, "capture_id": "should-block"}).status_code == 409
    assert client.post("/api/vision/runtime/apply-settings", json=settings).status_code == 409
    assert client.post("/api/camera/runtime/reset-defaults").status_code == 409
    assert "A3_PROFILE_LOCKED" in client.put("/api/color/config", json=color).text
