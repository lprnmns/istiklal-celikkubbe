"""Fail-closed, telemetry-only generic body–balloon association."""

from __future__ import annotations

import math
import time

from app.schemas.tracking import AssociationStatus, BodyBalloonAssociation, MultiTargetTrackingStatus
from app.schemas.vision import BodyDetection, VisionEvent


class BodyBalloonAssociationService:
    def __init__(self, max_distance_px: float = 180.0, ambiguity_margin_px: float = 24.0, stable_frames_required: int = 3) -> None:
        self.max_distance_px = max_distance_px
        self.ambiguity_margin_px = ambiguity_margin_px
        self.stable_frames_required = stable_frames_required
        self._previous_body_by_track: dict[int, int] = {}
        self._stable_frames_by_track: dict[int, int] = {}
        self._status = AssociationStatus()

    def reset(self) -> None:
        self._previous_body_by_track.clear()
        self._stable_frames_by_track.clear()
        self._status = AssociationStatus()

    def update(self, event: VisionEvent | None, tracks: MultiTargetTrackingStatus) -> AssociationStatus:
        now = time.time() if event is None else float(event.timestamp_ms) / 1000.0
        bodies = list(event.body_detections) if event is not None else []
        associations: list[BodyBalloonAssociation] = []
        active_track_ids = {track.track_id for track in tracks.tracks}
        for track_id in list(self._previous_body_by_track):
            if track_id not in active_track_ids:
                self._previous_body_by_track.pop(track_id, None)
                self._stable_frames_by_track.pop(track_id, None)

        candidates: list[tuple[float, int, BodyDetection, int, bool]] = []
        ambiguous_tracks: set[int] = set()
        for track in tracks.tracks:
            if not track.fresh:
                associations.append(BodyBalloonAssociation(balloon_track_id=track.track_id, state="orphan", stable_frames=0, updated_at=now))
                continue
            distances = sorted(
                (
                    (self._distance(track.center_x, track.center_y, body), body, self._body_key(body), self._inside_attachment_region(track.center_x, track.center_y, body))
                    for body in bodies
                    if self._inside_attachment_region(track.center_x, track.center_y, body)
                ),
                key=lambda item: (item[0], item[1].id),
            )
            if not distances or distances[0][0] > self.max_distance_px:
                self._clear_track(track.track_id)
                associations.append(BodyBalloonAssociation(balloon_track_id=track.track_id, state="orphan", stable_frames=0, updated_at=now))
                continue
            if len(distances) > 1 and distances[1][0] - distances[0][0] <= self.ambiguity_margin_px:
                ambiguous_tracks.add(track.track_id)
                self._clear_track(track.track_id)
                associations.append(BodyBalloonAssociation(balloon_track_id=track.track_id, state="ambiguous", distance_px=round(distances[0][0], 3), updated_at=now))
                continue
            candidates.append((distances[0][0], track.track_id, distances[0][1], distances[0][2], distances[0][3]))

        used_bodies: set[int] = set()
        for distance, track_id, body, body_key, attachment_region_ok in sorted(candidates):
            if track_id in ambiguous_tracks:
                continue
            if body_key in used_bodies:
                self._clear_track(track_id)
                associations.append(BodyBalloonAssociation(balloon_track_id=track_id, state="ambiguous", distance_px=round(distance, 3), updated_at=now))
                continue
            used_bodies.add(body_key)
            if self._previous_body_by_track.get(track_id) == body_key:
                stable_frames = self._stable_frames_by_track.get(track_id, 0) + 1
            else:
                stable_frames = 1
            self._previous_body_by_track[track_id] = body_key
            self._stable_frames_by_track[track_id] = stable_frames
            state = "stable" if stable_frames >= self.stable_frames_required else "tentative"
            confidence = max(0.0, min(1.0, 1.0 - distance / self.max_distance_px))
            associations.append(
                BodyBalloonAssociation(
                    balloon_track_id=track_id,
                    body_detection_id=body.id,
                    body_track_id=body.track_id,
                    state=state,
                    distance_px=round(distance, 3),
                    confidence=round(confidence, 4),
                    stable_frames=stable_frames,
                    attachment_region_ok=attachment_region_ok,
                    association_cost=round(distance / self.max_distance_px, 4),
                    updated_at=now,
                )
            )

        self._status = AssociationStatus(
            associations=sorted(associations, key=lambda item: item.balloon_track_id),
            stable_count=sum(item.state == "stable" for item in associations),
            ambiguous_count=sum(item.state == "ambiguous" for item in associations),
            orphan_count=sum(item.state == "orphan" for item in associations),
            updated_at=now,
        )
        return self._status

    def status(self) -> AssociationStatus:
        return self._status

    def _clear_track(self, track_id: int) -> None:
        self._previous_body_by_track.pop(track_id, None)
        self._stable_frames_by_track.pop(track_id, None)

    @staticmethod
    def _distance(x: float, y: float, body: BodyDetection) -> float:
        center_x = body.bbox.x + body.bbox.w / 2
        center_y = body.bbox.y + body.bbox.h / 2
        return math.hypot(x - center_x, y - center_y)

    @staticmethod
    def _body_key(body: BodyDetection) -> int:
        return body.track_id if body.track_id is not None else body.id

    @staticmethod
    def _inside_attachment_region(x: float, y: float, body: BodyDetection) -> bool:
        """Balloon must be in/near the body-specific visual attachment region.

        The region is deliberately generous before the final YOLO geometry
        calibration: a target's balloon may sit above, beside, or partially
        outside its body bbox.  It still rejects an unrelated distant balloon
        that happened to be the nearest detection.
        """
        bbox = body.bbox
        left = bbox.x - bbox.w
        right = bbox.x + bbox.w * 2
        top = bbox.y - bbox.h * 1.5
        bottom = bbox.y + bbox.h * 1.5
        return left <= x <= right and top <= y <= bottom
