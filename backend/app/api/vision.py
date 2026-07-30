import base64
import io
import re
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.api.deps import get_runtime
from app.schemas.vision import (
    CameraSelectRequest,
    CameraSource,
    CameraStatus,
    BrowserFrameInferenceRequest,
    VisionConfigUpdate,
    VisionEvent,
    VisionStatus,
)
from app.schemas.legacy_perception import (
    CameraHostDiagnostic,
    LegacyPerceptionPreset,
    LegacyPerceptionPresetList,
    RealCameraEvidence,
    RealCameraAcceptance,
    RealCameraEvidenceStatus,
    RealCameraSelection,
    RealCameraSelectRequest,
)
from app.schemas.camera_runtime import CameraRuntimeApplyResult, CameraRuntimeControlsUpdate, CameraRuntimeProfile, CameraRuntimeStatus
from app.schemas.vision_runtime_settings import (
    VisionRuntimeApplyResult,
    VisionRuntimePreset,
    VisionRuntimePresetApplyRequest,
    VisionRuntimePresetSaveRequest,
    VisionRuntimeProfile,
    VisionRuntimeStatus,
    VisionRuntimeTestResult,
    VisionRuntimeVerifyResult,
)
from app.services.runtime_state import RuntimeState
from app.services.camera_status_bridge import camera_status_from_runtime
from app.services.storage_paths import project_root

try:  # pragma: no cover - host dependent
    import numpy as np
    from PIL import Image
    import cv2
except Exception:  # pragma: no cover
    np = None
    Image = None
    cv2 = None

vision_router = APIRouter(prefix="/api/vision", tags=["vision"])
camera_router = APIRouter(prefix="/api/camera", tags=["camera"])


@vision_router.post("/models/upload")
async def upload_vision_model(request: Request) -> dict[str, str]:
    """Receive a locally chosen .pt file without exposing browser fake paths."""
    raw_name = request.headers.get("x-file-name", "")
    name = Path(raw_name).name
    if not name or Path(name).suffix.lower() not in {".pt", ".onnx", ".engine"}:
        raise HTTPException(status_code=400, detail="MODEL_FILE_EXTENSION_INVALID")
    if not re.fullmatch(r"[A-Za-z0-9._ -]+", name):
        raise HTTPException(status_code=400, detail="MODEL_FILE_NAME_INVALID")
    content = await request.body()
    max_bytes = 512 * 1024 * 1024
    if not content or len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="MODEL_FILE_SIZE_INVALID")
    destination_dir = project_root() / "models" / "uploaded"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / name
    destination.write_bytes(content)
    return {"path": str(destination), "file_name": name}


@vision_router.get("/status", response_model=VisionStatus)
def get_vision_status(runtime: RuntimeState = Depends(get_runtime)) -> VisionStatus:
    return runtime.vision_pipeline.status()


@vision_router.get("/config", response_model=VisionConfigUpdate)
def get_vision_config(runtime: RuntimeState = Depends(get_runtime)) -> VisionConfigUpdate:
    return VisionConfigUpdate(
        vision_mode=runtime.vision.vision_mode,
        body_model_path=runtime.vision.body_model_path,
        balloon_model_path=runtime.vision.balloon_model_path,
        body_conf_threshold=runtime.vision.body_conf_threshold,
        balloon_conf_threshold=runtime.vision.balloon_conf_threshold,
    )


@vision_router.put("/config", response_model=VisionStatus)
def update_vision_config(
    update: VisionConfigUpdate,
    runtime: RuntimeState = Depends(get_runtime),
) -> VisionStatus:
    return runtime.vision_pipeline.configure(update)


@vision_router.post("/start", response_model=VisionStatus)
def start_vision(runtime: RuntimeState = Depends(get_runtime)) -> VisionStatus:
    return runtime.vision_pipeline.start()


@vision_router.post("/stop", response_model=VisionStatus)
def stop_vision(runtime: RuntimeState = Depends(get_runtime)) -> VisionStatus:
    return runtime.vision_pipeline.stop()


@vision_router.post("/snapshot")
def snapshot(runtime: RuntimeState = Depends(get_runtime)) -> Response:
    if runtime.vision_runtime.profile.inference_adapter == "opencv_live_circle_surrogate":
        runtime.vision_surrogate.snapshot(runtime.camera_runtime, runtime.vision_runtime.profile)
    return Response(content=runtime.camera.snapshot(), media_type="image/jpeg")


