import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.websocket import WebSocketEnvelope
from app.services.camera_status_bridge import camera_status_from_runtime

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    runtime = websocket.app.state.runtime
    seq = 0
    try:
        while True:
            serial_timeout_entries = runtime.serial.check_timeouts()
            vision_event = runtime.vision_pipeline.latest()
            vision_status = runtime.vision_pipeline.status()
            camera_status = camera_status_from_runtime(runtime)
            decision = runtime.decision_engine.evaluate(runtime)
            hardware_status = runtime.hardware.status(mock_pico_active=runtime.pico.status().mock_mode)
            camera_runtime_status = runtime.camera_runtime.status()
            vision_runtime_status = runtime.vision_runtime.status(
                current_fps=vision_status.fps,
                latest_latency_ms=vision_status.latest_latency_ms,
                camera_source_type=runtime.camera_runtime.profile.source_type,
            )
            messages = [
                ("system.state", runtime.system_state().model_dump(mode="json")),
                ("decision.updated", decision.model_dump(mode="json")),
                ("pico.telemetry", runtime.pico.telemetry().model_dump(mode="json")),
                ("pico.connection", runtime.pico.last_connection_event.model_dump(mode="json")),
                ("pico.pin_validation", runtime.pico.last_validation.model_dump(mode="json")),
                ("serial.status", runtime.serial.status().model_dump(mode="json")),
                ("motion.status", runtime.motion.status().model_dump(mode="json")),
                ("hardware.status", hardware_status.model_dump(mode="json")),
                ("hardware.telemetry", hardware_status.telemetry.model_dump(mode="json")),
                ("calibration.status", runtime.calibration.status().model_dump(mode="json")),
                ("vision.status", vision_status.model_dump(mode="json")),
                ("vision.frame", vision_event.model_dump(mode="json")),
                ("vision.detections", vision_event.model_dump(mode="json")),
                ("camera.status", camera_status.model_dump(mode="json")),
                ("camera.runtime_status", camera_runtime_status.model_dump(mode="json")),
                ("vision.runtime_status", vision_runtime_status.model_dump(mode="json")),
                ("performance.status", runtime.performance.status(runtime).model_dump(mode="json")),
                ("mission.status", runtime.mission.snapshot().model_dump(mode="json")),
                (
                    "vision.frame_stats",
                    {
                        "fps": vision_event.fps,
                        "capture_latency_ms": vision_event.preprocess_ms,
                        "inference_latency_ms": vision_event.inference_ms,
                        "tracking_latency_ms": 0.0,
                        "decision_latency_ms": vision_event.postprocess_ms,
                    },
                ),
                ("decision.gates", runtime.safety.state(decision).model_dump(mode="json")),
                ("safety.gates", runtime.safety.state(decision).model_dump(mode="json")),
                ("tracking.status", runtime.auto_tracker.status().model_dump(mode="json")),
            ]
            # TrackingLoop owns PID state; WebSocket only publishes its last update.
            if runtime.auto_tracker.tracking_active and runtime.tracking_loop.last_update is not None:
                messages.append(("tracking.update", runtime.tracking_loop.last_update.model_dump(mode="json")))
            messages.extend(runtime.tracking_loop.drain_events())
            for warning in vision_event.warnings:
                messages.append(("vision.warning", {"frame_id": vision_event.frame_id, "warning": warning}))
            if runtime.last_safety_event is not None:
                messages.append(runtime.last_safety_event)
            if runtime.last_motion_event is not None:
                messages.append(runtime.last_motion_event)
            if runtime.calibration.last_event is not None:
                messages.append(runtime.calibration.last_event)
            if runtime.color_classifier.last_event is not None:
                messages.append(runtime.color_classifier.last_event)
            if runtime.model_registry.last_event is not None:
                messages.append(runtime.model_registry.last_event)
            if runtime.model_packages.last_event is not None:
                messages.append(runtime.model_packages.last_event)
            if runtime.inference_adapter.last_event is not None:
                messages.append(runtime.inference_adapter.last_event)
            if runtime.sessions.last_event is not None:
                messages.append(runtime.sessions.last_event)
            if runtime.annotations.last_event is not None:
                messages.append(runtime.annotations.last_event)
            if runtime.dataset.last_event is not None:
                messages.append(runtime.dataset.last_event)
            if runtime.data_lab.last_event is not None:
                messages.append(runtime.data_lab.last_event)
            if runtime.demo.last_event is not None:
                messages.append(runtime.demo.last_event)
            if runtime.replay.last_event is not None:
                messages.append(runtime.replay.last_event)
            if runtime.engagement_evidence.last_event is not None:
                messages.append(runtime.engagement_evidence.last_event)
            if runtime.self_test.last_event is not None:
                messages.append(runtime.self_test.last_event)
            if runtime.first_run.last_event is not None:
                messages.append(runtime.first_run.last_event)
            if runtime.interface_inventory.last_event is not None:
                messages.append(runtime.interface_inventory.last_event)
            if runtime.report_export.last_event is not None:
                messages.append(runtime.report_export.last_event)
            if runtime.hardware.last_event is not None:
                messages.append(runtime.hardware.last_event)
            if runtime.device_manager.last_event is not None:
                messages.append(runtime.device_manager.last_event)
            if runtime.device_profiles.last_event is not None:
                messages.append(runtime.device_profiles.last_event)
            if runtime.camera_runtime.last_event is not None:
                messages.append(runtime.camera_runtime.last_event)
            if runtime.vision_runtime.last_event is not None:
                messages.append(runtime.vision_runtime.last_event)
            if runtime.vision_surrogate.last_event is not None:
                messages.append(runtime.vision_surrogate.last_event)
            if runtime.release.last_event is not None:
                messages.append(runtime.release.last_event)
            if runtime.mission.last_event is not None:
                messages.append(runtime.mission.last_event)
            if runtime.person_safety.last_event is not None:
                messages.append(runtime.person_safety.last_event)
            replay_frame = runtime.replay.frame_event()
            if replay_frame is not None:
                messages.append(replay_frame)
            if decision.decision_state == "FAULT":
                messages.append(("safety.fault", decision.model_dump(mode="json")))
            if runtime.motion.status().motion_state == "FAULT":
                messages.append(("motion.fault", runtime.motion.status().model_dump(mode="json")))
            for entry in serial_timeout_entries:
                messages.append(("serial.timeout", entry.model_dump(mode="json")))
            for entry in runtime.serial.recent_logs()[-5:]:
                event_type = "serial.log_status" if entry.kind.value == "status" else f"serial.{entry.kind.value}"
                messages.append((event_type, entry.model_dump(mode="json")))
            for command in runtime.motion.command_log[-5:]:
                payload = command.model_dump(mode="json")
                messages.append(("motion.command_requested", payload))
                if command.command_type in {"stop", "scan_stop"} and command.accepted:
                    messages.append(("motion.stopped", payload))
                elif command.accepted:
                    messages.append(("motion.command_accepted_dry_run", payload))
                else:
                    messages.append(("motion.command_rejected", payload))
            for event_type, payload in messages:
                seq += 1
                envelope = WebSocketEnvelope(
                    type=event_type,
                    ts=time.time(),
                    seq=seq,
                    payload=payload,
                )
                await websocket.send_json(envelope.model_dump(mode="json"))
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        return
