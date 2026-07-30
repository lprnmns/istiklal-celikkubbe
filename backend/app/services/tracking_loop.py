"""
TrackingLoop — Bağımsız asyncio.Task olarak çalışan kapalı çevrim takip döngüsü.

WebSocket'in 200ms döngüsünden bağımsız, ~50-83Hz (12-20ms) interval ile çalışır.
Vision → AutoTracker → Serial motor komutu zincirini yönetir.

Eski sistemde bu döngü ``main.py.process_step()`` içinde senkron olarak çalışıyordu.
Yeni sistemde asyncio task olarak çalışarak backend event loop'u bloklamaz.
"""

from __future__ import annotations

import asyncio
import math
import time

from app.schemas.log import LogLevel
from app.schemas.tracking import TrackingState, TrackingUpdate
from app.services.auto_tracker_service import AutoTrackerService
from app.services.command_gateway import CommandGateway
from app.services.log_service import JsonlLogService
from app.services.safety_timing import MAX_VISION_EVENT_AGE_S
from app.services.serial_service import SerialService
from app.services.vision_pipeline import VisionPipeline

FIRE_ZONE_RADIUS_RATIO = 0.25
# TrackingLoop fiziksel ateş yetkisine sahip değildir. Bu eşik yalnız
# CommandGateway'e ileride verilecek dry-run fire-adayı telemetrisi içindir.
FIRE_REQUIRED_FRAMES = 3


