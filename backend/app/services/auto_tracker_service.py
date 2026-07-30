"""
AutoTrackerService - kapali cevrim hedef takip servisi.

Bu servis her kamera frame'inde balon merkezini ekran merkezine gore
normalize eder ve hiz komutu uretir. Kontrol, yarim ekran hatasina gore
olceklenen sade bir PD'dir; integral bilerek kullanilmaz.
"""

from __future__ import annotations

import math
import time

from app.schemas.config import AppConfig
from app.schemas.log import LogLevel
from app.schemas.tracking import TrackingConfigUpdate, TrackingFireResult, TrackingState, TrackingStatus, TrackingUpdate
from app.services.multi_target_tracker_service import MultiTargetTrackerService
from app.schemas.vision import VisionEvent
from app.services.log_service import JsonlLogService


class AutoTrackerService:
    """
    Kapali cevrim takip kontrolcusu.

    Her frame'de ``update()`` çağrılır:
    1. VisionEvent'ten hedef secilir.
    2. Hedef yoksa motor komutu sifirlanir.
    3. Hata yarim ekran genisligi/yuksekligine gore normalize edilir.
    4. Normalize PD + smoothing + bbox olcekli kilit bolgesi uygulanir.
    5. Motor hiz komutu uretirilir.
    """

    def __init__(self, config: AppConfig, logger: JsonlLogService) -> None:
        self.config = config
        self.logger = logger

        # Kp/Kd artik normalize hata uzerinden hiz birimi uretir.
        # Ki arayuz uyumlulugu icin tutulur, hareket hesabinda kullanilmaz.
        tracking_config = config.tracking
        self.pid_kp_x: float = tracking_config.pid_kp_x
        self.pid_ki_x: float = tracking_config.pid_ki_x
        self.pid_kd_x: float = tracking_config.pid_kd_x
        self.pid_kp_y: float = tracking_config.pid_kp_y
        self.pid_ki_y: float = tracking_config.pid_ki_y
        self.pid_kd_y: float = tracking_config.pid_kd_y
        self.output_min: float = tracking_config.output_min
        self.output_max: float = tracking_config.output_max
        self.integral_max: float = tracking_config.integral_max

        # --- Smoothing & deadband ---
        self.smoothing_alpha: float = tracking_config.smoothing_alpha
        self.command_rate_hz: float = tracking_config.command_rate_hz
        self.max_speed: int = tracking_config.max_speed
        self.min_move_speed: float = tracking_config.min_move_speed
        self.deadband_lock_ratio: float = tracking_config.deadband_lock_ratio
        self.deadband_slow_ratio: float = tracking_config.deadband_slow_ratio
        self.deadband_medium_ratio: float = tracking_config.deadband_medium_ratio
        self.max_lost_frames: int = tracking_config.max_lost_frames
        self.aim_offset_x_px: float = tracking_config.aim_offset_x_px
        self.aim_offset_y_px: float = tracking_config.aim_offset_y_px
        self.invert_x: bool = tracking_config.invert_x
        self.invert_y: bool = tracking_config.invert_y
        self.lead_enabled: bool = tracking_config.lead_enabled
        self.lead_latency_multiplier: float = tracking_config.lead_latency_multiplier
        self.lead_max_horizon_ms: float = tracking_config.lead_max_horizon_ms

        # --- Internal state ---
        self._smooth_x: float = 0.0
        self._smooth_y: float = 0.0
        self._prev_norm_error_x: float = 0.0
        self._prev_norm_error_y: float = 0.0
        self._derivative_x: float = 0.0
        self._derivative_y: float = 0.0
        self._target_lost_frames: int = 0
        self._total_frames: int = 0
        self._target_count: int = 0
        self._lost_count: int = 0
        self._last_time: float = time.time()

        # --- Tracking lifecycle ---
        self.tracking_active: bool = False
        self._state: TrackingState = TrackingState.IDLE
        self._last_update: TrackingUpdate | None = None
        self._last_fire_result: TrackingFireResult | None = None
        self.preferred_target_x: float | None = None
        self.preferred_target_y: float | None = None
        self.multi_target_tracker = MultiTargetTrackerService()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_tracking(self) -> TrackingStatus:
        """Takibi başlat."""
        self.tracking_active = True
        self._state = TrackingState.SEARCHING
        self._reset_internals()
        self.multi_target_tracker.reset()
        self.logger.emit(LogLevel.INFO, "TRACKING", "Tracking started")
        return self.status()

    def stop_tracking(self) -> TrackingStatus:
        """Takibi durdur."""
        self.tracking_active = False
        self._state = TrackingState.STOPPED
        self._reset_control_state()
        self.logger.emit(LogLevel.INFO, "TRACKING", "Tracking stopped")
        return self.status()

    def status(self) -> TrackingStatus:
        """Mevcut takip durumunu döner."""
        return TrackingStatus(
            active=self.tracking_active,
            state=self._state,
            target_count=self._target_count,
            lost_count=self._lost_count,
            total_frames=self._total_frames,
            pid_kp_x=self.pid_kp_x,
            pid_ki_x=self.pid_ki_x,
            pid_kd_x=self.pid_kd_x,
            pid_kp_y=self.pid_kp_y,
            pid_ki_y=self.pid_ki_y,
            pid_kd_y=self.pid_kd_y,
            smoothing_alpha=self.smoothing_alpha,
            command_rate_hz=self.command_rate_hz,
            max_speed=self.max_speed,
            aim_offset_x_px=self.aim_offset_x_px,
            aim_offset_y_px=self.aim_offset_y_px,
            invert_x=self.invert_x,
            invert_y=self.invert_y,
            lead_enabled=self.lead_enabled,
            lead_latency_multiplier=self.lead_latency_multiplier,
            lead_max_horizon_ms=self.lead_max_horizon_ms,
            preferred_target_x=self.preferred_target_x,
            preferred_target_y=self.preferred_target_y,
            last_update=self._last_update,
            last_fire_result=self._last_fire_result,
            multi_target_tracker=self.multi_target_tracker.status(),
        )

    def update_config(self, update: TrackingConfigUpdate) -> TrackingStatus:
        """PID ve tracking parametrelerini güncelle (canlı)."""
        if update.pid_kp_x is not None:
            self.pid_kp_x = update.pid_kp_x
        if update.pid_ki_x is not None:
            self.pid_ki_x = update.pid_ki_x
        if update.pid_kd_x is not None:
            self.pid_kd_x = update.pid_kd_x
        if update.pid_kp_y is not None:
            self.pid_kp_y = update.pid_kp_y
        if update.pid_ki_y is not None:
            self.pid_ki_y = update.pid_ki_y
        if update.pid_kd_y is not None:
            self.pid_kd_y = update.pid_kd_y
        if update.smoothing_alpha is not None:
            self.smoothing_alpha = update.smoothing_alpha
        if update.command_rate_hz is not None:
            self.command_rate_hz = max(1.0, min(60.0, update.command_rate_hz))
        if update.max_speed is not None:
            self.max_speed = update.max_speed
        if update.min_move_speed is not None:
            self.min_move_speed = max(0.0, update.min_move_speed)
        if update.deadband_lock_ratio is not None:
            self.deadband_lock_ratio = max(0.0, update.deadband_lock_ratio)
        if update.deadband_slow_ratio is not None:
            self.deadband_slow_ratio = max(0.0, update.deadband_slow_ratio)
        if update.deadband_medium_ratio is not None:
            self.deadband_medium_ratio = max(0.0, update.deadband_medium_ratio)
        if update.aim_offset_x_px is not None:
            self.aim_offset_x_px = update.aim_offset_x_px
        if update.aim_offset_y_px is not None:
            self.aim_offset_y_px = update.aim_offset_y_px
        if update.invert_x is not None:
            self.invert_x = update.invert_x
        if update.invert_y is not None:
            self.invert_y = update.invert_y
        if update.lead_enabled is not None:
            self.lead_enabled = update.lead_enabled
        if update.lead_latency_multiplier is not None:
            self.lead_latency_multiplier = max(0.0, min(3.0, update.lead_latency_multiplier))
        if update.lead_max_horizon_ms is not None:
            self.lead_max_horizon_ms = max(0.0, min(300.0, update.lead_max_horizon_ms))
        if update.max_lost_frames is not None:
            self.max_lost_frames = update.max_lost_frames
        self.logger.emit(LogLevel.INFO, "TRACKING", "Tracking config updated", update.model_dump(mode="json", exclude_none=True))
        return self.status()

    def select_target(self, x: float, y: float, detection_id: int | None = None, frame_id: int | None = None) -> TrackingStatus:
        """Vision overlay üstünden seçilen balon merkezini takip önceliği yap."""
        self.preferred_target_x = x
        self.preferred_target_y = y
        self.logger.emit(
            LogLevel.INFO,
            "TRACKING",
            "Tracking target selected",
            {"x": x, "y": y, "detection_id": detection_id, "frame_id": frame_id},
        )
        return self.status()

    def record_fire_result(self, result) -> TrackingStatus:
        self._last_fire_result = TrackingFireResult(
            accepted=bool(result.accepted),
            command=result.command,
            reason_codes=list(result.reason_codes),
            detail=result.detail,
            physical_command_generated=bool(result.physical_command_generated),
        )
        return self.status()

    # ------------------------------------------------------------------
    # Ana takip döngüsü (her frame'de çağrılır)
    # ------------------------------------------------------------------

    def update(self, vision_event: VisionEvent | None, frame_width: int, frame_height: int) -> TrackingUpdate:
        """
        Tek frame guncelleme.

        Parameters
        ----------
        vision_event : Son VisionEvent (None ise hedef yok)
        frame_width  : Kamera çözünürlük genişliği
        frame_height : Kamera çözünürlük yüksekliği

        Returns
        -------
        TrackingUpdate : Motor hız komutu + telemetri
        """
        now = time.time()
        dt = now - self._last_time
        if dt <= 0:
            dt = 0.033  # Fallback 30 FPS
        self._last_time = now
        self._total_frames += 1

        frame_cx = frame_width / 2.0 + self.aim_offset_x_px
        frame_cy = frame_height / 2.0 + self.aim_offset_y_px
        frame_id = vision_event.frame_id if vision_event else 0

        if not self.tracking_active:
            self._last_update = TrackingUpdate(
                state=TrackingState.IDLE,
                frame_center_x=frame_cx, frame_center_y=frame_cy,
                aim_offset_x_px=self.aim_offset_x_px,
                aim_offset_y_px=self.aim_offset_y_px,
                frame_id=frame_id, dt=dt,
            )
            return self._last_update

        # Aşama 2 için kalıcı çoklu-track telemetrisi. Bu katman tek başına
        # motor/ateş seçimi yapmaz; fiziksel komut yine Gateway'den geçer.
        self.multi_target_tracker.update(vision_event)

        # ---- 1. Hedef sec ----
        target = self._select_target(vision_event, frame_cx, frame_cy)

        target_x: float
        target_y: float
        target_w: float = 0.0
        target_h: float = 0.0
        using_kalman = False
        lead_horizon_ms = 0.0
        predicted_target_x: float | None = None
        predicted_target_y: float | None = None

        if target is not None:
            target_x, target_y = target[0], target[1]
            target_w, target_h = target[2], target[3]
            if self.lead_enabled and vision_event is not None:
                lead_horizon_ms = self._lead_horizon_ms(vision_event)
                track = self._fresh_track_near(target_x, target_y)
                if track is not None and lead_horizon_ms > 0:
                    horizon_s = lead_horizon_ms / 1000.0
                    # Yeni ölçüm, kontrolün başlangıç noktasıdır. Kalman'ın
                    # düzeltilmiş merkezi özellikle yeni başlayan bir track'te
                    # son ölçümün gerisinde kalabilir; onu başlangıç alırsak
                    # ``lead`` etkin olduğu halde taret geçmiş konuma yönelir.
                    # Bu yüzden filtrelenmiş track yalnız hız kestirimi verir,
                    # konum ise bu frame'in taze ölçümünden ileri alınır.
                    predicted_target_x = max(0.0, min(float(frame_width), target_x + track.velocity_x * horizon_s))
                    predicted_target_y = max(0.0, min(float(frame_height), target_y + track.velocity_y * horizon_s))
                    target_x = predicted_target_x
                    target_y = predicted_target_y
                    using_kalman = True
            self._target_lost_frames = 0
            self._target_count += 1
            self._state = TrackingState.TRACKING
        else:
            self._target_lost_frames += 1
            self._lost_count += 1
            self._state = TrackingState.SEARCHING
            self._reset_control_state()
            self._last_update = TrackingUpdate(
                state=TrackingState.SEARCHING,
                frame_center_x=frame_cx, frame_center_y=frame_cy,
                aim_offset_x_px=self.aim_offset_x_px,
                aim_offset_y_px=self.aim_offset_y_px,
                frame_id=frame_id, dt=dt,
                target_lost_frames=self._target_lost_frames,
            )
            return self._last_update

        # ---- 2. Hata hesabi ----
        error_x = target_x - frame_cx
        error_y = target_y - frame_cy

        norm_x = error_x / max(frame_cx, 1.0)
        norm_y = error_y / max(frame_cy, 1.0)
        norm_x = max(-1.0, min(1.0, norm_x))
        norm_y = max(-1.0, min(1.0, norm_y))

        derivative_x = (norm_x - self._prev_norm_error_x) / max(dt, 0.001)
        derivative_y = (norm_y - self._prev_norm_error_y) / max(dt, 0.001)
        self._prev_norm_error_x = norm_x
        self._prev_norm_error_y = norm_y

        derivative_alpha = 0.35
        self._derivative_x = derivative_alpha * derivative_x + (1 - derivative_alpha) * self._derivative_x
        self._derivative_y = derivative_alpha * derivative_y + (1 - derivative_alpha) * self._derivative_y

        raw_x = self.pid_kp_x * norm_x + self.pid_kd_x * self._derivative_x
        raw_y = self.pid_kp_y * norm_y + self.pid_kd_y * self._derivative_y

        # ---- 3. Exponential smoothing ----
        alpha = max(0.0, min(1.0, self.smoothing_alpha))
        self._smooth_x = alpha * raw_x + (1 - alpha) * self._smooth_x
        self._smooth_y = alpha * raw_y + (1 - alpha) * self._smooth_y

        speed_x = self._smooth_x
        speed_y = self._smooth_y

        # ---- 4. Bbox olcekli kilit bolgesi ----
        distance_to_center = math.sqrt(error_x ** 2 + error_y ** 2)
        deadband_zone = "full"

        deadband_enabled = (
            self.deadband_lock_ratio > 0
            or self.deadband_slow_ratio > 0
            or self.deadband_medium_ratio > 0
        )

        if deadband_enabled and target_w > 0 and target_h > 0:
            target_radius = min(target_w, target_h) / 2.0
            lock_threshold = max(8.0, target_radius * self.deadband_lock_ratio)
            slow_threshold = max(lock_threshold + 1.0, target_radius * self.deadband_slow_ratio)
            medium_threshold = max(slow_threshold + 1.0, target_radius * self.deadband_medium_ratio)

            if distance_to_center <= lock_threshold:
                deadband_zone = "locked"
                speed_x = 0
                speed_y = 0
                self._smooth_x = 0.0
                self._smooth_y = 0.0
                self._state = TrackingState.LOCKED
            elif distance_to_center < slow_threshold:
                deadband_zone = "slow"
                speed_x *= 0.35
                speed_y *= 0.35
            elif distance_to_center < medium_threshold:
                deadband_zone = "medium"
                speed_x *= 0.70
                speed_y *= 0.70

        # ---- 5. Yon inversiyon ----
        if self.invert_x:
            speed_x *= -1
        if self.invert_y:
            speed_y *= -1

        # ---- 6. Minimum hareket telafisi ----
        min_speed = max(0.0, self.min_move_speed)
        if deadband_zone not in ("locked", "slow"):
            if 0 < abs(speed_x) < min_speed:
                speed_x = math.copysign(min_speed, speed_x)
            if 0 < abs(speed_y) < min_speed:
                speed_y = math.copysign(min_speed, speed_y)
        elif deadband_zone == "slow":
            if abs(error_x) < 5 or abs(speed_x) < min_speed * 0.35:
                speed_x = 0
            if abs(error_y) < 5 or abs(speed_y) < min_speed * 0.35:
                speed_y = 0

        # ---- 7. Clamp ----
        speed_x = max(-self.max_speed, min(self.max_speed, int(speed_x)))
        speed_y = max(-self.max_speed, min(self.max_speed, int(speed_y)))

        result = TrackingUpdate(
            state=self._state,
            speed_x=speed_x,
            speed_y=speed_y,
            error_x_px=error_x,
            error_y_px=error_y,
            raw_pid_x=raw_x,
            raw_pid_y=raw_y,
            target_center_x=target_x,
            target_center_y=target_y,
            frame_center_x=frame_cx,
            frame_center_y=frame_cy,
            aim_offset_x_px=self.aim_offset_x_px,
            aim_offset_y_px=self.aim_offset_y_px,
            target_lost_frames=self._target_lost_frames,
            distance_to_center=distance_to_center,
            deadband_zone=deadband_zone,
            using_kalman_prediction=using_kalman,
            lead_horizon_ms=round(lead_horizon_ms, 3),
            predicted_target_center_x=predicted_target_x,
            predicted_target_center_y=predicted_target_y,
            frame_id=frame_id,
            dt=dt,
        )
        self._last_update = result
        return result

    # ------------------------------------------------------------------
    # Hedef seçimi (eski select_target())
    # ------------------------------------------------------------------

    def _select_target(
        self,
        event: VisionEvent | None,
        center_x: float,
        center_y: float,
    ) -> tuple[float, float, float, float] | None:
        """
        En yakın balon bbox merkezini seç.

        Eski sistemdeki ``get_closest_target()`` fonksiyonunun karşılığı.
        Balon yoksa body detection kullanılır.

        Returns
        -------
        (center_x, center_y, width, height) veya None
        """
        if event is None:
            return None

        preferred_x = self.preferred_target_x if self.preferred_target_x is not None else center_x
        preferred_y = self.preferred_target_y if self.preferred_target_y is not None else center_y

        # Öncelik 1: Balon detection (seçili hedefe, yoksa merkeze en yakın)
        if event.balloon_detections:
            best = min(
                event.balloon_detections,
                key=lambda b: (b.center_x - preferred_x) ** 2 + (b.center_y - preferred_y) ** 2,
            )
            self.preferred_target_x = best.center_x
            self.preferred_target_y = best.center_y
            return (best.center_x, best.center_y, best.bbox.w, best.bbox.h)

        # Öncelik 2: Body detection (en yakın) — balon yoksa gövdeyi takip et
        if event.body_detections:
            best = min(
                event.body_detections,
                key=lambda b: (b.bbox.x + b.bbox.w / 2 - center_x) ** 2 + (b.bbox.y + b.bbox.h / 2 - center_y) ** 2,
            )
            cx = best.bbox.x + best.bbox.w / 2
            cy = best.bbox.y + best.bbox.h / 2
            return (cx, cy, best.bbox.w, best.bbox.h)

        return None

    def _lead_horizon_ms(self, event: VisionEvent) -> float:
        measured_latency = max(0.0, float(event.total_latency_ms or event.total_ms or 0.0))
        control_period = 1000.0 / max(1.0, self.command_rate_hz)
        return min(self.lead_max_horizon_ms, (measured_latency + control_period) * self.lead_latency_multiplier)

    def _fresh_track_near(self, x: float, y: float):
        fresh = [item for item in self.multi_target_tracker.status().tracks if item.fresh]
        if not fresh:
            return None
        return min(fresh, key=lambda item: (item.center_x - x) ** 2 + (item.center_y - y) ** 2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset_internals(self) -> None:
        """Tüm iç durumu sıfırla."""
        self._reset_control_state()
        self._target_lost_frames = 0
        self._total_frames = 0
        self._target_count = 0
        self._lost_count = 0
        self._last_fire_result = None
        self._last_time = time.time()

    def _reset_control_state(self) -> None:
        self._smooth_x = 0.0
        self._smooth_y = 0.0
        self._prev_norm_error_x = 0.0
        self._prev_norm_error_y = 0.0
        self._derivative_x = 0.0
        self._derivative_y = 0.0
