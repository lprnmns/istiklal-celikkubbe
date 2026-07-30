from app.schemas.tracking import AssociationStatus, BodyBalloonAssociation, MultiTargetTrack, MultiTargetTrackingStatus
from app.services.target_priority_service import TargetPriorityService


def _track(track_id: int, x: float, y: float, vx: float, vy: float, confidence: float = 0.9) -> MultiTargetTrack:
    return MultiTargetTrack(track_id=track_id, detection_id=track_id, center_x=x, center_y=y, velocity_x=vx, velocity_y=vy, age_frames=5, hits=5, confidence=confidence, fresh=True)


def test_earlier_exit_stable_target_has_priority_over_slower_target() -> None:
    service = TargetPriorityService()
    tracks = MultiTargetTrackingStatus(tracks=[_track(1, 600, 180, 100, 0), _track(2, 320, 180, 5, 0)])
    associations = AssociationStatus(associations=[
        BodyBalloonAssociation(balloon_track_id=1, body_detection_id=101, state="stable", stable_frames=4),
        BodyBalloonAssociation(balloon_track_id=2, body_detection_id=102, state="stable", stable_frames=4),
    ])

    status = service.update(tracks, associations, 640, 360, 320, 180)

    assert status.selected_track_id == 1
    assert [candidate.balloon_track_id for candidate in status.ranked_candidates] == [1, 2]


def test_ambiguous_or_orphan_tracks_are_excluded_from_priority() -> None:
    service = TargetPriorityService()
    tracks = MultiTargetTrackingStatus(tracks=[_track(1, 600, 180, 100, 0), _track(2, 320, 180, 5, 0)])
    associations = AssociationStatus(associations=[
        BodyBalloonAssociation(balloon_track_id=1, body_detection_id=101, state="ambiguous"),
        BodyBalloonAssociation(balloon_track_id=2, body_detection_id=None, state="orphan"),
    ])

    status = service.update(tracks, associations, 640, 360, 320, 180)

    assert status.selected_track_id is None
    assert status.ranked_candidates == []
    assert status.excluded_track_ids == [1, 2]


def test_stage3_priority_can_exclude_stable_friend_links() -> None:
    service = TargetPriorityService()
    tracks = MultiTargetTrackingStatus(tracks=[_track(1, 600, 180, 100, 0), _track(2, 320, 180, 5, 0)])
    associations = AssociationStatus(associations=[
        BodyBalloonAssociation(balloon_track_id=1, body_detection_id=101, state="stable", stable_frames=4),
        BodyBalloonAssociation(balloon_track_id=2, body_detection_id=102, state="stable", stable_frames=4),
    ])

    status = service.update(tracks, associations, 640, 360, 320, 180, allowed_body_detection_ids={102})

    assert status.selected_track_id == 2
    assert [candidate.balloon_track_id for candidate in status.ranked_candidates] == [2]
    assert status.excluded_track_ids == [1]
