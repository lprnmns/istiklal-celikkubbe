"""Deterministic multi-target tracking for Aşama 2 telemetry.

This service is intentionally perception/control only.  It produces stable
track identities and Kalman predictions, but does not emit motor or fire
commands.  CommandGateway remains the only physical-output boundary.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

from app.schemas.tracking import MultiTargetTrack, MultiTargetTrackingStatus
from app.schemas.vision import BalloonDetection, VisionEvent
from app.services.kalman_tracker import KalmanTracker


@dataclass
class _Track:
    track_id: int
    kalman: KalmanTracker
    center_x: float
    center_y: float
    velocity_x: float
    velocity_y: float
    detection_id: int | None
    confidence: float
    age_frames: int = 1
    hits: int = 1
    misses: int = 0
    updated_at: float = 0.0


class MultiTargetTrackerService:
    """Nearest-neighbour association over one constant-velocity Kalman per track."""

    def __init__(self, max_match_distance_px: float = 120.0, max_misses: int = 5) -> None:
        self.max_match_distance_px = max_match_distance_px
        self.max_misses = max_misses
        self._next_track_id = 1
        self._tracks: dict[int, _Track] = {}
        self._last_timestamp_s: float | None = None

    def reset(self) -> None:
        self._next_track_id = 1
        self._tracks.clear()
        self._last_timestamp_s = None

    def update(self, event: VisionEvent | None) -> MultiTargetTrackingStatus:
        now = time.time() if event is None else float(event.timestamp_ms) / 1000.0
        if self._last_timestamp_s is None:
            dt = 1 / 30.0
        else:
            dt = max(1 / 120.0, min(0.5, now - self._last_timestamp_s))
        self._last_timestamp_s = now

        predictions: dict[int, tuple[float, float]] = {}
        for track_id, track in self._tracks.items():
            track.kalman.dt = dt
            predictions[track_id] = track.kalman.predict() if track.kalman.initialized else (track.center_x, track.center_y)

        detections = list(event.balloon_detections) if event is not None else []
        matches = self._match(predictions, detections)
        matched_tracks = {track_id for track_id, _ in matches}
        matched_detections = {detection_index for _, detection_index in matches}

        for track_id, detection_index in matches:
            track = self._tracks[track_id]
            detection = detections[detection_index]
            previous_x, previous_y = track.center_x, track.center_y
            corrected_x, corrected_y = track.kalman.update(detection.center_x, detection.center_y)
            track.center_x, track.center_y = corrected_x, corrected_y
            track.velocity_x = (corrected_x - previous_x) / dt
            track.velocity_y = (corrected_y - previous_y) / dt
            track.detection_id = detection.id
            track.confidence = detection.confidence
            track.age_frames += 1
            track.hits += 1
            track.misses = 0
            track.updated_at = now

        for track_id, track in list(self._tracks.items()):
            if track_id in matched_tracks:
                continue
            predicted_x, predicted_y = predictions[track_id]
            track.center_x, track.center_y = predicted_x, predicted_y
            track.age_frames += 1
            track.misses += 1
            track.detection_id = None
            track.updated_at = now
            if track.misses > self.max_misses:
                del self._tracks[track_id]

        for detection_index, detection in enumerate(detections):
            if detection_index not in matched_detections:
                self._create_track(detection, now)

        return self.status()

    def status(self) -> MultiTargetTrackingStatus:
        tracks = [
            MultiTargetTrack(
                track_id=track.track_id,
                detection_id=track.detection_id,
                center_x=round(track.center_x, 3),
                center_y=round(track.center_y, 3),
                velocity_x=round(track.velocity_x, 3),
                velocity_y=round(track.velocity_y, 3),
                age_frames=track.age_frames,
                hits=track.hits,
                misses=track.misses,
                confidence=track.confidence,
                predicted=track.misses > 0,
                fresh=track.misses == 0,
                updated_at=track.updated_at,
            )
            for track in sorted(self._tracks.values(), key=lambda item: item.track_id)
        ]
        return MultiTargetTrackingStatus(
            tracker_kind="kalman_nearest_neighbor",
            active_track_count=len(tracks),
            tracks=tracks,
        )

    def _create_track(self, detection: BalloonDetection, timestamp_s: float) -> None:
        kalman = KalmanTracker()
        center_x, center_y = kalman.update(detection.center_x, detection.center_y)
        track_id = self._next_track_id
        self._next_track_id += 1
        self._tracks[track_id] = _Track(
            track_id=track_id,
            kalman=kalman,
            center_x=center_x,
            center_y=center_y,
            velocity_x=0.0,
            velocity_y=0.0,
            detection_id=detection.id,
            confidence=detection.confidence,
            updated_at=timestamp_s,
        )

    def _match(self, predictions: dict[int, tuple[float, float]], detections: list[BalloonDetection]) -> list[tuple[int, int]]:
        candidates: list[tuple[float, int, int]] = []
        for track_id, (x, y) in predictions.items():
            for detection_index, detection in enumerate(detections):
                distance = math.hypot(detection.center_x - x, detection.center_y - y)
                if distance <= self.max_match_distance_px:
                    candidates.append((distance, track_id, detection_index))
        matches: list[tuple[int, int]] = []
        used_tracks: set[int] = set()
        used_detections: set[int] = set()
        for _, track_id, detection_index in sorted(candidates):
            if track_id not in used_tracks and detection_index not in used_detections:
                matches.append((track_id, detection_index))
                used_tracks.add(track_id)
                used_detections.add(detection_index)
        return matches
