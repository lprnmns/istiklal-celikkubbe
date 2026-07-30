import time

from app.schemas.vision import BBox, BalloonDetection, VisionEvent
from app.services.multi_target_tracker_service import MultiTargetTrackerService


def _event(frame_id: int, positions: list[tuple[int, int]], timestamp_ms: int | None = None) -> VisionEvent:
    balloons = [
        BalloonDetection(
            id=index + 10,
            confidence=0.95,
            bbox=BBox(x=x - 15, y=y - 15, w=30, h=30),
            center_x=x,
            center_y=y,
            source="multi_track_test",
        )
        for index, (x, y) in enumerate(positions)
    ]
    return VisionEvent(
        frame_id=frame_id,
        timestamp_ms=timestamp_ms if timestamp_ms is not None else int(time.time() * 1000) + frame_id * 33,
        source="multi_track_test",
        frame_width=640,
        frame_height=360,
        fps=30,
        preprocess_ms=1,
        inference_ms=1,
        postprocess_ms=1,
        total_latency_ms=3,
        body_detections=[],
        balloon_detections=balloons,
    )


def test_three_targets_keep_stable_track_ids_when_detection_order_changes() -> None:
    tracker = MultiTargetTrackerService(max_match_distance_px=80, max_misses=2)
    first = tracker.update(_event(1, [(100, 100), (300, 120), (500, 140)]))
    assert first.active_track_count == 3
    original_ids = [track.track_id for track in first.tracks]

    second = tracker.update(_event(2, [(505, 140), (105, 100), (295, 120)]))

    assert second.active_track_count == 3
    assert [track.track_id for track in second.tracks] == original_ids
    assert all(track.hits == 2 and track.misses == 0 for track in second.tracks)


def test_short_occlusion_is_predicted_then_track_expires_after_miss_budget() -> None:
    tracker = MultiTargetTrackerService(max_match_distance_px=80, max_misses=2)
    tracker.update(_event(1, [(100, 100)]))

    predicted = tracker.update(_event(2, []))
    assert predicted.active_track_count == 1
    assert predicted.tracks[0].predicted is True
    assert predicted.tracks[0].misses == 1

    tracker.update(_event(3, []))
    expired = tracker.update(_event(4, []))
    assert expired.active_track_count == 0
