"""Small, deterministic body tracker used only for perception evidence.

It owns no actuator and emits no command.  Its purpose is to stop a frame
local YOLO detection id being mistaken for temporal IFF continuity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.schemas.vision import BodyDetection


@dataclass
class _BodyTrack:
    track_id: int
    class_name: str
    center_x: float
    center_y: float
    stable_frames: int = 1
    misses: int = 0


class BodyTrackerService:
    def __init__(self, max_match_distance_px: float = 140.0, max_misses: int = 3) -> None:
        self.max_match_distance_px = max_match_distance_px
        self.max_misses = max_misses
        self._next_track_id = 1
        self._tracks: dict[int, _BodyTrack] = {}

    def reset(self) -> None:
        self._next_track_id = 1
        self._tracks.clear()

    def update(self, bodies: list[BodyDetection]) -> list[BodyDetection]:
        candidates: list[tuple[float, int, int]] = []
        for track_id, track in self._tracks.items():
            for detection_index, body in enumerate(bodies):
                # A class switch is not temporal evidence.  It must begin a
                # new track rather than inheriting a previous IFF decision.
                if body.class_name != track.class_name:
                    continue
                center_x = body.bbox.x + body.bbox.w / 2
                center_y = body.bbox.y + body.bbox.h / 2
                distance = math.hypot(center_x - track.center_x, center_y - track.center_y)
                if distance <= self.max_match_distance_px:
                    candidates.append((distance, track_id, detection_index))

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()
        updates: dict[int, BodyDetection] = {}
        for _, track_id, detection_index in sorted(candidates):
            if track_id in matched_tracks or detection_index in matched_detections:
                continue
            track = self._tracks[track_id]
            body = bodies[detection_index]
            center_x = body.bbox.x + body.bbox.w / 2
            center_y = body.bbox.y + body.bbox.h / 2
            track.center_x = center_x
            track.center_y = center_y
            track.stable_frames += 1
            track.misses = 0
            matched_tracks.add(track_id)
            matched_detections.add(detection_index)
            updates[detection_index] = body.model_copy(update={"track_id": track_id, "stable_frames": track.stable_frames})

        for track_id, track in list(self._tracks.items()):
            if track_id in matched_tracks:
                continue
            track.misses += 1
            if track.misses > self.max_misses:
                del self._tracks[track_id]

        for detection_index, body in enumerate(bodies):
            if detection_index in matched_detections:
                continue
            center_x = body.bbox.x + body.bbox.w / 2
            center_y = body.bbox.y + body.bbox.h / 2
            track_id = self._next_track_id
            self._next_track_id += 1
            self._tracks[track_id] = _BodyTrack(
                track_id=track_id,
                class_name=body.class_name,
                center_x=center_x,
                center_y=center_y,
            )
            updates[detection_index] = body.model_copy(update={"track_id": track_id, "stable_frames": 1})
        return [updates[index] for index in range(len(bodies))]
