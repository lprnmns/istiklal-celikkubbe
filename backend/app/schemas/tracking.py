"""
Tracking Pydantic Schemas — AutoTrackerService veri modelleri.
"""

from __future__ import annotations

import time
from enum import StrEnum

from pydantic import BaseModel, Field


class TrackingState(StrEnum):
    """Takip döngüsü durumları."""

    IDLE = "IDLE"                     # Takip kapalı
    SEARCHING = "SEARCHING"           # Hedef aranıyor
    TRACKING = "TRACKING"             # Aktif takip
    LOCKED = "LOCKED"                 # Hedef merkezde (deadband içinde)
    TARGET_LOST = "TARGET_LOST"       # Hedef kayboldu (Kalman tahmini devam)
    STOPPED = "STOPPED"               # Manuel durduruldu
    ERROR = "ERROR"                   # Hata durumu


class TrackingUpdate(BaseModel):
    """Her tracking frame'inde üretilen güncelleme."""

    state: TrackingState = TrackingState.IDLE
    speed_x: int = 0
    speed_y: int = 0
    error_x_px: float = 0.0
    error_y_px: float = 0.0
    raw_pid_x: float = 0.0
    raw_pid_y: float = 0.0
    target_center_x: float | None = None
    target_center_y: float | None = None
    frame_center_x: float = 0.0
    frame_center_y: float = 0.0
    aim_offset_x_px: float = 0.0
    aim_offset_y_px: float = 0.0
    target_lost_frames: int = 0
    distance_to_center: float = 0.0
    deadband_zone: str = "none"       # none / locked / slow / medium / full
    using_kalman_prediction: bool = False
    lead_horizon_ms: float = 0.0
    predicted_target_center_x: float | None = None
    predicted_target_center_y: float | None = None
    frame_id: int = 0
    dt: float = 0.0
    updated_at: float = Field(default_factory=time.time)


class TrackingFireResult(BaseModel):
    accepted: bool
    command: str = "FIRE"
    reason_codes: list[str] = Field(default_factory=list)
    detail: str
    physical_command_generated: bool = False
    updated_at: float = Field(default_factory=time.time)


class MultiTargetTrack(BaseModel):
    track_id: int
    detection_id: int | None = None
    center_x: float
    center_y: float
    velocity_x: float
    velocity_y: float
    age_frames: int = 0
    hits: int = 0
    misses: int = 0
    confidence: float = 0.0
    predicted: bool = False
    fresh: bool = False
    updated_at: float = Field(default_factory=time.time)


class MultiTargetTrackingStatus(BaseModel):
    tracker_kind: str = "kalman_nearest_neighbor"
    active_track_count: int = 0
    tracks: list[MultiTargetTrack] = Field(default_factory=list)
    updated_at: float = Field(default_factory=time.time)


class BodyBalloonAssociation(BaseModel):
    balloon_track_id: int
    body_detection_id: int | None = None
    body_track_id: int | None = None
    state: str  # stable / tentative / ambiguous / orphan
    distance_px: float | None = None
    confidence: float = 0.0
    stable_frames: int = 0
    attachment_region_ok: bool = False
    association_cost: float | None = None
    updated_at: float = Field(default_factory=time.time)


class AssociationStatus(BaseModel):
    associations: list[BodyBalloonAssociation] = Field(default_factory=list)
    stable_count: int = 0
    ambiguous_count: int = 0
    orphan_count: int = 0
    updated_at: float = Field(default_factory=time.time)


class TargetPriorityCandidate(BaseModel):
    balloon_track_id: int
    body_detection_id: int
    body_track_id: int | None = None
    score: float
    time_to_exit_s: float | None = None
    solution_quality: float
    return_cost: float
    reasons: list[str] = Field(default_factory=list)


class TargetPriorityStatus(BaseModel):
    selected_track_id: int | None = None
    ranked_candidates: list[TargetPriorityCandidate] = Field(default_factory=list)
    excluded_track_ids: list[int] = Field(default_factory=list)
    updated_at: float = Field(default_factory=time.time)


class EngagementState(StrEnum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED_HIT = "CONFIRMED_HIT"
    REENGAGE = "REENGAGE"


class EngagementOutcome(StrEnum):
    PENDING = "PENDING"
    HIT_CONFIRMED = "HIT_CONFIRMED"
    MISS_CONFIRMED = "MISS_CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"


class EngagementRecord(BaseModel):
    balloon_track_id: int
    body_detection_id: int | None = None
    body_track_id: int | None = None
    state: EngagementState
    shot_count: int = 1
    reason: str
    shot_at: float
    outcome: EngagementOutcome = EngagementOutcome.PENDING
    balloon_missing_frames: int = 0
    balloon_missing_since: float | None = None
    balloon_visible_after_grace: bool = False
    body_lost_during_confirmation: bool = False
    updated_at: float = Field(default_factory=time.time)


class EngagementStatus(BaseModel):
    records: list[EngagementRecord] = Field(default_factory=list)
    pending_count: int = 0
    confirmed_hit_count: int = 0
    reengage_count: int = 0
    updated_at: float = Field(default_factory=time.time)


class TrackingStatus(BaseModel):
    """Takip sistemi genel durumu."""

    active: bool = False
    state: TrackingState = TrackingState.IDLE
    target_count: int = 0
    lost_count: int = 0
    total_frames: int = 0
    pid_kp_x: float = 8.0
    pid_ki_x: float = 0.01
    pid_kd_x: float = 0.50
    pid_kp_y: float = 4.0
    pid_ki_y: float = 0.002
    pid_kd_y: float = 0.30
    smoothing_alpha: float = 0.5
    command_rate_hz: float = 83.0
    max_speed: int = 1000
    aim_offset_x_px: float = 0.0
    aim_offset_y_px: float = 0.0
    invert_x: bool = False
    invert_y: bool = False
    lead_enabled: bool = False
    lead_latency_multiplier: float = 1.0
    lead_max_horizon_ms: float = 120.0
    preferred_target_x: float | None = None
    preferred_target_y: float | None = None
    last_update: TrackingUpdate | None = None
    last_fire_result: TrackingFireResult | None = None
    multi_target_tracker: MultiTargetTrackingStatus = Field(default_factory=MultiTargetTrackingStatus)
    updated_at: float = Field(default_factory=time.time)


class TrackingConfigUpdate(BaseModel):
    """PID ve tracking parametrelerini güncellemek için."""

    pid_kp_x: float | None = None
    pid_ki_x: float | None = None
    pid_kd_x: float | None = None
    pid_kp_y: float | None = None
    pid_ki_y: float | None = None
    pid_kd_y: float | None = None
    smoothing_alpha: float | None = None
    command_rate_hz: float | None = None
    max_speed: int | None = None
    min_move_speed: float | None = None
    deadband_lock_ratio: float | None = None
    deadband_slow_ratio: float | None = None
    deadband_medium_ratio: float | None = None
    aim_offset_x_px: float | None = None
    aim_offset_y_px: float | None = None
    invert_x: bool | None = None
    invert_y: bool | None = None
    lead_enabled: bool | None = None
    lead_latency_multiplier: float | None = None
    lead_max_horizon_ms: float | None = None
    max_lost_frames: int | None = None


class TrackingTargetSelectRequest(BaseModel):
    """Vision overlay üzerinden seçilen takip hedefi."""

    x: float
    y: float
    detection_id: int | None = None
    frame_id: int | None = None
