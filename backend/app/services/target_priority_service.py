"""Telemetry-only Aşama 2 target priority over stable associations."""

from __future__ import annotations

import math
import time

from app.schemas.tracking import AssociationStatus, MultiTargetTrackingStatus, TargetPriorityCandidate, TargetPriorityStatus


class TargetPriorityService:
    def __init__(self, hysteresis_bonus: float = 0.08) -> None:
        self.hysteresis_bonus = hysteresis_bonus
        self._selected_track_id: int | None = None
        self._status = TargetPriorityStatus()

    def reset(self) -> None:
        self._selected_track_id = None
        self._status = TargetPriorityStatus()

    def update(
        self,
        tracks: MultiTargetTrackingStatus,
        associations: AssociationStatus,
        frame_width: int,
        frame_height: int,
        aim_x: float,
        aim_y: float,
        allowed_body_detection_ids: set[int] | None = None,
    ) -> TargetPriorityStatus:
        association_by_track = {item.balloon_track_id: item for item in associations.associations}
        candidates: list[TargetPriorityCandidate] = []
        excluded: list[int] = []
        diagonal = max(1.0, math.hypot(frame_width, frame_height))
        for track in tracks.tracks:
            association = association_by_track.get(track.track_id)
            if association is None or association.state != "stable" or association.body_detection_id is None or not track.fresh:
                excluded.append(track.track_id)
                continue
            if allowed_body_detection_ids is not None and association.body_detection_id not in allowed_body_detection_ids:
                excluded.append(track.track_id)
                continue
            distance = math.hypot(track.center_x - aim_x, track.center_y - aim_y)
            return_cost = min(1.0, distance / diagonal)
            solution_quality = max(0.0, min(1.0, track.confidence * (1.0 - return_cost)))
            time_to_exit = self._time_to_exit(track.center_x, track.center_y, track.velocity_x, track.velocity_y, frame_width, frame_height)
            exit_urgency = 0.0 if time_to_exit is None else max(0.0, min(1.0, 1.0 / max(time_to_exit, 0.25)))
            score = 0.52 * exit_urgency + 0.38 * solution_quality - 0.24 * return_cost
            reasons = [f"exit={time_to_exit:.2f}s" if time_to_exit is not None else "exit=unknown", f"solution={solution_quality:.3f}"]
            if track.track_id == self._selected_track_id:
                score += self.hysteresis_bonus
                reasons.append("hysteresis_bonus")
            candidates.append(
                TargetPriorityCandidate(
                    balloon_track_id=track.track_id,
                    body_detection_id=association.body_detection_id,
                    body_track_id=association.body_track_id,
                    score=round(score, 5),
                    time_to_exit_s=None if time_to_exit is None else round(time_to_exit, 4),
                    solution_quality=round(solution_quality, 5),
                    return_cost=round(return_cost, 5),
                    reasons=reasons,
                )
            )
        ranked = sorted(candidates, key=lambda item: (-item.score, item.balloon_track_id))
        self._selected_track_id = ranked[0].balloon_track_id if ranked else None
        self._status = TargetPriorityStatus(
            selected_track_id=self._selected_track_id,
            ranked_candidates=ranked,
            excluded_track_ids=sorted(excluded),
            updated_at=time.time(),
        )
        return self._status

    def status(self) -> TargetPriorityStatus:
        return self._status

    @staticmethod
    def _time_to_exit(x: float, y: float, vx: float, vy: float, width: int, height: int) -> float | None:
        times: list[float] = []
        if vx > 0:
            times.append((width - x) / vx)
        elif vx < 0:
            times.append((0 - x) / vx)
        if vy > 0:
            times.append((height - y) / vy)
        elif vy < 0:
            times.append((0 - y) / vy)
        valid = [value for value in times if value >= 0]
        return min(valid) if valid else None