@vision_router.get("/latest", response_model=VisionEvent)
def get_latest_vision(runtime: RuntimeState = Depends(get_runtime)) -> VisionEvent:
    return runtime.vision_pipeline.latest()


@vision_router.post("/browser-frame", response_model=VisionEvent)
def browser_frame_inference(request: BrowserFrameInferenceRequest, runtime: RuntimeState = Depends(get_runtime)) -> VisionEvent:
    if np is None or Image is None:
        raise HTTPException(status_code=503, detail="browser_frame_decode_dependencies_unavailable")
    payload = request.image_base64
    if "," in payload:
        payload = payload.split(",", 1)[1]
    try:
        decoded = base64.b64decode(payload, validate=False)
        image = Image.open(io.BytesIO(decoded)).convert("RGB")
        # CameraRuntime/OpenCV frames are BGR.  Keep browser frames in the
        # same convention so model preprocessing and body-ROI HSV IFF see
        # identical channel ordering.
        frame = np.asarray(image)[:, :, ::-1].copy()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"browser_frame_decode_failed:{exc}") from exc
    return runtime.vision_pipeline.latest_from_external_frame(
        frame,
        source="browser_camera_ultralytics_yolo",
        camera_source_kind="browser_camera",
        frame_origin="browser_frame_upload",
        camera_device_path=request.device_label,
    )


@vision_router.get("/legacy-presets", response_model=LegacyPerceptionPresetList)
def legacy_perception_presets(runtime: RuntimeState = Depends(get_runtime)) -> LegacyPerceptionPresetList:
    return runtime.legacy_perception.list_presets()


@vision_router.get("/legacy-presets/{preset_id}", response_model=LegacyPerceptionPreset)
def legacy_perception_preset(preset_id: str, runtime: RuntimeState = Depends(get_runtime)) -> LegacyPerceptionPreset:
    return runtime.legacy_perception.get_preset(preset_id)


@vision_router.get("/real-camera/status", response_model=RealCameraEvidenceStatus)
def real_camera_status(runtime: RuntimeState = Depends(get_runtime)) -> RealCameraEvidenceStatus:
    return runtime.legacy_perception.status(runtime.camera_runtime)


@vision_router.post("/real-camera/select", response_model=RealCameraSelection)
def real_camera_select(request: RealCameraSelectRequest, runtime: RuntimeState = Depends(get_runtime)) -> RealCameraSelection:
    return runtime.camera_host.select_camera(request.device_path, request.camera_kind)


@vision_router.post("/real-camera/capture-evidence", response_model=RealCameraEvidence)
def real_camera_capture_evidence(runtime: RuntimeState = Depends(get_runtime), preset_id: str | None = None, device_path: str | None = None) -> RealCameraEvidence:
    host = runtime.camera_host.status()
    if not host.host_camera_devices_detected:
        blocked = runtime.camera_host.capture_blocked("Linux host did not expose /dev/video* camera devices")
        return runtime.legacy_perception.capture_host_blocked_evidence(blocked, preset_id=preset_id)
    if "permission" in host.blocker_reason.lower():
        blocked = runtime.camera_host.capture_blocked(host.blocker_reason)
        return runtime.legacy_perception.capture_host_blocked_evidence(blocked, preset_id=preset_id)
    direct_capture = runtime.camera_host.capture_frame_evidence(device_path=device_path)
    if direct_capture.get("frame_captured") or runtime.camera_runtime.profile.source_type == "mock":
        return runtime.legacy_perception.record_camera_host_frame_evidence(direct_capture, preset_id=preset_id)
    evidence = runtime.legacy_perception.capture_evidence(runtime.camera_runtime, preset_id=preset_id)
    runtime.camera_host.mark_capture_attempt(
        frame_captured=evidence.status == "recorded",
        reason="real camera frame evidence captured" if evidence.status == "recorded" else evidence.status,
    )
    return evidence


@vision_router.get("/real-camera/latest", response_model=RealCameraEvidence)
def real_camera_latest(runtime: RuntimeState = Depends(get_runtime)) -> RealCameraEvidence:
    return runtime.legacy_perception.latest()