class TrackingLoop:
    """
    Kapalı çevrim takip döngüsü.

    Lifecycle:
        loop = TrackingLoop(...)
        await loop.start()    # asyncio.Task başlatır
        ...
        await loop.stop()     # Task'ı durdurur

    Her iterasyonda:
        1. VisionPipeline'dan son frame al
        2. AutoTrackerService.update() ile PID hesapla
    3. CommandGateway ile preflight sonrası Pico'ya hız komutu gönder
    """

    def __init__(
        self,
        auto_tracker: AutoTrackerService,
        vision_pipeline: VisionPipeline,
        serial: SerialService,
        gateway: CommandGateway,
        logger: JsonlLogService,
        frame_width: int = 1920,
        frame_height: int = 1080,
        interval_ms: float = 12.0,
        tuning=None,
    ) -> None:
        self.auto_tracker = auto_tracker
        self.vision_pipeline = vision_pipeline
        self.serial = serial
        self.gateway = gateway
        self.logger = logger
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.interval_s = interval_ms / 1000.0
        self.tuning = tuning
        self._task: asyncio.Task | None = None
        self._running = False
        self.last_update: TrackingUpdate | None = None
        self.loop_count = 0
        self.errors = 0
        self.fire_target_frames = 0
        self.is_firing = False
        self._fire_candidate_active = False
        self._last_stale_vision_log_at = 0.0
        self._last_speed_sent_at = 0.0
        self._last_speed_sent: tuple[int, int] | None = None
        self._target_loss_safed = False
        self._events: list[tuple[str, dict]] = []

    async def start(self) -> None:
        """Tracking döngüsünü başlat."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        self.logger.emit(LogLevel.INFO, "TRACKING_LOOP", "Tracking loop started", {"interval_ms": self.interval_s * 1000})

    async def stop(self) -> None:
        """Tracking döngüsünü durdur ve motorları güvenli şekilde durdur."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self.gateway.runtime is not None:
            self.gateway.serial.gateway_safe_stop()
            self.gateway.driver_enabled = False
            self.gateway.actuator_armed = False
        self.is_firing = False
        self._reset_fire_candidate()
        self.logger.emit(LogLevel.INFO, "TRACKING_LOOP", "Tracking loop stopped", {"total_loops": self.loop_count})

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    def drain_events(self) -> list[tuple[str, dict]]:
        events = self._events
        self._events = []
        return events

    async def _run(self) -> None:
        """Ana tracking döngüsü."""
        while self._running:
            try:
                t0 = time.time()
                if self.gateway.runtime is not None:
                    self.gateway.tick(self.gateway.runtime)

                # Tracker aktif değilse bekle
                if not self.auto_tracker.tracking_active:
                    await asyncio.sleep(0.1)
                    continue

                # 1. Son vision event'i al
                vision_event = self.vision_pipeline.latest()
                frame_width, frame_height = self._frame_size()
                if not self._vision_event_is_fresh(vision_event):
                    self._handle_stale_vision(vision_event)
                    vision_event = None

                # 2. Tracker'ı güncelle
                update = self.auto_tracker.update(
                    vision_event,
                    frame_width=frame_width,
                    frame_height=frame_height,
                )
                self.last_update = update
                if self.tuning is not None:
                    self.tuning.observe(update)
                if self.gateway.runtime is not None:
                    runtime = self.gateway.runtime
                    tracks = self.auto_tracker.status().multi_target_tracker
                    associations = runtime.association.update(vision_event, tracks)
                    runtime.target_priority.update(
                        tracks,
                        associations,
                        frame_width,
                        frame_height,
                        update.frame_center_x,
                        update.frame_center_y,
                        allowed_body_detection_ids=(
                            {body.id for body in vision_event.body_detections if body.target_team == "enemy"}
                            if self.gateway.profile.value == "COMPETITION"
                            and runtime.mission.state.active_stage == "stage3"
                            and vision_event is not None
                            else None
                        ),
                    )
                    # In competition A2/A3 the tracker must converge on the
                    # ranked stable association, not the nearest raw balloon.
                    # It is an in-memory guidance preference only; physical
                    # motion still passes through CommandGateway below.
                    if (
                        self.gateway.profile.value == "COMPETITION"
                        and runtime.mission.state.active_stage in {"stage2", "stage3"}
                    ):
                        selected_id = runtime.target_priority.status().selected_track_id
                        selected = next((item for item in tracks.tracks if item.track_id == selected_id), None)
                        if selected is not None:
                            self.auto_tracker.preferred_target_x = selected.center_x
                            self.auto_tracker.preferred_target_y = selected.center_y
                    confirmations = runtime.hit_confirmation.update(vision_event, tracks)
                    runtime.engagement_evidence.record_confirmation_status(confirmations)
                    runtime.engagement_evidence.observe_frame(
                        vision_event,
                        update,
                        tracks,
                        associations,
                        mission_stage=runtime.mission.state.active_stage,
                        command_profile=self.gateway.profile.value,
                    )
                    runtime.engagement_evidence.capture_active_camera_frame(runtime.camera_runtime)
                    runtime.engagement_evidence.capture_active_digital_twin_state(lambda: runtime.digital_twin.state(runtime))
                    runtime.engagement_evidence.finalize_due_recording()
                    if runtime.mission.state.active_stage == "stage2":
                        runtime.stage2_engagement.observe(confirmations, runtime.mission.state.stage2_round)
                    elif runtime.mission.state.active_stage == "stage3":
                        runtime.stage3_engagement.observe(
                            vision_event,
                            tracks,
                            confirmations,
                            runtime.mission.state.stage3_round,
                        )
                self.loop_count += 1

                # 3. Motor komutunu rate-limit ile gönder. USB CDC buffer'ı
                # şişerse fire komutu eski SPD paketlerinin arkasına düşer.
                target_absent = self._safe_stop_on_target_loss(update)
                if not target_absent and self._should_send_speed(update) and self.gateway.runtime is not None:
                    self.gateway.send_motion(self.gateway.runtime, update.speed_x, update.speed_y, origin="tracking")
                    self._last_speed_sent_at = time.time()
                    self._last_speed_sent = (update.speed_x, update.speed_y)

                self._update_fire_zone(vision_event, update, frame_width, frame_height)

                # 4. Interval bekle (loop süresi çıkarılarak)
                elapsed = time.time() - t0
                sleep_time = max(0.001, self.interval_s - elapsed)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.errors += 1
                self.logger.emit(LogLevel.ERROR, "TRACKING_LOOP", f"Loop error: {exc}")
                await asyncio.sleep(0.1)  # Hata durumunda yavaşla

        if self.gateway.runtime is not None:
            self.gateway.serial.gateway_safe_stop()
            self.gateway.driver_enabled = False
            self.gateway.actuator_armed = False
        self.is_firing = False

    def _safe_stop_on_target_loss(self, update: TrackingUpdate) -> bool:
        """Cut the enabled motor driver once when the tracked target disappears.

        A zero-speed SPD packet stops step generation but leaves the Pico motor
        driver energized. Target loss is a safety transition, so it must use
        the full CommandGateway STP + DRV,0 chain. The latch prevents flooding
        the USB serial queue while subsequent frames remain target-free.
        """
        if update.state != TrackingState.SEARCHING:
            self._target_loss_safed = False
            return False
        if self._target_loss_safed:
            return True

        self._target_loss_safed = True
        self._last_speed_sent = (0, 0)
        self._reset_fire_candidate()
        if self.gateway.runtime is None or not self.gateway.driver_enabled:
            return True

        result = self.gateway.stop_motion()
        payload = {
            "frame_id": update.frame_id,
            "target_lost_frames": update.target_lost_frames,
            "accepted": result.accepted,
            "reason_codes": result.reason_codes,
            "detail": result.detail,
        }
        self._events.append(("tracking.target_lost_safe_stop", payload))
        self.logger.emit(
            LogLevel.INFO if result.accepted else LogLevel.ERROR,
            "TRACKING_LOOP",
            "Target lost; CommandGateway safe-stop applied",
            payload,
        )
        return True

    def _should_send_speed(self, update: TrackingUpdate) -> bool:
        speed = (update.speed_x, update.speed_y)
        elapsed = time.time() - self._last_speed_sent_at
        if speed == self._last_speed_sent and elapsed < 0.25:
            return False
        command_rate_hz = max(1.0, min(60.0, float(getattr(self.auto_tracker, "command_rate_hz", 30.0) or 30.0)))
        return elapsed >= 1.0 / command_rate_hz

    def _frame_size(self) -> tuple[int, int]:
        camera_runtime = getattr(self.vision_pipeline, "camera_runtime", None)
        if camera_runtime is None:
            return self.frame_width, self.frame_height
        status = camera_runtime.status()
        width = int(status.actual_width or status.requested_width or self.frame_width)
        height = int(status.actual_height or status.requested_height or self.frame_height)
        self.frame_width = width
        self.frame_height = height
        return width, height

    def _update_fire_zone(self, vision_event, update: TrackingUpdate, frame_width: int, frame_height: int) -> None:
        if update.target_center_x is None or update.target_center_y is None:
            self._reset_fire_candidate()
            return
        target_bbox = self._target_bbox_for_update(vision_event, update)
        if target_bbox is None:
            self._reset_fire_candidate()
            return
        fire_radius = min(target_bbox.w, target_bbox.h) * FIRE_ZONE_RADIUS_RATIO
        crosshair_x = update.frame_center_x
        crosshair_y = update.frame_center_y
        distance = math.hypot(update.target_center_x - crosshair_x, update.target_center_y - crosshair_y)
        if distance <= fire_radius:
            self.fire_target_frames += 1
        else:
            self._reset_fire_candidate()
        if self.fire_target_frames >= FIRE_REQUIRED_FRAMES and not self._fire_candidate_active:
            self._fire_candidate_active = True
            self.logger.emit(
                LogLevel.WARN,
                "TRACKING_LOOP",
                "Fire candidate observed; forwarding to CommandGateway for preflight evaluation",
                self._fire_event_payload(vision_event, update, distance, fire_radius),
            )
            self._events.append(("tracking.fire_candidate", self._fire_event_payload(vision_event, update, distance, fire_radius)))
            if self._physical_auto_fire_allowed():
                result = self.gateway.fire_from_tracking(self.gateway.runtime, self._fire_event_payload(vision_event, update, distance, fire_radius))
                self.auto_tracker.record_fire_result(result)
                self._events.append(("tracking.fire_result", result.model_dump(mode="json")))

    def _physical_auto_fire_allowed(self) -> bool:
        """Keep LIVE_TEST tracking physical but its FIRE action operator-driven.

        Competition stages A2/A3 own autonomous engagement. LIVE_TEST and
        VIDEO_DEMO still retain fully working physical FIRE through the visible
        operator/Gateway command, but a centered target cannot surprise-trigger
        or interrupt a motion-only tracking acceptance run.
        """
        runtime = self.gateway.runtime
        if runtime is None or self.gateway.profile.value != "COMPETITION":
            return False
        return runtime.mission.state.active_stage in {"stage2", "stage3"}

    def _vision_event_is_fresh(self, vision_event) -> bool:
        if vision_event is None:
            return False
        event_timestamp_s = float(vision_event.timestamp_ms) / 1000.0
        age_s = time.time() - event_timestamp_s
        return 0.0 <= age_s <= MAX_VISION_EVENT_AGE_S

    def _handle_stale_vision(self, vision_event) -> None:
        now = time.time()
        if now - self._last_stale_vision_log_at >= 1.0:
            age_ms = None
            if vision_event is not None:
                age_ms = round(max(0.0, (now - float(vision_event.timestamp_ms) / 1000.0) * 1000.0), 1)
            self.logger.emit(
                LogLevel.WARN,
                "TRACKING_LOOP",
                "Stale or missing vision event; tracker is commanded to safe search",
                {"event_age_ms": age_ms, "max_age_ms": int(MAX_VISION_EVENT_AGE_S * 1000)},
            )
            self._last_stale_vision_log_at = now
        self._reset_fire_candidate()

    def _reset_fire_candidate(self) -> None:
        self.fire_target_frames = 0
        self._fire_candidate_active = False

    def _target_bbox_for_update(self, vision_event, update: TrackingUpdate):
        if vision_event is None or not vision_event.balloon_detections:
            return None
        return min(
            vision_event.balloon_detections,
            key=lambda det: (det.center_x - (update.target_center_x or det.center_x)) ** 2
            + (det.center_y - (update.target_center_y or det.center_y)) ** 2,
        ).bbox

    def _fire_event_payload(self, vision_event, update: TrackingUpdate, distance: float, fire_radius: float) -> dict:
        payload = {
            "frame_id": update.frame_id,
            "distance_px": round(distance, 2),
            "fire_radius_px": round(fire_radius, 2),
            "target_center_x": update.target_center_x,
            "target_center_y": update.target_center_y,
            "required_stable_frames": FIRE_REQUIRED_FRAMES,
            "physical_fire_generated": False,
        }
        target = self._target_bbox_for_update(vision_event, update)
        if target is None or vision_event is None:
            return payload
        balloon = min(
            vision_event.balloon_detections,
            key=lambda det: (det.center_x - (update.target_center_x or det.center_x)) ** 2
            + (det.center_y - (update.target_center_y or det.center_y)) ** 2,
        )
        tracks = getattr(getattr(self.auto_tracker.status(), "multi_target_tracker", None), "tracks", [])
        if not isinstance(tracks, (list, tuple)):
            return payload
        track = next((item for item in tracks if item.detection_id == balloon.id and item.fresh), None)
        if track is None:
            return payload
        payload["balloon_detection_id"] = balloon.id
        payload["balloon_track_id"] = track.track_id
        if self.gateway.runtime is not None:
            association = next(
                (item for item in self.gateway.runtime.association.status().associations if item.balloon_track_id == track.track_id),
                None,
            )
            if association is not None:
                payload["body_detection_id"] = association.body_detection_id
                payload["body_track_id"] = association.body_track_id
                payload["association_state"] = association.state
                body = next((item for item in vision_event.body_detections if item.id == association.body_detection_id), None)
                if body is not None:
                    payload["body_class"] = body.class_name
                    payload["body_team"] = body.target_team
        return payload
