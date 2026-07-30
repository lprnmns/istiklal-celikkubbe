from __future__ import annotations

import re
import threading
import time
from typing import TYPE_CHECKING

from app.schemas.command_gateway import CommandProfile, GatewayCommandResult, GatewayPreflightResult, PreflightGate
from app.schemas.stage3_engagement import Stage3FriendLink
from app.schemas.decision import DecisionStateValue
from app.schemas.log import LogLevel
from app.schemas.system import MissionMode
from app.services.safety_timing import MAX_VISION_EVENT_AGE_S
from app.services.serial_service import SerialService
from app.services.safety_zone_service import active_zone_name

if TYPE_CHECKING:
    from app.services.runtime_state import RuntimeState


class CommandGateway:
    """The only backend service permitted to emit live raw Pico commands."""

    def __init__(self, serial: SerialService, logger) -> None:
        self.serial = serial
        self.logger = logger
        self.profile = CommandProfile.DRY_RUN
        self.last_preflight = GatewayPreflightResult(
            profile=self.profile,
            physical_motion_enabled=False,
            physical_fire_enabled=False,
            ready=False,
            reason_codes=["DRY_RUN_ACTIVE"],
            gates=[],
        )
        self.actuator_armed = False
        self.pico_estop_active: bool | None = None
        self.pico_protocol: str | None = None
        self.fire_release_at: float | None = None
        self._fire_release_timer: threading.Timer | None = None
        self._fire_release_lock = threading.Lock()
        self.driver_enabled = False
        self.runtime: RuntimeState | None = None
        self._last_health_probe_at = 0.0
        # The installed Arduino protocol reports ACK/health but no absolute
        # step counters.  Keep a host-side open-loop estimate from accepted
        # semantic speed commands so the digital twin can mirror the physical
        # turret without pretending that encoder telemetry exists.
        self._pose_lock = threading.Lock()
        self._pose_pan_steps = 0.0
        self._pose_tilt_steps = 0.0
        self._pose_speed_x = 0.0
        self._pose_speed_y = 0.0
        self._monotonic = time.monotonic
        self._pose_updated_at = self._monotonic()

    def bind_runtime(self, runtime: "RuntimeState") -> None:
        self.runtime = runtime
        state = runtime.motion.status()
        with self._pose_lock:
            self._pose_pan_steps = float(state.pan_position_steps)
            self._pose_tilt_steps = float(state.tilt_position_steps)
            self._pose_updated_at = self._monotonic()

    def connect_pico(self, port: str, baudrate: int) -> tuple[bool, str]:
        """Visible operator action: choose a Pico port, then run preflight."""
        ok, code = self.serial.gateway_connect_real(port, baudrate)
        self.last_preflight = GatewayPreflightResult(
            profile=self.profile,
            physical_motion_enabled=False,
            physical_fire_enabled=False,
            ready=False,
            reason_codes=[] if ok else [code],
            gates=[PreflightGate(code=code, ready=ok, detail="Run preflight after a successful port open.")],
            pico_protocol=None,
            actuator_armed=False,
        )
        return ok, code

    def select_profile(
        self,
        runtime: "RuntimeState",
        profile: CommandProfile,
        actuator_arm_requested: bool = False,
    ) -> GatewayPreflightResult:
        self._stop_pose_estimate(runtime, command="gateway_profile_change")
        self._release_fire_output(force=True)
        self.profile = profile
        self.actuator_armed = False
        self.driver_enabled = False
        if profile == CommandProfile.DRY_RUN:
            runtime.config.system.dry_run = True
            runtime.config.system.hardware_enabled = False
            runtime.config.hardware.physical_command_enabled = False
            runtime.config.hardware.allow_physical_motion = False
            runtime.config.hardware.allow_physical_fire = False
            runtime.config.motion.real_motion_enabled = False
            runtime.force_armed = False
            self.serial.gateway_safe_stop()
            self.last_preflight = GatewayPreflightResult(
                profile=profile,
                physical_motion_enabled=False,
                physical_fire_enabled=False,
                ready=True,
                reason_codes=["DRY_RUN_ACTIVE"],
                gates=[PreflightGate(code="DRY_RUN_ACTIVE", ready=True, detail="Simulation profile selected; no physical command is emitted.")],
                pico_protocol=self.pico_protocol,
                actuator_armed=False,
            )
            return self.last_preflight

        runtime.config.system.dry_run = False
        runtime.config.system.hardware_enabled = True
        runtime.config.system.mode = MissionMode.MANUAL if profile in {CommandProfile.LIVE_TEST, CommandProfile.VIDEO_DEMO} else MissionMode.AUTONOMOUS
        runtime.config.hardware.physical_command_enabled = True
        runtime.config.hardware.allow_physical_motion = True
        runtime.config.hardware.allow_physical_fire = True
        runtime.config.motion.real_motion_enabled = True
        runtime.force_armed = True
        return self.run_preflight(runtime, actuator_arm_requested=actuator_arm_requested)

    def run_preflight(self, runtime: "RuntimeState", actuator_arm_requested: bool = False) -> GatewayPreflightResult:
        previously_active = self.actuator_armed or self.driver_enabled or runtime.force_armed
        gates: list[PreflightGate] = []
        reasons: list[str] = []

        if self.profile == CommandProfile.DRY_RUN:
            return self.select_profile(runtime, CommandProfile.DRY_RUN)

        ping = self.serial.gateway_exchange("PING", ("OK,PONG", "PONG"))
        pico_ok = ping.accepted
        if pico_ok:
            self.pico_protocol = "arduino_raw" if "OK,PONG" in ping.reason else "micropython_json"
        gates.append(PreflightGate(code="PICO_HANDSHAKE_OK" if pico_ok else "PICO_HANDSHAKE_FAILED", ready=pico_ok, detail=ping.reason))
        if not pico_ok:
            reasons.append("PICO_HANDSHAKE_FAILED")

        stat = self.serial.gateway_exchange("STAT", ("OK,STAT", "STATUS")) if pico_ok else None
        stat_ok = bool(stat and stat.accepted)
        estop_active = self._estop_from_response(stat.reason if stat else "")
        self.pico_estop_active = estop_active if stat_ok else None
        gates.append(
            PreflightGate(
                code="ESTOP_RELEASED" if stat_ok and not estop_active else "ESTOP_ACTIVE" if estop_active else "ESTOP_STATE_UNKNOWN",
                ready=stat_ok and not estop_active,
                detail=stat.reason if stat else "Pico status is unavailable.",
            )
        )
        if not stat_ok:
            reasons.append("ESTOP_STATE_UNKNOWN")
        elif estop_active:
            reasons.append("ESTOP_ACTIVE")

        camera_fresh = self._camera_is_fresh(runtime)
        gates.append(
            PreflightGate(
                code="CAMERA_FRESH" if camera_fresh else "CAMERA_STALE",
                ready=camera_fresh,
                detail=f"Latest camera event must be newer than {int(MAX_VISION_EVENT_AGE_S * 1000)}ms.",
            )
        )
        if not camera_fresh:
            reasons.append("CAMERA_STALE")

        motion = runtime.motion.status()
        motion_ready = motion.motion_state != "FAULT" and not motion.estop_state
        gates.append(
            PreflightGate(
                code="MOTION_LIMITS_OK" if motion_ready else "MOTION_FAULT_OR_ESTOP",
                ready=motion_ready,
                detail="Motion service has no fault and its E-stop state is released." if motion_ready else "Motion fault or E-stop state is active.",
            )
        )
        if not motion_ready:
            reasons.append("MOTION_FAULT_OR_ESTOP")

        # Motion authority and trigger authority are intentionally separate.
        # A visible TEST startup uses the real camera/Pico/turret motion path
        # without arming the trigger. CANLI SISTEM requests the same preflight
        # with actuator_arm_requested=True and gains FIRE authority only after
        # the Pico acknowledges ARM,1.
        arm_ok = False
        if stat_ok and not estop_active and actuator_arm_requested:
            arm = self.serial.gateway_exchange("ARM,1", ("OK,ARM_1", "TRIGGER_ARMED"))
            arm_ok = arm.accepted
            if not arm_ok:
                reasons.append("ACTUATOR_ARM_FAILED")
            arm_detail = arm.reason
        elif stat_ok and not estop_active and not actuator_arm_requested:
            disarm = self.serial.gateway_exchange("ARM,0", ("OK,ARM_0", "TRIGGER_DISARMED"))
            if not disarm.accepted:
                reasons.append("ACTUATOR_DISARM_FAILED")
            reasons.append("ACTUATOR_NOT_ARMED")
            arm_detail = disarm.reason if disarm.accepted else f"Trigger disarm failed: {disarm.reason}"
        elif not actuator_arm_requested:
            reasons.append("ACTUATOR_NOT_ARMED")
            arm_detail = "Trigger disarm skipped because Pico/E-stop preflight is not ready."
        else:
            arm_detail = "Actuator arm skipped because Pico/E-stop preflight is not ready."
        self.actuator_armed = arm_ok
        runtime.force_armed = arm_ok
        gates.append(PreflightGate(code="ACTUATOR_ARMED" if arm_ok else "ACTUATOR_NOT_ARMED", ready=arm_ok, detail=arm_detail))

        # Not requesting ARM (or an ARM failure) must not suppress safe turret
        # motion. A failed ARM,0 acknowledgement is different: TEST cannot be
        # considered motion-ready until the Pico confirms trigger disarm.
        motion_reasons = [code for code in reasons if code not in {"ACTUATOR_NOT_ARMED", "ACTUATOR_ARM_FAILED"}]
        motion_authorized = not motion_reasons
        fire_authorized = motion_authorized and arm_ok
        result = GatewayPreflightResult(
            profile=self.profile,
            physical_motion_enabled=motion_authorized,
            physical_fire_enabled=fire_authorized,
            ready=fire_authorized,
            reason_codes=sorted(set(reasons)),
            gates=gates,
            pico_protocol=self.pico_protocol,
            actuator_armed=self.actuator_armed,
        )
        self.last_preflight = result
        if not motion_authorized and previously_active:
            self.serial.gateway_safe_stop()
            self.driver_enabled = False
        self.logger.emit(
            LogLevel.INFO if motion_authorized else LogLevel.WARN,
            "COMMAND_GATEWAY",
            "Preflight completed",
            result.model_dump(mode="json"),
        )
        return result

    def send_motion(self, runtime: "RuntimeState", speed_x: int, speed_y: int, origin: str = "operator") -> GatewayCommandResult:
        stage1_competition = self.profile == CommandProfile.COMPETITION and runtime.mission.state.active_stage == "stage1"
        if origin == "tracking" and stage1_competition:
            return self._blocked("MOTION", ["MANUAL_TRACKING_MOTION_BLOCKED"])
        if origin == "manual_operator" and stage1_competition:
            mission = runtime.mission.state
            if not mission.stage1_order_locked:
                return self._blocked("MOTION", ["STAGE1_PLAN_NOT_STARTED"])
            if not mission.timer_running:
                return self._blocked("MOTION", ["STAGE1_TIMER_NOT_RUNNING"])
            if mission.elapsed_s >= 300:
                return self._blocked("MOTION", ["STAGE1_TIME_EXPIRED"])
        # Refresh the explicit Pico health check before evaluating a stale
        # heartbeat.  This permits a recovered Pico to resume after the user
        # runs/selects a live profile; it never emits motion before preflight.
        if not self._heartbeat_is_fresh():
            refreshed = self.run_preflight(runtime, actuator_arm_requested=self.actuator_armed)
            if not refreshed.ready:
                return self._blocked("MOTION", refreshed.reason_codes)
        reasons = self._live_reasons(runtime, require_actuator_arm=False)
        reasons.extend(self._movement_boundary_reasons(runtime, speed_x, speed_y))
        if reasons:
            return self._blocked("MOTION", reasons)
        driver_ack = None
        if not self.driver_enabled:
            driver = self.serial.gateway_exchange("DRV,1", ("OK,DRIVER_ENABLED",))
            if not driver.accepted:
                return self._blocked("MOTION", ["PICO_DRIVER_ENABLE_FAILED"], driver.reason)
            self.driver_enabled = True
            driver_ack = driver.reason
        # Safety/limit checks above use semantic operator coordinates: +X is
        # camera-right and +Y is camera-up.  Only at the hardware boundary do
        # we adapt those directions to the installed motor wiring.
        motor = runtime.config.motor
        if motor.axis_swap:
            raw_speed_x = int(speed_y) * motor.tilt_direction_multiplier
            raw_speed_y = int(speed_x) * motor.pan_direction_multiplier
        else:
            raw_speed_x = int(speed_x) * motor.pan_direction_multiplier
            raw_speed_y = int(speed_y) * motor.tilt_direction_multiplier
        speed = self.serial.gateway_exchange(f"SPD,{raw_speed_x},{raw_speed_y}", ("OK,SPD",))
        if speed.accepted:
            self._set_pose_speed(runtime, float(speed_x), float(speed_y))
        return GatewayCommandResult(
            accepted=speed.accepted,
            command="SPD",
            reason_codes=[] if speed.accepted else ["PICO_MOTION_WRITE_FAILED"],
            detail=speed.reason,
            pico_ack=driver_ack,
            physical_command_generated=speed.accepted and not speed.no_physical_command_generated,
        )

    def fire_from_tracking(self, runtime: "RuntimeState", candidate: dict) -> GatewayCommandResult:
        stage = runtime.mission.state.active_stage
        if self.profile == CommandProfile.COMPETITION and stage == "stage1":
            return self._blocked("FIRE", ["MANUAL_OPERATOR_COMMAND_REQUIRED"])
        if self.profile == CommandProfile.COMPETITION:
            if stage == "stage2":
                stage2_reasons = self._autonomous_engagement_reasons(runtime, candidate, stage="A2")
                if stage2_reasons:
                    return self._blocked("FIRE", stage2_reasons)
            else:
                decision = runtime.decision_engine.evaluate(runtime)
                if decision.decision_state != DecisionStateValue.FIRE_READY:
                    return self._blocked("FIRE", ["DECISION_NOT_FIRE_READY", *decision.blocking_reasons])
                if stage == "stage3":
                    candidate_body = candidate.get("body_detection_id")
                    if not isinstance(candidate_body, int) or decision.selected_body_detection_id != candidate_body:
                        return self._blocked("FIRE", ["A3_DECISION_TARGET_MISMATCH"])
                    stage3_reasons = self._autonomous_engagement_reasons(runtime, candidate, stage="A3")
                    if stage3_reasons:
                        return self._blocked("FIRE", stage3_reasons)
                    friend_links = self._stage3_friend_links(runtime)
                    if len(friend_links) != 2:
                        return self._blocked("FIRE", ["A3_FRIEND_SAFETY_EVIDENCE_INCOMPLETE"])
                    candidate["friend_links"] = [item.model_dump(mode="json") for item in friend_links]
        elif self.profile in {CommandProfile.LIVE_TEST, CommandProfile.VIDEO_DEMO}:
            event = runtime.vision.latest_event
            if event is None or not event.balloon_detections:
                return self._blocked("FIRE", ["LIVE_TEST_BALLOON_NOT_DETECTED"])
        else:
            return self._blocked("FIRE", ["DRY_RUN_ACTIVE"])

        reasons = self._live_reasons(runtime, require_actuator_arm=True)
        zone_name = active_zone_name(
            runtime.config.decision.fire_forbidden_zones,
            runtime.motion.status().pan_position_deg,
            runtime.motion.status().tilt_position_deg,
        )
        if zone_name:
            reasons.append("FIRE_FORBIDDEN_ZONE")
        if reasons:
            return self._blocked("FIRE", reasons)
        command = self.serial.gateway_exchange("LZR,1", ("OK,LASER_1", "FIRE_SERVO_PULLED"))
        if not command.accepted:
            return self._blocked("FIRE", ["PICO_FIRE_REJECTED"], command.reason)
        self._schedule_fire_release(1.0)
        result = GatewayCommandResult(
            accepted=True,
            command="LZR,1",
            detail="Pico acknowledged trigger pull.",
            pico_ack=command.reason,
            physical_command_generated=not command.no_physical_command_generated,
        )
        # Evidence is observational.  A recorder failure must never alter an
        # accepted Pico command or create another physical output.
        try:
            runtime.engagement_evidence.record_shot_ack(runtime, candidate, result)
        except Exception as exc:
            self.logger.emit(LogLevel.WARN, "COMMAND_GATEWAY", "Shot evidence record failed", {"reason_code": "EVIDENCE_RECORD_FAILED", "error": str(exc)})
        balloon_track_id = candidate.get("balloon_track_id")
        # Visual confirmation is an observational fact for every accepted
        # tracked shot, including LIVE_TEST/VIDEO_DEMO.  Only competition
        # stages below consume it for score/round progression.
        if isinstance(balloon_track_id, int):
            runtime.hit_confirmation.register_shot(
                balloon_track_id,
                candidate.get("body_detection_id") if isinstance(candidate.get("body_detection_id"), int) else None,
                body_track_id=candidate.get("body_track_id") if isinstance(candidate.get("body_track_id"), int) else None,
            )
        if self.profile == CommandProfile.COMPETITION and stage in {"stage2", "stage3"}:
            if isinstance(balloon_track_id, int):
                if stage == "stage2":
                    runtime.stage2_engagement.register_shot(balloon_track_id, runtime.mission.state.stage2_round)
                elif stage == "stage3":
                    body_class = candidate.get("body_class")
                    friend_links = [Stage3FriendLink.model_validate(item) for item in candidate.get("friend_links", [])]
                    if isinstance(body_class, str):
                        runtime.stage3_engagement.register_shot(
                            enemy_class=body_class,
                            enemy_balloon_track_id=balloon_track_id,
                            friend_links=friend_links,
                            current_round=runtime.mission.state.stage3_round,
                        )
        self.logger.emit(LogLevel.INFO, "COMMAND_GATEWAY", "Fire command acknowledged", {**candidate, **result.model_dump(mode="json")})
        return result

    @staticmethod
    def _autonomous_engagement_reasons(runtime: "RuntimeState", candidate: dict, stage: str) -> list[str]:
        """A2/A3 physical fire requires a current, selected, stable link.

        This deliberately consumes only telemetry services.  None of these
        services write serial; CommandGateway remains the sole output point.
        """
        prefix = stage
        balloon_track_id = candidate.get("balloon_track_id")
        if not isinstance(balloon_track_id, int):
            return [f"{prefix}_TRACK_ID_UNRESOLVED"]
        if not runtime.auto_tracker.tracking_active:
            return [f"{prefix}_TRACKING_NOT_ACTIVE"]
        tracks = runtime.auto_tracker.status().multi_target_tracker.tracks
        track = next((item for item in tracks if item.track_id == balloon_track_id), None)
        if track is None or not track.fresh:
            return [f"{prefix}_TRACK_STALE"]
        priority = runtime.target_priority.status()
        if priority.selected_track_id != balloon_track_id:
            return [f"{prefix}_PRIORITY_TARGET_MISMATCH"]
        association = next(
            (item for item in runtime.association.status().associations if item.balloon_track_id == balloon_track_id),
            None,
        )
        if association is None or association.state != "stable" or association.body_detection_id is None:
            return [f"{prefix}_ASSOCIATION_NOT_STABLE"]
        candidate_body = candidate.get("body_detection_id")
        if isinstance(candidate_body, int) and candidate_body != association.body_detection_id:
            return [f"{prefix}_ASSOCIATION_TARGET_MISMATCH"]
        record = next((item for item in runtime.hit_confirmation.status().records if item.balloon_track_id == balloon_track_id), None)
        if record is not None and record.state.value == "PENDING_CONFIRMATION":
            return [f"{prefix}_HIT_CONFIRMATION_PENDING"]
        if stage == "A2":
            mission = runtime.mission.state
            if mission.stage2_failed:
                return ["A2_STAGE_FAILED"]
            if mission.stage2_completed_rounds >= 4:
                return ["A2_ALL_ROUNDS_COMPLETED"]
        elif stage == "A3":
            if candidate.get("body_team") != "enemy":
                return ["A3_CANDIDATE_NOT_ENEMY"]
            if candidate.get("body_class") not in {"f16", "helicopter", "ballistic_missile", "mini_micro_uav"}:
                return ["A3_CANDIDATE_CLASS_UNRESOLVED"]
            mission = runtime.mission.state
            if mission.stage3_failed:
                return ["A3_STAGE_FAILED"]
            if mission.stage3_completed_rounds >= 8:
                return ["A3_ALL_ROUNDS_COMPLETED"]
        return []

    @staticmethod
    def _stage3_friend_links(runtime: "RuntimeState") -> list[Stage3FriendLink]:
        event = runtime.vision.latest_event
        if event is None:
            return []
        body_by_id = {body.id: body for body in event.body_detections}
        links: list[Stage3FriendLink] = []
        for association in runtime.association.status().associations:
            if association.state != "stable" or association.body_detection_id is None or association.body_track_id is None:
                continue
            body = body_by_id.get(association.body_detection_id)
            if body is not None and body.target_team == "friend":
                links.append(
                    Stage3FriendLink(
                        balloon_track_id=association.balloon_track_id,
                        body_track_id=association.body_track_id,
                    )
                )
        return sorted(links, key=lambda item: item.balloon_track_id)

    def fire_from_operator(self, runtime: "RuntimeState", candidate: dict) -> GatewayCommandResult:
        """Stage-1 manual fire: explicit operator intent, never tracker intent."""
        mission = runtime.mission.state
        stage1_competition = self.profile == CommandProfile.COMPETITION and mission.active_stage == "stage1"
        if stage1_competition:
            if not mission.stage1_order_locked:
                return self._blocked("FIRE", ["STAGE1_PLAN_NOT_STARTED"])
            if not mission.timer_running:
                return self._blocked("FIRE", ["STAGE1_TIMER_NOT_RUNNING"])
            if mission.elapsed_s >= 300:
                return self._blocked("FIRE", ["STAGE1_TIME_EXPIRED"])
            if not runtime.mission.snapshot().score.stage1_next_target:
                return self._blocked("FIRE", ["STAGE1_ALL_TARGETS_COMPLETED"])
        reasons = self._live_reasons(runtime, require_actuator_arm=True)
        zone_name = active_zone_name(
            runtime.config.decision.fire_forbidden_zones,
            runtime.motion.status().pan_position_deg,
            runtime.motion.status().tilt_position_deg,
        )
        if zone_name:
            reasons.append("FIRE_FORBIDDEN_ZONE")
        if reasons:
            return self._blocked("FIRE", reasons)
        command = self.serial.gateway_exchange("LZR,1", ("OK,LASER_1", "FIRE_SERVO_PULLED"))
        if not command.accepted:
            return self._blocked("FIRE", ["PICO_FIRE_REJECTED"], command.reason)
        self._schedule_fire_release(1.0)
        result = GatewayCommandResult(
            accepted=True,
            command="LZR,1",
            detail="Pico acknowledged manual trigger pull.",
            pico_ack=command.reason,
            physical_command_generated=not command.no_physical_command_generated,
        )
        # A manual fire may follow an already locked tracked target.  Attach
        # its ACK to that read-only evidence record when present.
        try:
            runtime.engagement_evidence.record_shot_ack(runtime, candidate, result)
        except Exception as exc:
            self.logger.emit(LogLevel.WARN, "COMMAND_GATEWAY", "Manual shot evidence record failed", {"reason_code": "EVIDENCE_RECORD_FAILED", "error": str(exc)})
        self.logger.emit(LogLevel.INFO, "COMMAND_GATEWAY", "Manual fire command acknowledged", {**candidate, **result.model_dump(mode="json")})
        return result

    def configure_trigger_servo(self, runtime: "RuntimeState", release_deg: int, fire_deg: int) -> GatewayCommandResult:
        """Configure Pico trigger endpoints through the same live authority.

        The command changes PWM configuration only; it never pulls the
        trigger. A later explicit test/fire is still separately preflighted.
        """
        if not (0 <= release_deg < fire_deg <= 180):
            return self._blocked("SRV,CFG", ["SERVO_ANGLE_RANGE_INVALID"])
        reasons = self._live_reasons(runtime, require_actuator_arm=False)
        if reasons:
            return self._blocked("SRV,CFG", reasons)
        if self.pico_protocol == "arduino_raw":
            raw_command = f"CFG_SERVO,{release_deg},{fire_deg}"
            expected_ack = ("OK,SERVO_CFG",)
        else:
            raw_command = f"SRV,CFG,{release_deg},{fire_deg}"
            expected_ack = ("OK,SERVO_CONFIGURED", "SERVO_CONFIGURED")
        command = self.serial.gateway_exchange(raw_command, expected_ack)
        if not command.accepted:
            return self._blocked("SRV,CFG", ["PICO_SERVO_CONFIG_REJECTED"], command.reason)
        return GatewayCommandResult(
            accepted=True, command=raw_command, detail="Pico acknowledged trigger servo configuration.",
            pico_ack=command.reason, physical_command_generated=not command.no_physical_command_generated,
        )

    def test_trigger(self, runtime: "RuntimeState", pulse_s: float) -> GatewayCommandResult:
        """Visible empty-chamber trigger test; exactly the normal live fire gates."""
        reasons = self._live_reasons(runtime, require_actuator_arm=True)
        if reasons:
            return self._blocked("SRV,TEST", reasons)
        # MicroPython exposes SRV,TEST. The currently installed Arduino
        # firmware exposes the same armed/E-stop protected actuator through
        # LZR,1, so use that real protocol without consuming competition shot
        # ledger capacity for an explicitly labelled empty-chamber test.
        if self.pico_protocol == "arduino_raw":
            raw_command = "LZR,1"
            expected_ack = ("OK,LASER_1",)
        else:
            raw_command = "SRV,TEST"
            expected_ack = ("OK,SERVO_TEST", "FIRE_SERVO_PULLED")
        command = self.serial.gateway_exchange(
            raw_command,
            expected_ack,
            count_physical_shot=False,
        )
        if not command.accepted:
            return self._blocked("SRV,TEST", ["PICO_FIRE_REJECTED"], command.reason)
        self._schedule_fire_release(pulse_s)
        return GatewayCommandResult(
            accepted=True, command=raw_command, detail="Pico acknowledged empty-chamber trigger test.", pico_ack=command.reason,
            physical_command_generated=not command.no_physical_command_generated,
        )

    def stop_motion(self) -> GatewayCommandResult:
        """A safe-stop is always allowed, including during a failed preflight."""
        result = self.serial.gateway_exchange("STP", ("OK,STOP", "EMERGENCY_STOP"))
        driver = self.serial.gateway_exchange("DRV,0", ("OK,DRIVER_DISABLED",))
        self.driver_enabled = False
        if self.runtime is not None:
            self._stop_pose_estimate(self.runtime, command="gateway_stop")
        accepted = result.accepted and driver.accepted
        return GatewayCommandResult(
            accepted=accepted,
            command="STP",
            reason_codes=[] if accepted else (["PICO_STOP_WRITE_FAILED"] if not result.accepted else ["PICO_DRIVER_DISABLE_FAILED"]),
            detail=f"{result.reason}; {driver.reason}",
            pico_ack=driver.reason if accepted else result.reason if result.accepted else None,
            physical_command_generated=accepted and not result.no_physical_command_generated and not driver.no_physical_command_generated,
        )

    def invalidate_preflight(self, runtime: "RuntimeState", reason_code: str) -> None:
        """Safely invalidate live authority after an operator safety edit."""
        self._stop_pose_estimate(runtime, command="gateway_preflight_invalidated")
        if self.profile != CommandProfile.DRY_RUN:
            self.serial.gateway_safe_stop()
        self._release_fire_output(force=True)
        self.actuator_armed = False
        self.driver_enabled = False
        runtime.force_armed = False
        self.last_preflight = self.last_preflight.model_copy(
            update={
                "ready": False,
                "physical_motion_enabled": False,
                "physical_fire_enabled": False,
                "actuator_armed": False,
                "reason_codes": sorted(set([*self.last_preflight.reason_codes, reason_code])),
            }
        )

    def tick(self, runtime: "RuntimeState") -> None:
        # Fallback for deterministic tests and runtimes that already call
        # tick(). The independent Timer below is the primary production path.
        self._release_fire_output(force=False)
        live_reasons = self._live_reasons(runtime, require_actuator_arm=False)
        if self.profile != CommandProfile.DRY_RUN and live_reasons:
            self._safe_live_runtime(runtime, live_reasons)

    def maintenance_tick(self, runtime: "RuntimeState") -> None:
        """Production heartbeat/E-Stop monitor independent of browser state."""
        self.refresh_motion_estimate(runtime)
        self._release_fire_output(force=False)
        if self.profile == CommandProfile.DRY_RUN:
            return
        now = time.time()
        if now - self._last_health_probe_at < 0.5:
            return
        self._last_health_probe_at = now
        if self.serial.connection_state.name == "FAULT":
            self._safe_live_runtime(runtime, ["PICO_CONNECTION_FAULT"])
            return
        ping = self.serial.gateway_exchange("PING", ("OK,PONG", "PONG"))
        if not ping.accepted:
            self._safe_live_runtime(runtime, ["PICO_CONNECTION_FAULT", "PICO_HEARTBEAT_STALE"])
            return
        stat = self.serial.gateway_exchange("STAT", ("OK,STAT", "STATUS"))
        if not stat.accepted:
            self._safe_live_runtime(runtime, ["PICO_CONNECTION_FAULT", "ESTOP_STATE_UNKNOWN"])
            return
        self.pico_estop_active = self._estop_from_response(stat.reason)
        if self.pico_estop_active:
            self._safe_live_runtime(runtime, ["ESTOP_ACTIVE"])
            return
        self.tick(runtime)

    def _safe_live_runtime(self, runtime: "RuntimeState", reasons: list[str]) -> None:
        self._stop_pose_estimate(runtime, command="gateway_safe_stop")
        was_active = self.last_preflight.ready or self.actuator_armed or self.driver_enabled or runtime.force_armed
        if was_active:
            self.serial.gateway_safe_stop()
        self.actuator_armed = False
        self.driver_enabled = False
        runtime.force_armed = False
        reason_set = set(reasons)
        updated_gates = []
        for gate in self.last_preflight.gates:
            if "CAMERA_STALE" in reason_set and gate.code in {"CAMERA_FRESH", "CAMERA_STALE"}:
                gate = gate.model_copy(update={"code": "CAMERA_STALE", "ready": False, "detail": "Latest real camera frame is stale or unavailable."})
            elif reason_set.intersection({"PICO_CONNECTION_FAULT", "PICO_HEARTBEAT_STALE"}) and gate.code.startswith("PICO_"):
                code = "PICO_CONNECTION_FAULT" if "PICO_CONNECTION_FAULT" in reason_set else "PICO_HEARTBEAT_STALE"
                gate = gate.model_copy(update={"code": code, "ready": False, "detail": "Pico heartbeat/connection is unavailable."})
            elif "ESTOP_ACTIVE" in reason_set and gate.code in {"ESTOP_RELEASED", "ESTOP_ACTIVE", "ESTOP_STATE_UNKNOWN"}:
                gate = gate.model_copy(update={"code": "ESTOP_ACTIVE", "ready": False, "detail": "Physical E-Stop is active."})
            elif "ACTUATOR_NOT_ARMED" in reason_set and gate.code in {"ACTUATOR_ARMED", "ACTUATOR_NOT_ARMED"}:
                gate = gate.model_copy(update={"code": "ACTUATOR_NOT_ARMED", "ready": False, "detail": "Actuator is not armed."})
            updated_gates.append(gate)
        self.last_preflight = self.last_preflight.model_copy(
            update={
                "ready": False,
                "physical_motion_enabled": False,
                "physical_fire_enabled": False,
                "actuator_armed": False,
                "reason_codes": sorted(set([*self.last_preflight.reason_codes, *reasons])),
                "gates": updated_gates,
            }
        )
        runtime.last_safety_event = ("safety.gateway_safed", self.last_preflight.model_dump(mode="json"))

    def refresh_motion_estimate(self, runtime: "RuntimeState" | None = None) -> None:
        """Advance and publish the non-encoder live pose estimate.

        This method is safe to call from the maintenance loop and read-only
        digital-twin requests.  It never writes serial or enables hardware.
        """
        bound_runtime = runtime or self.runtime
        if bound_runtime is None:
            return
        with self._pose_lock:
            self._integrate_pose_locked(bound_runtime)
            self._publish_pose_locked(bound_runtime, command="gateway_open_loop_estimate")

    def _set_pose_speed(self, runtime: "RuntimeState", speed_x: float, speed_y: float) -> None:
        with self._pose_lock:
            self._integrate_pose_locked(runtime)
            motion = runtime.config.motion
            command_scale = max(float(motion.command_full_scale), 1e-6)
            self._pose_speed_x = (
                max(-command_scale, min(command_scale, float(speed_x)))
                / command_scale
                * float(motion.pan_max_steps_per_second)
            )
            self._pose_speed_y = (
                max(-command_scale, min(command_scale, float(speed_y)))
                / command_scale
                * float(motion.tilt_max_steps_per_second)
            )
            self._publish_pose_locked(runtime, command="gateway_open_loop_estimate")

    def _stop_pose_estimate(self, runtime: "RuntimeState", *, command: str) -> None:
        with self._pose_lock:
            self._integrate_pose_locked(runtime)
            self._pose_speed_x = 0.0
            self._pose_speed_y = 0.0
            self._publish_pose_locked(runtime, command=command)

    def _integrate_pose_locked(self, runtime: "RuntimeState") -> None:
        now = self._monotonic()
        elapsed_s = max(0.0, now - self._pose_updated_at)
        self._pose_updated_at = now
        if elapsed_s <= 0.0:
            return
        self._pose_pan_steps += self._pose_speed_x * elapsed_s
        self._pose_tilt_steps += self._pose_speed_y * elapsed_s
        motion = runtime.config.motion
        pan_scale = max(float(motion.pan_steps_per_degree), 1e-6)
        tilt_scale = max(float(motion.tilt_steps_per_degree), 1e-6)
        if motion.soft_limits_enabled:
            self._pose_pan_steps = min(max(self._pose_pan_steps, motion.pan_min_deg * pan_scale), motion.pan_max_deg * pan_scale)
            self._pose_tilt_steps = min(max(self._pose_tilt_steps, motion.tilt_min_deg * tilt_scale), motion.tilt_max_deg * tilt_scale)

    def _publish_pose_locked(self, runtime: "RuntimeState", *, command: str) -> None:
        motion = runtime.config.motion
        pan_scale = max(float(motion.pan_steps_per_degree), 1e-6)
        tilt_scale = max(float(motion.tilt_steps_per_degree), 1e-6)
        pan_deg = self._pose_pan_steps / pan_scale
        tilt_deg = self._pose_tilt_steps / tilt_scale
        moving = bool(self._pose_speed_x or self._pose_speed_y)
        runtime.motion.state = runtime.motion.state.model_copy(
            update={
                "motion_state": "JOGGING" if moving else "STOPPED",
                "pan_position_deg": pan_deg,
                "tilt_position_deg": tilt_deg,
                "pan_target_deg": pan_deg,
                "tilt_target_deg": tilt_deg,
                "pan_position_steps": int(round(self._pose_pan_steps)),
                "tilt_position_steps": int(round(self._pose_tilt_steps)),
                "pan_error_deg": 0.0,
                "tilt_error_deg": 0.0,
                "driver_enabled": self.driver_enabled,
                "dry_run": self.profile == CommandProfile.DRY_RUN,
                "last_command": command,
                "last_error": None,
                "updated_at": time.time(),
            }
        )

    def _schedule_fire_release(self, pulse_s: float) -> None:
        """Release the physical trigger independently of UI/WS activity."""
        delay_s = max(0.01, float(pulse_s))
        with self._fire_release_lock:
            if self._fire_release_timer is not None:
                self._fire_release_timer.cancel()
            self.fire_release_at = time.time() + delay_s
            timer = threading.Timer(delay_s, self._release_fire_output, kwargs={"force": True})
            timer.daemon = True
            self._fire_release_timer = timer
            timer.start()

    def _release_fire_output(self, *, force: bool) -> None:
        with self._fire_release_lock:
            deadline = self.fire_release_at
            if deadline is None or (not force and time.time() < deadline):
                return
            timer = self._fire_release_timer
            self._fire_release_timer = None
            self.fire_release_at = None
            if timer is not None and timer is not threading.current_thread():
                timer.cancel()
        released = self.serial.gateway_exchange("LZR,0", ("OK,LASER_0", "FIRE_SERVO_RELEASED"))
        self.logger.emit(
            LogLevel.INFO if released.accepted else LogLevel.ERROR,
            "COMMAND_GATEWAY",
            "Trigger release command completed",
            {"accepted": released.accepted, "detail": released.reason},
        )

    def _live_reasons(self, runtime: "RuntimeState", require_actuator_arm: bool) -> list[str]:
        reasons: list[str] = []
        if self.profile == CommandProfile.DRY_RUN:
            reasons.append("DRY_RUN_ACTIVE")
        if require_actuator_arm and not self.last_preflight.physical_fire_enabled:
            reasons.append("PREFLIGHT_NOT_READY")
        if not require_actuator_arm and not self.last_preflight.physical_motion_enabled:
            reasons.append("PREFLIGHT_NOT_READY")
        if runtime.config.system.dry_run or not runtime.config.system.hardware_enabled:
            reasons.append("LIVE_PROFILE_NOT_ACTIVE")
        if self.serial.connection_state.name == "FAULT":
            reasons.append("PICO_CONNECTION_FAULT")
        if not self._heartbeat_is_fresh():
            reasons.append("PICO_HEARTBEAT_STALE")
        if not self._camera_is_fresh(runtime):
            reasons.append("CAMERA_STALE")
        if runtime.motion.status().estop_state:
            reasons.append("ESTOP_ACTIVE")
        if self.pico_estop_active is True:
            reasons.append("ESTOP_ACTIVE")
        if require_actuator_arm and not self.actuator_armed:
            reasons.append("ACTUATOR_NOT_ARMED")
        if require_actuator_arm and self.serial.magazine_remaining <= 0:
            reasons.append("MAGAZINE_EMPTY")
        return sorted(set(reasons))

    @staticmethod
    def _movement_boundary_reasons(runtime: "RuntimeState", speed_x: int, speed_y: int) -> list[str]:
        """Reject a command that exceeds configured speed/soft/physical limits.

        Pico firmware remains the final electrical/limit authority.  This
        gateway check gives the operator a deterministic, visible reason
        before a command reaches that last-resort layer.
        """
        state = runtime.motion.status()
        motion = runtime.config.motion
        max_speed = int(runtime.config.motor.max_speed)
        reasons: list[str] = []
        if abs(int(speed_x)) > max_speed or abs(int(speed_y)) > max_speed:
            reasons.append("MOTION_SPEED_LIMIT")
        if speed_x < 0 and state.pan_limit_left:
            reasons.append("PAN_LEFT_LIMIT_ACTIVE")
        if speed_x > 0 and state.pan_limit_right:
            reasons.append("PAN_RIGHT_LIMIT_ACTIVE")
        if speed_y > 0 and state.tilt_limit_up:
            reasons.append("TILT_UP_LIMIT_ACTIVE")
        if speed_y < 0 and state.tilt_limit_down:
            reasons.append("TILT_DOWN_LIMIT_ACTIVE")
        if motion.soft_limits_enabled:
            if speed_x < 0 and state.pan_position_deg <= motion.pan_min_deg:
                reasons.append("PAN_SOFT_LIMIT")
            if speed_x > 0 and state.pan_position_deg >= motion.pan_max_deg:
                reasons.append("PAN_SOFT_LIMIT")
            if speed_y < 0 and state.tilt_position_deg <= motion.tilt_min_deg:
                reasons.append("TILT_SOFT_LIMIT")
            if speed_y > 0 and state.tilt_position_deg >= motion.tilt_max_deg:
                reasons.append("TILT_SOFT_LIMIT")
        zone_name = active_zone_name(motion.motion_forbidden_zones, state.pan_position_deg, state.tilt_position_deg)
        if zone_name and (speed_x or speed_y):
            reasons.append("MOTION_FORBIDDEN_ZONE")
        return sorted(set(reasons))

    def _heartbeat_is_fresh(self) -> bool:
        if self.serial.gateway_last_heartbeat_at is None:
            return False
        age_ms = (time.time() - self.serial.gateway_last_heartbeat_at) * 1000
        return age_ms <= self.serial.config.serial.heartbeat_timeout_ms

    @staticmethod
    def _camera_is_fresh(runtime: "RuntimeState") -> bool:
        # Manual LIVE_TEST motion only needs proof that the selected physical
        # camera is producing current frames.  Requiring a detector event here
        # made the turret jog controls impossible to use before a YOLO model
        # was selected, even though the raw camera preview was healthy.
        # Tracking/fire paths retain their own target/detection checks.
        camera_runtime = runtime.camera_runtime
        frame_at = camera_runtime.last_frame_at
        if (
            camera_runtime.profile.source_type in {"usb", "laptop"}
            and frame_at is not None
            and not camera_runtime.capture_paused
        ):
            frame_age_s = time.time() - frame_at
            if 0.0 <= frame_age_s <= MAX_VISION_EVENT_AGE_S:
                return True

        event = runtime.vision.latest_event
        if event is None:
            return False
        age_s = time.time() - float(event.timestamp_ms) / 1000.0
        return 0.0 <= age_s <= MAX_VISION_EVENT_AGE_S

    @staticmethod
    def _estop_from_response(response: str) -> bool:
        return bool(re.search(r"ESTOP[=:_]1", response))

    def _blocked(self, command: str, reason_codes: list[str], detail: str | None = None) -> GatewayCommandResult:
        result = GatewayCommandResult(
            accepted=False,
            command=command,
            reason_codes=sorted(set(reason_codes)),
            detail=detail or "Physical command blocked by CommandGateway preflight.",
            physical_command_generated=False,
        )
        self.logger.emit(LogLevel.WARN, "COMMAND_GATEWAY", "Command rejected", result.model_dump(mode="json"))
        return result