@vision_router.get("/real-camera/acceptance", response_model=RealCameraAcceptance)
def real_camera_acceptance(runtime: RuntimeState = Depends(get_runtime)) -> RealCameraAcceptance:
    host = runtime.camera_host.latest()
    latest = runtime.legacy_perception.latest()
    status = "passed" if latest.status == "recorded" and latest.frame_origin == "real_capture" else (
        "blocked" if host.camera_acceptance_status == "blocked_by_host_os" else "partial"
    )
    return RealCameraAcceptance(
        status=status,
        camera_tooling_status=host.camera_acceptance_status,
        frame_captured=latest.status == "recorded" and latest.frame_origin == "real_capture",
        device_path=latest.camera_device_path,
        width=latest.frame_width,
        height=latest.frame_height,
        fps_estimate=latest.fps_estimate,
        frame_hash=latest.target_center_metadata.get("frame_hash") if isinstance(latest.target_center_metadata, dict) else None,
        frame_path=latest.target_center_metadata.get("frame_path") if isinstance(latest.target_center_metadata, dict) else None,
        capture_method=latest.target_center_metadata.get("capture_method") if isinstance(latest.target_center_metadata, dict) else None,
        selected_camera_device=latest.target_center_metadata.get("selected_camera_device") if isinstance(latest.target_center_metadata, dict) else latest.camera_device_path,
        selected_camera_name=latest.target_center_metadata.get("selected_camera_name") if isinstance(latest.target_center_metadata, dict) else None,
        camera_kind=(latest.target_center_metadata.get("camera_kind") if isinstance(latest.target_center_metadata, dict) else None) or "unknown_camera",
        internal_camera_passed=latest.status == "recorded" and latest.camera_device_path in {"/dev/video0", "/dev/video1"},
        external_usb_camera_passed=latest.status == "recorded" and latest.camera_device_path in {"/dev/video2", "/dev/video3"},
        blocker_reason=host.blocker_reason,
        camera_host=host,
        latest_evidence=latest,
        advisory_only=True,
        physical_command_enabled=False,
        no_physical_command_generated=True,
    )


@vision_router.get("/camera-host/status", response_model=CameraHostDiagnostic)
def camera_host_status(runtime: RuntimeState = Depends(get_runtime)) -> CameraHostDiagnostic:
    return runtime.camera_host.status()


@vision_router.post("/camera-host/diagnose", response_model=CameraHostDiagnostic)
def camera_host_diagnose(runtime: RuntimeState = Depends(get_runtime)) -> CameraHostDiagnostic:
    return runtime.camera_host.diagnose()


@vision_router.get("/camera-host/latest", response_model=CameraHostDiagnostic)
def camera_host_latest(runtime: RuntimeState = Depends(get_runtime)) -> CameraHostDiagnostic:
    return runtime.camera_host.latest()


@camera_router.get("/status", response_model=CameraStatus)
def get_camera_status(runtime: RuntimeState = Depends(get_runtime)) -> CameraStatus:
    return camera_status_from_runtime(runtime)


@camera_router.get("/sources", response_model=list[CameraSource])
def get_camera_sources(runtime: RuntimeState = Depends(get_runtime)) -> list[CameraSource]:
    return runtime.camera.sources()


