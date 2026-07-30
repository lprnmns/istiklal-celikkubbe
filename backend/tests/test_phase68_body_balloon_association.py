import time

from app.schemas.tracking import MultiTargetTrack, MultiTargetTrackingStatus
from app.schemas.vision import BBox, BodyDetection, VisionEvent
from app.services.body_balloon_association_service import BodyBalloonAssociationService


def _event(bodies: list[BodyDetection]) -> VisionEvent:
    return VisionEvent(
        frame_id=1, timestamp_ms=int(time.time() * 1000), source="association_test", frame_width=640, frame_height=360,
        fps=30, preprocess_ms=1, inference_ms=1, postprocess_ms=1, total_latency_ms=3,
        body_detections=bodies, balloon_detections=[],
    )


def _body(identifier: int, x: int, y: int) -> BodyDetection:
    return BodyDetection(id=identifier, class_name="target", class_id=0, confidence=0.9, bbox=BBox(x=x, y=y, w=40, h=40))


def _tracks(*positions: tuple[int, int]) -> MultiTargetTrackingStatus:
    return MultiTargetTrackingStatus(tracks=[
        MultiTargetTrack(track_id=index + 1, detection_id=index + 10, center_x=x, center_y=y, velocity_x=0, velocity_y=0, age_frames=3, hits=3, confidence=0.9, fresh=True)
        for index, (x, y) in enumerate(positions)
    ])


def test_association_becomes_stable_only_after_temporal_evidence() -> None:
    service = BodyBalloonAssociationService(stable_frames_required=3)
    event = _event([_body(101, 90, 90)])

    assert service.update(event, _tracks((110, 110))).associations[0].state == "tentative"
    assert service.update(event, _tracks((110, 110))).associations[0].state == "tentative"
    stable = service.update(event, _tracks((110, 110))).associations[0]
    assert stable.state == "stable"
    assert stable.body_detection_id == 101


def test_ambiguous_and_orphan_associations_never_become_stable() -> None:
    service = BodyBalloonAssociationService(max_distance_px=180, ambiguity_margin_px=30)
    ambiguous = service.update(_event([_body(1, 80, 90), _body(2, 120, 90)]), _tracks((120, 110)))
    orphan = service.update(_event([]), _tracks((120, 110)))

    assert ambiguous.associations[0].state == "ambiguous"
    assert orphan.associations[0].state == "orphan"


def test_balloon_outside_body_attachment_region_is_orphan() -> None:
    service = BodyBalloonAssociationService(max_distance_px=500)
    status = service.update(_event([_body(1, 20, 20)]), _tracks((400, 300)))

    assert status.associations[0].state == "orphan"
