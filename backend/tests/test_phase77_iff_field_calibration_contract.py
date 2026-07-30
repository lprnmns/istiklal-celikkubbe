import numpy as np

from fastapi.testclient import TestClient

from app.schemas.color import ColorCalibrationReferenceRequest, ColorClassifySampleRequest, TeamValue
from app.schemas.vision import BBox, BodyDetection


def _body(track_id: int) -> BodyDetection:
    return BodyDetection(
        id=track_id,
        track_id=track_id,
        class_name="f16",
        class_id=0,
        confidence=0.9,
        bbox=BBox(x=10, y=10, w=60, h=60),
    )


def _frame(bgr: tuple[int, int, int]):
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[10:70, 10:70] = bgr
    return frame


def test_stage3_iff_requires_real_field_references_and_invalidates_when_profile_changes(client: TestClient) -> None:
    classifier = client.app.state.runtime.color_classifier
    enemy = _body(1)
    for frame_id in range(1, 6):
        enemy = classifier.classify_frame_bodies(_frame((0, 0, 255)), frame_id, [enemy], [])[0]
        if frame_id >= 3:
            classifier.record_calibration_reference(
                ColorCalibrationReferenceRequest(expected_team=TeamValue.ENEMY, capture_id=f"enemy-{frame_id}")
            )

    ready, detail = classifier.real_iff_ready_for(enemy, frame_id=5)
    assert ready is False
    assert "A3_IFF_FRIEND_REFERENCE_INSUFFICIENT" in detail

    friend = _body(2)
    for frame_id in range(6, 9):
        friend = classifier.classify_frame_bodies(_frame((255, 0, 0)), frame_id, [friend], [])[0]
        classifier.record_calibration_reference(
            ColorCalibrationReferenceRequest(expected_team=TeamValue.FRIEND, capture_id=f"friend-{frame_id}")
        )

    status = classifier.calibration_status()
    assert status.valid is True
    enemy = classifier.classify_frame_bodies(_frame((0, 0, 255)), 9, [enemy], [])[0]
    ready, detail = classifier.real_iff_ready_for(enemy, frame_id=9)
    assert ready is True
    assert "current" in detail

    next_config = classifier.get_config().model_copy(update={"decision_threshold": 0.6})
    classifier.update_config(next_config)
    invalidated = classifier.calibration_status()
    assert invalidated.valid is False
    assert "A3_IFF_ENEMY_REFERENCE_INSUFFICIENT" in invalidated.reason_codes


def test_mock_color_sample_cannot_be_registered_as_iff_field_reference(client: TestClient) -> None:
    classifier = client.app.state.runtime.color_classifier
    classifier.classify_sample(
        ColorClassifySampleRequest(
            frame_id=1,
            detection_id=1,
            mock_team=TeamValue.ENEMY,
            balloon_bbox_present=True,
            body_pixel_count=500,
        )
    )
    try:
        classifier.record_calibration_reference(
            ColorCalibrationReferenceRequest(expected_team=TeamValue.ENEMY, capture_id="mock-is-not-iff")
        )
    except ValueError as exc:
        assert str(exc) == "A3_IFF_REAL_ROI_EVIDENCE_REQUIRED"
    else:  # pragma: no cover
        raise AssertionError("mock sample became field calibration evidence")