@camera_router.post("/select", response_model=CameraStatus)
def select_camera(
    request: CameraSelectRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> CameraStatus:
    return runtime.camera.select(request)


@camera_router.get("/stream.mjpg")
def camera_stream(runtime: RuntimeState = Depends(get_runtime)) -> StreamingResponse:
    if runtime.camera_runtime.profile.source_type != "mock":
        return StreamingResponse(
            runtime.camera_runtime.mjpeg_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    return StreamingResponse(
        runtime.camera.mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@camera_router.get("/frame.jpg")
def camera_frame(runtime: RuntimeState = Depends(get_runtime)) -> Response:
    """Return one current frame for a browser-safe live preview."""
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
    }
    if runtime.camera_runtime.profile.source_type == "mock":
        return Response(content=runtime.camera.snapshot(), media_type="image/jpeg", headers=headers)
    frame, warnings = runtime.camera_runtime.live_preview_frame()
    if cv2 is None:
        return Response(content=b"opencv unavailable", status_code=503, media_type="text/plain", headers=headers)
    if frame is None:
        frame = runtime.camera_runtime._placeholder_frame("; ".join(warnings) or "camera frame unavailable")
    stream_frame = runtime.camera_runtime._stream_frame(frame)
    ok, encoded = cv2.imencode(".jpg", stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    if not ok:
        return Response(content=b"jpeg encode failed", status_code=503, media_type="text/plain", headers=headers)
    return Response(content=encoded.tobytes(), media_type="image/jpeg", headers=headers)


@camera_router.get("/stream-overlay.mjpg")
def camera_overlay_stream(runtime: RuntimeState = Depends(get_runtime)) -> StreamingResponse:
    """Live camera MJPEG with the most recent vision-event boxes rendered."""
    if runtime.camera_runtime.profile.source_type == "mock":
        return StreamingResponse(runtime.camera.mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
    def frames():
        while True:
            frame, _warnings = runtime.camera_runtime.live_preview_frame()
            if frame is None or cv2 is None:
                time.sleep(0.08)
                continue
            frame = runtime.camera_runtime._stream_frame(frame)
            event = runtime.vision.latest_event
            if event is not None and event.frame_width > 0 and event.frame_height > 0:
                sx, sy = frame.shape[1] / event.frame_width, frame.shape[0] / event.frame_height
                for detection, color, label in [
                    *[(item, (40, 220, 255), "BALON") for item in event.balloon_detections],
                    *[(item, (255, 180, 40), "HEDEF") for item in event.body_detections],
                ]:
                    x, y = int(detection.bbox.x * sx), int(detection.bbox.y * sy)
                    w, h = int(detection.bbox.w * sx), int(detection.bbox.h * sy)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    confidence_label = (
                        f"{detection.confidence:.1%}"
                        if detection.confidence < 0.1
                        else f"{detection.confidence:.0%}"
                    )
                    cv2.putText(frame, f"{label} {confidence_label}", (x, max(18, y - 7)), cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
            ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
            time.sleep(1 / max(runtime.camera_runtime.profile.fps, 1))
    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@camera_router.get("/runtime/status", response_model=CameraRuntimeStatus)
def camera_runtime_status(runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeStatus:
    return runtime.camera_runtime.status()


@camera_router.post("/runtime/start-preview", response_model=CameraRuntimeStatus)
def camera_runtime_start_preview(runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeStatus:
    """Start only the selected raw camera capture; never enables inference."""
    return runtime.camera_runtime.start_preview()


@camera_router.get("/runtime/profile", response_model=CameraRuntimeProfile)
def camera_runtime_profile(runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeProfile:
    return runtime.camera_runtime.profile


@camera_router.post("/runtime/apply-profile", response_model=CameraRuntimeApplyResult)
def camera_runtime_apply(profile: CameraRuntimeProfile, runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeApplyResult:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    return runtime.camera_runtime.apply(profile)


@camera_router.patch("/runtime/controls", response_model=CameraRuntimeStatus)
def camera_runtime_controls(update: CameraRuntimeControlsUpdate, runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeStatus:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    return runtime.camera_runtime.apply_controls(update)


@camera_router.post("/runtime/reset-defaults", response_model=CameraRuntimeApplyResult)
def camera_runtime_reset(runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeApplyResult:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    return runtime.camera_runtime.reset_defaults()


@camera_router.post("/runtime/probe-current", response_model=CameraRuntimeApplyResult)
def camera_runtime_probe_current(runtime: RuntimeState = Depends(get_runtime)) -> CameraRuntimeApplyResult:
    return runtime.camera_runtime.probe_current()


@camera_router.post("/runtime/snapshot")
def camera_runtime_snapshot(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    if runtime.vision_runtime.profile.inference_adapter == "opencv_live_circle_surrogate":
        return runtime.vision_surrogate.snapshot(runtime.camera_runtime, runtime.vision_runtime.profile)
    return runtime.camera_runtime.snapshot()


@camera_router.post("/runtime/benchmark")
def camera_runtime_benchmark(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.camera_runtime.benchmark()


@camera_router.post("/runtime/release")
def camera_runtime_release(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.camera_runtime.release()


@vision_router.get("/runtime/settings", response_model=VisionRuntimeProfile)
def vision_runtime_settings(runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeProfile:
    return runtime.vision_runtime.profile


@vision_router.post("/runtime/apply-settings", response_model=VisionRuntimeApplyResult)
def vision_runtime_apply(profile: VisionRuntimeProfile, runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeApplyResult:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    status = runtime.vision_pipeline.status()
    return runtime.vision_runtime.apply(profile, current_fps=status.fps, latest_latency_ms=status.latest_latency_ms, camera_source_type=runtime.camera_runtime.profile.source_type)


@vision_router.post("/runtime/reset-defaults", response_model=VisionRuntimeApplyResult)
def vision_runtime_reset(runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeApplyResult:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    status = runtime.vision_pipeline.status()
    return runtime.vision_runtime.reset_defaults()


@vision_router.post("/runtime/reload-models")
def vision_runtime_reload(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    return runtime.vision_runtime.reload_models()


@vision_router.post("/runtime/warmup")
def vision_runtime_warmup(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.vision_runtime.warmup(runtime.vision_pipeline)


@vision_router.post("/runtime/benchmark")
def vision_runtime_benchmark(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.vision_runtime.benchmark(runtime.vision_pipeline)


@vision_router.get("/runtime/status", response_model=VisionRuntimeStatus)
def vision_runtime_status(runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeStatus:
    pipeline_status = runtime.vision_pipeline.status()
    result = runtime.vision_runtime.status(
        current_fps=pipeline_status.fps,
        latest_latency_ms=pipeline_status.latest_latency_ms,
        camera_source_type=runtime.camera_runtime.profile.source_type,
    )
    # Setup Center supports direct local model paths in addition to registry
    # packages. Reflect the path actually used by VisionPipeline; otherwise the
    # cockpit says "model missing / reload required" while CUDA inference is
    # visibly producing detections from that selected file.
    direct_models = [
        ("body", runtime.vision.body_model_path),
        ("balloon", runtime.vision.balloon_model_path),
    ]
    present = [(role, str(Path(path))) for role, path in direct_models if path and Path(path).is_file()]
    inference_failed = any(str(item).startswith("ultralytics_inference_failed:") for item in pipeline_status.warnings)
    if result.profile.inference_adapter == "ultralytics_yolo" and present:
        roles = {role: path for role, path in present}
        selected_path = roles.get("balloon") or roles.get("body")
        details = {
            **result.active_model_details,
            "active_model_id": "setup_direct_model_path",
            "adapter_mode": "ultralytics_yolo",
            "model_type": "combined_detector" if len(present) > 1 else f"{present[0][0]}_detector",
            "model_file": Path(selected_path).name if selected_path else None,
            "file_path": selected_path,
            "class_mapping_status": "direct_path_present_unverified",
            "loaded": not inference_failed,
            "last_test_status": "live_inference_failed" if inference_failed else ("live_inference_active" if pipeline_status.latest_frame_id > 0 else "awaiting_first_frame"),
        }
        warnings = [
            item for item in result.warnings
            if item != "Model reload required for Ultralytics YOLO adapter." and not item.startswith("model_missing:")
        ]
        errors = [item for item in result.errors if item != "active_yolo_model_file_missing"]
        if inference_failed:
            errors.append(next(item for item in pipeline_status.warnings if str(item).startswith("ultralytics_inference_failed:")))
        result = result.model_copy(update={
            "active_model_summary": {
                **result.active_model_summary,
                "active_body_model_id": "setup_body_path" if "body" in roles else None,
                "active_balloon_model_id": "setup_balloon_path" if "balloon" in roles else None,
            },
            "active_model_details": details,
            "effective_adapter": "ultralytics_yolo",
            "runtime_source": "setup_direct_model_path",
            "test_adapter_active": False,
            "reload_required": False,
            "adapter_available": not inference_failed,
            "warnings": warnings,
            "errors": errors,
        })
    return result


@vision_router.get("/runtime/presets", response_model=list[VisionRuntimePreset])
def vision_runtime_presets(runtime: RuntimeState = Depends(get_runtime)) -> list[VisionRuntimePreset]:
    return runtime.vision_runtime.presets()


@vision_router.post("/runtime/apply-preset", response_model=VisionRuntimeApplyResult)
def vision_runtime_apply_preset(request: VisionRuntimePresetApplyRequest, runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeApplyResult:
    if runtime.stage3_competition_profile_locked():
        raise HTTPException(status_code=409, detail="A3_PROFILE_LOCKED")
    status = runtime.vision_pipeline.status()
    return runtime.vision_runtime.apply_preset(request.preset_name, current_fps=status.fps, latest_latency_ms=status.latest_latency_ms)


@vision_router.post("/runtime/save-preset")
def vision_runtime_save_preset(request: VisionRuntimePresetSaveRequest, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.vision_runtime.save_preset(request.preset)


@vision_router.post("/runtime/verify-active", response_model=VisionRuntimeVerifyResult)
def vision_runtime_verify_active(runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeVerifyResult:
    return runtime.vision_runtime.verify_active()


@vision_router.post("/runtime/test-active-model", response_model=VisionRuntimeTestResult)
def vision_runtime_test_active_model(runtime: RuntimeState = Depends(get_runtime)) -> VisionRuntimeTestResult:
    return runtime.vision_runtime.test_active_model()
