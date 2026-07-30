import time
import os
import subprocess
import sys
import tempfile
import threading
import glob
import re
from pathlib import Path

import yaml

from app.schemas.camera_runtime import CameraRuntimeApplyResult, CameraRuntimeControlsUpdate, CameraRuntimeProfile, CameraRuntimeStatus
from app.schemas.config import AppConfig
from app.schemas.log import LogLevel
from app.services.device_manager_service import DeviceManagerService
from app.services.log_service import JsonlLogService
from app.services.storage_paths import project_root

try:  # pragma: no cover - host dependent
    import cv2
    import numpy as np
except Exception:  # pragma: no cover
    cv2 = None
    np = None


class CameraRuntimeService:
    def __init__(self, config: AppConfig, devices: DeviceManagerService, logger: JsonlLogService) -> None:
        self.config = config
        self.devices = devices
        self.logger = logger
        self.profile = CameraRuntimeProfile(
            source_type=config.camera_runtime.default_source_type,
            width=config.camera_runtime.default_width,
            height=config.camera_runtime.default_height,
            fps=config.camera_runtime.default_fps,
            pixel_format=config.camera_runtime.default_fourcc,
            lens_profile=config.camera_runtime.default_lens_profile,
            stream_width=config.camera_runtime.default_width,
            stream_height=config.camera_runtime.default_height,
            inference_width=config.camera_runtime.inference_width,
            inference_height=config.camera_runtime.inference_height,
            device_path=config.camera_runtime.default_device_path,
        )
        self.last_error: str | None = None
        self.last_warnings: list[str] = []
        self.last_capture_backend: str = "fallback"
        self.last_capture_error: str | None = None
        self.last_probe_result: dict | None = None
        self.last_frame = None
        self.last_frame_at: float | None = None
        self.last_frame_warnings: list[str] = []
        self.frame_lock = threading.Lock()
        self.capture = None
        self.capture_key: tuple | None = None
        self.capture_lock = threading.Lock()
        self.capture_worker_thread: threading.Thread | None = None
        self.capture_worker_process: subprocess.Popen | None = None
        self.capture_worker_stop = threading.Event()
        self.capture_worker_key: tuple | None = None
        self.capture_paused = False
        self.updated_at = time.time()
        self.last_event: tuple[str, dict] | None = None
        self.path = project_root() / "config" / "runtime" / "camera_profile.active.yaml"
        self._load_persisted_profile()

    def status(self) -> CameraRuntimeStatus:
        decision = self._camera_source_decision()
        actual_width = self.profile.width
        actual_height = self.profile.height
        if self.last_frame is not None:
            actual_height = int(self.last_frame.shape[0])
            actual_width = int(self.last_frame.shape[1])
        last_frame_age_ms = None
        if self.last_frame_at is not None:
            last_frame_age_ms = max(0, int((time.time() - self.last_frame_at) * 1000))
        selected_device = decision["selected_device"]
        selected_backend = "mock" if self.profile.source_type == "mock" else self.last_capture_backend
        # A frame from a previous Setup/profile session is not proof that the
        # current camera stream is alive. Treat only a recent frame as live so
        # the UI cannot report "camera active" while showing a stale/black
        # capture after a device ownership conflict.
        frame_fresh_limit_ms = max(1500, int(5000 / max(self.profile.fps, 1)))
        frame_is_fresh = last_frame_age_ms is not None and last_frame_age_ms <= frame_fresh_limit_ms
        device_available = decision["capture_device"] is not None
        is_real_camera_evidence = (
            self.profile.source_type in {"usb", "laptop"}
            and device_available
            and self.last_frame is not None
            and frame_is_fresh
            and selected_backend in {"opencv", "ffmpeg"}
        )
        source_mode = str(decision["source_mode"])
        if is_real_camera_evidence:
            source_mode = "REAL_USB_CAMERA_LIVE" if decision["is_external_usb_camera"] else "REAL_LAPTOP_CAMERA_LIVE"
        elif self.last_frame is not None and decision["is_laptop_camera"]:
            source_mode = "REAL_LAPTOP_CAMERA_LATEST_FRAME"
        elif self.last_frame is not None and decision["is_external_usb_camera"]:
            source_mode = "REAL_USB_CAMERA_LATEST_FRAME"
        return CameraRuntimeStatus(
            profile=self.profile,
            running=self.profile.source_type == "mock" or is_real_camera_evidence,
            selected_camera=selected_device,
            requested_width=self.profile.width,
            requested_height=self.profile.height,
            requested_fps=self.profile.fps,
            requested_pixel_format=self.profile.pixel_format,
            actual_width=actual_width,
            actual_height=actual_height,
            actual_fps=float(self.profile.fps),
            actual_fps_measured=float(self.profile.fps),
            actual_pixel_format=self.profile.pixel_format,
            backend_api=selected_backend,
            warmup_ms=0.0 if self.profile.source_type == "mock" else 120.0,
            dropped_frames=0,
            last_probe_result=self.last_probe_result,
            recommendation_score=self._recommendation_score(),
            last_apply_ok=self.last_error is None,
            last_error=self.last_error,
            warnings=self.last_warnings,
            selected_device=selected_device,
            selected_backend=selected_backend,
            source_mode=source_mode,
            input_format="mjpeg" if self.profile.pixel_format in {"auto", "MJPG"} else self.profile.pixel_format.lower(),
            resolution=f"{actual_width}x{actual_height}",
            last_frame_age_ms=last_frame_age_ms,
            last_capture_error=self.last_capture_error,
            is_real_camera_evidence=is_real_camera_evidence,
            is_external_usb_camera=bool(decision["is_external_usb_camera"]),
            is_laptop_camera=bool(decision["is_laptop_camera"]),
            hardware_presence_note=str(decision["hardware_presence_note"]),
            updated_at=self.updated_at,
        )

    def apply(self, profile: CameraRuntimeProfile) -> CameraRuntimeApplyResult:
        self._event("camera.profile_apply_started", profile.model_dump(mode="json"), "Camera runtime profile apply started")
        previous = self.profile
        warnings: list[str] = []
        suggested_action = None
        accepted = True
        rollback = False
        if profile.source_type != "mock":
            device_id = profile.device_id
            if not device_id and profile.device_path:
                device_id = f"camera_{profile.device_path.strip('/').replace('/', '_').replace('.', '_')}"
            if os.name == "nt":
                # Opening a DirectShow camera during profile validation takes
                # several seconds and the following preview call used to open
                # the same device a second time.  PnP presence is sufficient
                # for apply; the background preview worker supplies the real
                # frame/health proof immediately afterwards.
                saved_index_responds = self.devices.windows_camera_path_responds(profile.device_path)
                device = next((item for item in self.devices.inventory().cameras if item.device_id == (device_id or "")), None)
                if saved_index_responds:
                    # Keep the explicitly requested path/stable identity. PnP
                    # ordinal mapping is not authoritative when virtual camera
                    # indexes are present.
                    pass
                elif device is None or not device.connected:
                    accepted = False
                    rollback = True
                    warnings.append("Camera device not found.")
                    suggested_action = "Refresh devices and select a listed camera."
                else:
                    profile = profile.model_copy(
                        update={"device_path": device.device_path, "stable_path": device.stable_path}
                    )
            else:
                probe = self.devices.probe_camera(device_id or "")
                if not probe.accepted:
                    accepted = False
                    rollback = True
                    warnings.extend(probe.warnings or ["Camera probe failed."])
                    suggested_action = probe.suggested_action or "Use mock camera or verify device permissions."
                elif probe.device is not None:
                    profile = profile.model_copy(update={"device_path": probe.device.device_path, "stable_path": probe.device.stable_path})
        if accepted:
            self._stop_capture_worker()
            self._release_capture()
            self.capture_paused = False
            self.profile = profile
            self.last_error = None
            self.last_warnings = warnings
            self._persist()
        else:
            self.profile = previous
            self.last_error = "camera_profile_apply_failed"
            self.last_warnings = warnings
            self._event("camera.profile_rollback", {"warnings": warnings, "profile": previous.model_dump(mode="json")}, "Camera runtime profile rolled back", LogLevel.WARN)
        self.updated_at = time.time()
        result = CameraRuntimeApplyResult(
            accepted=accepted,
            applied=accepted,
            rollback_performed=rollback,
            profile=self.profile,
            actual_width=self.profile.width,
            actual_height=self.profile.height,
            actual_fps=float(self.profile.fps),
            actual_fps_measured=float(self.profile.fps),
            actual_pixel_format=self.profile.pixel_format,
            backend_api="mock" if self.profile.source_type == "mock" else "opencv",
            warmup_ms=0.0 if self.profile.source_type == "mock" else 120.0,
            dropped_frames=0,
            last_probe_result=self.last_probe_result,
            warnings=warnings,
            suggested_action=suggested_action,
        )
        self._event("camera.profile_apply_completed", result.model_dump(mode="json"), "Camera runtime profile apply completed", LogLevel.INFO if accepted else LogLevel.WARN)
        return result

    def apply_controls(self, controls: CameraRuntimeControlsUpdate) -> CameraRuntimeStatus:
        update = controls.model_dump(exclude_none=True)
        self.profile = self.profile.model_copy(update=update)
        if self.profile.source_type != "mock":
            path = self.profile.device_path or self.profile.stable_path
            if path:
                self._apply_v4l2_controls(path)
        self.updated_at = time.time()
        self._persist()
        self._event("camera.controls_updated", {"controls": update, "profile": self.profile.model_dump(mode="json")}, "Camera runtime controls updated")
        return self.status()

    def reset_defaults(self) -> CameraRuntimeApplyResult:
        return self.apply(CameraRuntimeProfile())

    def probe_current(self) -> CameraRuntimeApplyResult:
        started = time.time()
        warnings = ["Current profile probe is metadata-only for mock/replay sources."] if self.profile.source_type in {"mock", "replay"} else []
        self.last_probe_result = {
            "requested_width": self.profile.width,
            "requested_height": self.profile.height,
            "requested_fps": self.profile.fps,
            "requested_pixel_format": self.profile.pixel_format,
            "actual_width": self.profile.width,
            "actual_height": self.profile.height,
            "actual_fps_measured": float(self.profile.fps),
            "actual_pixel_format": self.profile.pixel_format,
            "backend_api": "mock" if self.profile.source_type == "mock" else "opencv",
            "warmup_ms": round((time.time() - started) * 1000, 3),
            "dropped_frames": 0,
            "warnings": warnings,
            "no_physical_command_generated": True,
        }
        return CameraRuntimeApplyResult(
            accepted=True,
            applied=False,
            profile=self.profile,
            actual_width=self.profile.width,
            actual_height=self.profile.height,
            actual_fps=float(self.profile.fps),
            actual_fps_measured=float(self.profile.fps),
            actual_pixel_format=self.profile.pixel_format,
            backend_api="mock" if self.profile.source_type == "mock" else "opencv",
            warmup_ms=self.last_probe_result["warmup_ms"],
            dropped_frames=0,
            last_probe_result=self.last_probe_result,
            warnings=warnings,
        )

    def benchmark(self) -> dict:
        result = {
            "source_type": self.profile.source_type,
            "target_fps": self.profile.fps,
            "estimated_latency_ms": round(1000 / max(self.profile.fps, 1), 3),
            "no_physical_command_generated": True,
        }
        self._event("camera.benchmark_completed", result, "Camera runtime benchmark completed")
        return result

    def snapshot(self) -> dict:
        return {
            "accepted": True,
            "source_type": self.profile.source_type,
            "width": self.profile.width,
            "height": self.profile.height,
            "no_physical_command_generated": True,
        }

    def release(self) -> dict:
        self.capture_paused = True
        self._release_capture()
        self.last_capture_backend = "released"
        self.last_capture_error = None
        self.last_warnings = ["camera runtime capture released by operator request"]
        self.updated_at = time.time()
        self._event("camera.runtime_released", {"profile": self.profile.model_dump(mode="json")}, "Camera runtime capture released")
        return {
            "ok": True,
            "released": True,
            "message": "Kamera runtime yakalaması bırakıldı.",
            "no_physical_command_generated": True,
        }

    def start_preview(self) -> CameraRuntimeStatus:
        """Start the profile-owned capture without blocking the API on USB warmup."""
        self.capture_paused = False
        if self.profile.source_type == "mock":
            self.read_frame()
            return self.status()
        decision = self._camera_source_decision()
        path = decision["capture_device"]
        if path is None:
            self.last_error = "camera_device_unavailable"
            self.last_capture_backend = "fallback"
            self.last_capture_error = str(decision["hardware_presence_note"])
            self.last_warnings = [self.last_capture_error]
            self.updated_at = time.time()
            return self.status()
        if self._is_persistent_capture_path(path):
            self._ensure_capture_worker(path)
        else:
            self.read_frame()
        self.updated_at = time.time()
        return self.status()

    def read_frame(self):
        if self.capture_paused:
            self.last_capture_backend = "released"
            self.last_capture_error = "camera_runtime_capture_released"
            return None, ["camera_runtime_capture_released"]
        if self.profile.source_type == "mock":
            if cv2 is None or np is None:
                return None, ["mock_frame_numpy_unavailable"]
            frame = np.zeros((self.profile.height, self.profile.width, 3), dtype=np.uint8)
            cx = int(self.profile.width * 0.58)
            cy = int(self.profile.height * 0.42)
            radius = max(12, int(min(self.profile.width, self.profile.height) * 0.08))
            cv2.circle(frame, (cx, cy), radius, (0, 0, 255), -1)
            cv2.putText(frame, "MOCK SURROGATE FRAME", (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            self.last_capture_backend = "fallback"
            self.last_capture_error = None
            return frame, ["mock camera frame used for surrogate"]
        if cv2 is None:
            return None, ["opencv_not_available"]
        decision = self._camera_source_decision()
        path = decision["capture_device"]
        if path is None:
            self.last_capture_backend = "fallback"
            self.last_capture_error = str(decision["hardware_presence_note"])
            return None, ["camera_device_not_selected", str(decision["hardware_presence_note"])]
        # The live MJPEG endpoint calls this at the requested stream rate.
        # Do not reuse a one-second cached frame here: doing so created a
        # 1 FPS-looking preview while repeatedly encoding that same image.
        # Cached frames remain available only as a failure fallback below.
        frame, opencv_warnings = self._read_frame_opencv_persistent(path)
        if frame is not None:
            self.last_capture_backend = "opencv"
            self.last_capture_error = None
            return frame, opencv_warnings
        frame, ffmpeg_warnings = self._read_frame_ffmpeg(path)
        if frame is not None:
            self.last_error = None
            self.last_capture_backend = "ffmpeg"
            self.last_capture_error = None
            self._set_last_frame(frame, ffmpeg_warnings)
            return frame, ffmpeg_warnings
        if isinstance(path, str) and path.startswith("/dev/"):
            if self.last_frame is not None:
                cached_frame, cached_warnings = self._cached_frame(max_age_s=None)
                if cached_frame is not None:
                    return cached_frame, [*(opencv_warnings or []), *(ffmpeg_warnings or []), *cached_warnings]
            self.last_error = "camera_frame_read_failed"
            self.last_capture_backend = "fallback"
            self.last_capture_error = "; ".join([*(opencv_warnings or []), *(ffmpeg_warnings or []), f"camera_frame_read_failed:{path}"])
            return None, [*(opencv_warnings or []), *(ffmpeg_warnings or []), f"camera_frame_read_failed:{path}"]
        capture = cv2.VideoCapture(path if isinstance(path, str) and path.startswith("/dev/") else path)
        if not capture.isOpened():
            self.last_error = "camera_open_failed"
            self.last_capture_backend = "fallback"
            self.last_capture_error = f"camera_open_failed:{path}"
            return None, [f"camera_open_failed:{path}"]
        try:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.profile.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.profile.height)
            capture.set(cv2.CAP_PROP_FPS, self.profile.fps)
            ok, frame = capture.read()
            if not ok or frame is None:
                self.last_error = "camera_frame_read_failed"
                self.last_capture_backend = "fallback"
                self.last_capture_error = "camera_frame_read_failed"
                return None, ["camera_frame_read_failed"]
            self.last_error = None
            self.last_capture_backend = "opencv"
            self.last_capture_error = None
            self._set_last_frame(frame, [])
            return frame, []
        finally:
            capture.release()

    def evidence_frame_copy(self):
        """Return the latest camera frame for a non-control evidence writer.

        The copy is intentionally read-only and does not open a device, alter
        capture settings, or wait for a new frame.
        """
        with self.frame_lock:
            if self.last_frame is None:
                return None, None
            return self.last_frame.copy(), self.last_frame_at

    def live_preview_frame(self):
        """Return the latest frame from one profile-owned capture worker.

        Browser previews, inference polling and evidence readers must not each
        open/read the same UVC device independently. The worker is the sole
        continuous camera reader; consumers receive copies of its latest
        frame without contending for the V4L2 handle.
        """
        if self.profile.source_type == "mock":
            return self.read_frame()
        decision = self._camera_source_decision()
        path = decision["capture_device"]
        if self._is_persistent_capture_path(path):
            self._ensure_capture_worker(path)
            deadline = time.monotonic() + 0.6
            while time.monotonic() < deadline:
                frame, warnings = self._cached_frame(max_age_s=0.5)
                if frame is not None:
                    return frame, warnings
                time.sleep(0.01)
            if os.name == "nt" and isinstance(path, str) and path.startswith("camera-index:"):
                # Never fall through to a backend-owned DirectShow open. The
                # isolated child is the only process allowed to touch the UVC
                # driver; callers can retry after warmup without risking a
                # second owner or a native hot-unplug crash.
                return None, ["windows_camera_worker_warming"]
        return self.read_frame()

    def _read_frame_opencv_persistent(self, path: str):
        if cv2 is None or not self._is_persistent_capture_path(path):
            return None, []
        key = (path, self.profile.width, self.profile.height, self.profile.fps, self.profile.pixel_format)
        with self.capture_lock:
            if self.capture is None or self.capture_key != key:
                self._release_capture_locked()
                self._configure_v4l2_device(path)
                source, backend = self._opencv_capture_source(path)
                capture = cv2.VideoCapture(source, backend)
                if self.profile.pixel_format == "MJPG":
                    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                elif self.profile.pixel_format == "YUYV":
                    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.profile.width)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.profile.height)
                capture.set(cv2.CAP_PROP_FPS, self.profile.fps)
                if not capture.isOpened():
                    capture.release()
                    self.last_error = "camera_open_failed"
                    self.last_capture_backend = "fallback"
                    self.last_capture_error = f"opencv_persistent_open_failed:{path}"
                    return None, [f"opencv_persistent_open_failed:{path}"]
                self.capture = capture
                self.capture_key = key
            ok, frame = self.capture.read()
            if not ok or frame is None:
                self._release_capture_locked()
                self.last_error = "camera_frame_read_failed"
                self.last_capture_backend = "fallback"
                self.last_capture_error = "opencv_persistent_frame_read_failed"
                return None, ["opencv_persistent_frame_read_failed"]
            self.last_error = None
            self.last_capture_backend = "opencv"
            self.last_capture_error = None
            self._set_last_frame(frame, ["opencv persistent capture used for real camera"])
            return frame, ["opencv persistent capture used for real camera"]

    def _release_capture(self) -> None:
        self._stop_capture_worker()
        with self.capture_lock:
            self._release_capture_locked()

    def _release_capture_locked(self) -> None:
        if self.capture is not None:
            try:
                self.capture.release()
            except Exception:
                pass
        self.capture = None
        self.capture_key = None

    def _ensure_capture_worker(self, path: str) -> None:
        key = (path, self.profile.width, self.profile.height, self.profile.fps, self.profile.pixel_format)
        if self.capture_worker_key == key and self._capture_worker_running():
            return
        self._stop_capture_worker()
        self.capture_worker_stop.clear()
        self.capture_worker_key = key
        isolated_windows_camera = os.name == "nt" and path.startswith("camera-index:")
        self.capture_worker_thread = threading.Thread(
            target=self._windows_isolated_capture_worker if isolated_windows_camera else self._capture_worker,
            args=(path, key),
            name="camera-runtime-isolated-bridge" if isolated_windows_camera else "camera-runtime-capture",
            daemon=True,
        )
        self.capture_worker_thread.start()

    def _capture_worker_running(self) -> bool:
        return self.capture_worker_thread is not None and self.capture_worker_thread.is_alive()

    def _stop_capture_worker(self) -> None:
        worker = self.capture_worker_thread
        if worker is None:
            return
        self.capture_worker_stop.set()
        process = self.capture_worker_process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
        if worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout=1.0)
        self.capture_worker_process = None
        self.capture_worker_thread = None
        self.capture_worker_key = None
        self.capture_worker_stop.clear()

    def _capture_worker(self, path: str, key: tuple) -> None:
        target_interval = 1.0 / max(float(self.profile.fps or 30), 1.0)
        while not self.capture_worker_stop.is_set() and self.capture_worker_key == key:
            started = time.perf_counter()
            frame, warnings = self._read_frame_opencv_persistent(path)
            if frame is not None:
                self._set_last_frame(frame, warnings)
            wait_s = max(0.001, target_interval - (time.perf_counter() - started))
            self.capture_worker_stop.wait(wait_s)

    def _windows_isolated_capture_worker(self, path: str, key: tuple) -> None:
        """Keep unstable Windows UVC/OpenCV code outside the backend process.

        Some DirectShow drivers terminate the process with 0xC0000005 when a
        live USB camera is removed. The child owns VideoCapture; the backend
        only decodes its atomic latest-frame JPEG, so Gateway/UI stay alive.
        """
        try:
            camera_index = int(path.split(":", 1)[1])
        except (IndexError, ValueError):
            self.last_error = "camera_index_invalid"
            self.last_capture_error = f"camera_index_invalid:{path}"
            return
        runtime_dir = project_root() / "config" / "runtime" / "windows_camera_worker"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        frame_path = runtime_dir / "latest.jpg"
        frame_path.unlink(missing_ok=True)
        worker_script = Path(__file__).with_name("windows_camera_capture_worker.py")
        if not self._windows_profile_camera_present():
            self.last_error = "camera_device_removed"
            self.last_capture_backend = "fallback"
            self.last_capture_error = "windows_camera_pnp_identity_missing"
            self.last_warnings = [self.last_capture_error]
            return
        command = [
            sys.executable,
            str(worker_script),
            "--index", str(camera_index),
            "--width", str(int(self.profile.width)),
            "--height", str(int(self.profile.height)),
            "--fps", str(int(self.profile.fps)),
            "--pixel-format", str(self.profile.pixel_format),
            "--output", str(frame_path),
        ]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.capture_worker_process = process
        last_mtime_ns = -1
        worker_started_at = time.monotonic()
        last_frame_received_at: float | None = None
        last_presence_check_at = 0.0
        presence_process: subprocess.Popen | None = None
        identity = self.profile.stable_path or ""
        identity_match = re.search(r"VID_[0-9A-Fa-f]{4}&PID_[0-9A-Fa-f]{4}", identity)
        presence_script = None
        if identity_match is not None:
            token = identity_match.group(0).upper()
            presence_script = (
                f"if (@(Get-PnpDevice -PresentOnly | Where-Object InstanceId -Like '*{token}*').Count -gt 0) "
                "{ '1' } else { '0' }"
            )
        while not self.capture_worker_stop.is_set() and self.capture_worker_key == key:
            return_code = process.poll()
            if return_code is not None:
                self.last_error = "camera_capture_process_stopped"
                self.last_capture_backend = "fallback"
                self.last_capture_error = f"windows_camera_capture_process_exit:{return_code}"
                self.last_warnings = [self.last_capture_error]
                break
            try:
                stat = frame_path.stat()
                if stat.st_mtime_ns != last_mtime_ns and cv2 is not None:
                    # Read the JPEG bytes while holding the Windows file handle
                    # only for the copy.  cv2.imread may keep the destination
                    # open long enough to repeatedly collide with the producer's
                    # atomic os.replace(), reducing a 30 FPS UVC stream to a few
                    # visible updates per second and intermittently tripping the
                    # Gateway CAMERA_STALE gate.
                    encoded = frame_path.read_bytes()
                    frame = None
                    if encoded and np is not None:
                        frame = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        last_mtime_ns = stat.st_mtime_ns
                        self.last_error = None
                        self.last_capture_backend = "opencv"
                        self.last_capture_error = None
                        self.last_warnings = []
                        self._set_last_frame(frame, ["isolated Windows camera capture"])
                        last_frame_received_at = time.monotonic()
            except OSError:
                pass
            now = time.monotonic()
            if presence_process is not None and presence_process.poll() is not None:
                stdout, _stderr = presence_process.communicate()
                camera_present = presence_process.returncode == 0 and stdout.strip().endswith("1")
                presence_process = None
                if not camera_present:
                    self.last_error = "camera_device_removed"
                    self.last_capture_backend = "fallback"
                    self.last_capture_error = "windows_camera_pnp_identity_missing"
                    self.last_warnings = [self.last_capture_error]
                    process.terminate()
                    try:
                        process.wait(timeout=0.75)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
            if presence_script is not None and presence_process is None and now - last_presence_check_at >= 1.0:
                last_presence_check_at = now
                # PnP enumeration can take 0.5-0.7 s on Windows. Run it
                # asynchronously so stable-identity checks never pause frame
                # ingestion long enough to create a false CAMERA_STALE gate.
                presence_process = subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", presence_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            initial_timeout_s = 6.0
            live_stall_timeout_s = 1.5
            if (
                (last_frame_received_at is None and now - worker_started_at > initial_timeout_s)
                or (last_frame_received_at is not None and now - last_frame_received_at > live_stall_timeout_s)
            ):
                self.last_error = "camera_capture_stalled"
                self.last_capture_backend = "fallback"
                self.last_capture_error = "windows_camera_capture_stalled"
                self.last_warnings = [self.last_capture_error]
                process.terminate()
                try:
                    process.wait(timeout=0.75)
                except subprocess.TimeoutExpired:
                    process.kill()
                break
            self.capture_worker_stop.wait(0.02)
        if presence_process is not None and presence_process.poll() is None:
            presence_process.terminate()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
        if self.capture_worker_process is process:
            self.capture_worker_process = None

    def _windows_profile_camera_present(self) -> bool:
        if os.name != "nt":
            return True
        identity = self.profile.stable_path or ""
        match = re.search(r"VID_[0-9A-Fa-f]{4}&PID_[0-9A-Fa-f]{4}", identity)
        if match is None:
            return False
        token = match.group(0).upper()
        script = (
            f"if (@(Get-PnpDevice -PresentOnly | Where-Object InstanceId -Like '*{token}*').Count -gt 0) "
            "{ '1' } else { '0' }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=1.5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and result.stdout.strip().endswith("1")

    def _set_last_frame(self, frame, warnings: list[str]) -> None:
        with self.frame_lock:
            self.last_frame = frame.copy()
            self.last_frame_at = time.time()
            self.last_frame_warnings = warnings

    def _cached_frame(self, max_age_s: float | None) -> tuple[object | None, list[str]]:
        with self.frame_lock:
            if self.last_frame is None:
                return None, []
            age_s = time.time() - (self.last_frame_at or time.time())
            if max_age_s is not None and age_s > max_age_s:
                return None, [f"cached_real_frame_stale:{int(age_s * 1000)}ms"]
            return self.last_frame.copy(), [*self.last_frame_warnings, f"using_cached_real_frame:{int(age_s * 1000)}ms"]

    def _configure_v4l2_device(self, path: str) -> None:
        if not isinstance(path, str) or not path.startswith("/dev/"):
            return
        pixel_format = "MJPG" if self.profile.pixel_format in {"auto", "MJPG"} else self.profile.pixel_format
        command = [
            "v4l2-ctl",
            f"--device={path}",
            f"--set-fmt-video=width={int(self.profile.width)},height={int(self.profile.height)},pixelformat={pixel_format}",
            f"--set-parm={int(self.profile.fps)}",
        ]
        try:
            subprocess.run(command, check=False, capture_output=True, text=True, timeout=1.5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return
        self._apply_v4l2_controls(path)

    def _apply_v4l2_controls(self, path: str) -> None:
        controls: dict[str, int] = {}
        if self.profile.brightness is not None:
            controls["brightness"] = int(self.profile.brightness)
        if self.profile.contrast is not None:
            controls["contrast"] = int(self.profile.contrast)
        if self.profile.saturation is not None:
            controls["saturation"] = int(self.profile.saturation)
        if self.profile.sharpness is not None:
            controls["sharpness"] = int(self.profile.sharpness)
        if self.profile.gain is not None:
            controls["gain"] = int(self.profile.gain)
        if self.profile.white_balance_auto is not None:
            controls["white_balance_automatic"] = 1 if self.profile.white_balance_auto else 0
        if self.profile.white_balance_value is not None:
            controls["white_balance_temperature"] = int(self.profile.white_balance_value)
        if self.profile.exposure_auto is not None:
            controls["auto_exposure"] = 3 if self.profile.exposure_auto else 1
        if self.profile.exposure_value is not None:
            controls["exposure_time_absolute"] = int(self.profile.exposure_value)
        if not controls:
            return
        command = ["v4l2-ctl", f"--device={path}"]
        command.extend(f"--set-ctrl={name}={value}" for name, value in controls.items())
        try:
            subprocess.run(command, check=False, capture_output=True, text=True, timeout=1.5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return

    def _read_frame_ffmpeg(self, path: str):
        if cv2 is None or not isinstance(path, str) or not path.startswith("/dev/"):
            return None, []
        with tempfile.NamedTemporaryFile(prefix="istiklal_camera_frame_", suffix=".jpg", delete=False) as output:
            output_path = Path(output.name)
        input_format = {
            "MJPG": "mjpeg",
            "YUYV": "yuyv422",
            "auto": "mjpeg",
        }.get(self.profile.pixel_format, "mjpeg")
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "v4l2",
            "-input_format",
            input_format,
            "-video_size",
            f"{self.profile.width}x{self.profile.height}",
            "-i",
            path,
            "-frames:v",
            "1",
            "-update",
            "1",
            str(output_path),
        ]
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=3)
            if completed.returncode != 0:
                self.last_capture_backend = "fallback"
                self.last_capture_error = f"ffmpeg_frame_capture_failed:{completed.stderr.strip() or completed.returncode}"
                return None, [self.last_capture_error]
            frame = cv2.imread(str(output_path))
            if frame is None:
                self.last_capture_backend = "fallback"
                self.last_capture_error = "ffmpeg_frame_decode_failed"
                return None, ["ffmpeg_frame_decode_failed"]
            self.last_capture_backend = "ffmpeg"
            self.last_capture_error = None
            return frame, ["ffmpeg frame capture used for real camera"]
        except FileNotFoundError:
            self.last_capture_backend = "fallback"
            self.last_capture_error = "ffmpeg_not_available"
            return None, ["ffmpeg_not_available"]
        except subprocess.TimeoutExpired:
            self.last_capture_backend = "fallback"
            self.last_capture_error = "ffmpeg_frame_capture_timeout"
            return None, ["ffmpeg_frame_capture_timeout"]
        finally:
            try:
                output_path.unlink(missing_ok=True)
            except OSError:
                pass

    def mjpeg_stream(self):
        while True:
            frame, warnings = self.live_preview_frame()
            if frame is None or cv2 is None:
                placeholder = self._placeholder_frame("; ".join(warnings) or "camera frame unavailable")
                ok, encoded = cv2.imencode(".jpg", placeholder) if cv2 is not None else (False, None)
                if ok:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
                else:
                    yield b"--frame\r\nContent-Type: text/plain\r\n\r\ncamera frame unavailable\r\n"
            else:
                stream_frame = self._stream_frame(frame)
                ok, encoded = cv2.imencode(".jpg", stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
                else:
                    self.last_warnings = warnings + ["jpeg_encode_failed"]
                    yield b"--frame\r\nContent-Type: text/plain\r\n\r\njpeg encode failed\r\n"
            # The profile-owned worker captures continuously. This consumer
            # sleep paces encoding/network delivery without slowing capture or
            # monopolising the V4L2 lock when multiple browser panels exist.
            time.sleep(1 / max(self.profile.fps, 1))

    def _stream_frame(self, frame):
        if cv2 is None:
            return frame
        width = int(self.profile.stream_width or self.profile.width or frame.shape[1])
        height = int(self.profile.stream_height or self.profile.height or frame.shape[0])
        if width > 0 and height > 0 and (frame.shape[1] != width or frame.shape[0] != height):
            return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        return frame

    def _placeholder_frame(self, message: str):
        height = max(int(self.profile.stream_height or self.profile.height or 360), 240)
        width = max(int(self.profile.stream_width or self.profile.width or 640), 320)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (18, 24, 32)
        source_mode = str(self._camera_source_decision()["source_mode"])
        title = "CAMERA FRAME UNAVAILABLE" if source_mode == "CAMERA_UNAVAILABLE" else source_mode.replace("_", " ")
        cv2.putText(frame, title[:44], (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 220, 255), 2)
        cv2.putText(frame, message[:86], (24, 86), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1)
        cv2.putText(frame, "no_physical_command_generated=true", (24, height - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (120, 255, 160), 1)
        return frame

    def _camera_source_decision(self) -> dict[str, object]:
        if self.profile.source_type == "mock":
            return {
                "source_mode": "MOCK_OR_FIXTURE",
                "selected_device": "mock",
                "capture_device": None,
                "is_external_usb_camera": False,
                "is_laptop_camera": False,
                "hardware_presence_note": "MOCK/SURROGATE — NOT REAL CAMERA EVIDENCE",
            }
        configured = self.profile.device_path or self.profile.stable_path or self.profile.device_id
        if isinstance(configured, str) and configured.startswith("camera-index:"):
            present = any(item.device_path == configured for item in self.devices.inventory().cameras)
            if present:
                is_laptop = self.profile.source_type == "laptop"
                return {
                    "source_mode": "REAL_LAPTOP_CAMERA_LATEST_FRAME" if is_laptop else "REAL_USB_CAMERA_LATEST_FRAME",
                    "selected_device": configured,
                    "capture_device": configured,
                    "is_external_usb_camera": not is_laptop,
                    "is_laptop_camera": is_laptop,
                    "hardware_presence_note": "Windows camera present; live frame pending",
                }
        if isinstance(configured, str) and configured.startswith("/dev/") and Path(configured).exists():
            is_laptop = self._is_laptop_camera(configured)
            return {
                "source_mode": "REAL_LAPTOP_CAMERA_LATEST_FRAME" if is_laptop else "REAL_USB_CAMERA_LATEST_FRAME",
                "selected_device": configured,
                "capture_device": configured,
                "is_external_usb_camera": not is_laptop,
                "is_laptop_camera": is_laptop,
                "hardware_presence_note": "camera present; live frame pending",
            }
        available = sorted(glob.glob("/dev/video*"))
        if available:
            laptop = next((path for path in available if self._is_laptop_camera(path)), available[0])
            missing_note = f"configured camera {configured or 'not_selected'} not present; using laptop camera for development"
            return {
                "source_mode": "REAL_LAPTOP_CAMERA_LATEST_FRAME",
                "selected_device": laptop,
                "capture_device": laptop,
                "is_external_usb_camera": False,
                "is_laptop_camera": True,
                "hardware_presence_note": missing_note,
            }
        return {
            "source_mode": "CAMERA_UNAVAILABLE",
            "selected_device": configured,
            "capture_device": None,
            "is_external_usb_camera": False,
            "is_laptop_camera": False,
            "hardware_presence_note": "CAMERA_UNAVAILABLE; external USB and laptop camera not present",
        }

    @staticmethod
    def _is_laptop_camera(path: str) -> bool:
        return path.endswith("/video0") or path.endswith("/video1")

    @staticmethod
    def _is_persistent_capture_path(path: object) -> bool:
        return isinstance(path, str) and (path.startswith("/dev/") or path.startswith("camera-index:"))

    @staticmethod
    def _opencv_capture_source(path: str) -> tuple[str | int, int]:
        if path.startswith("camera-index:"):
            return int(path.split(":", 1)[1]), cv2.CAP_DSHOW
        return path, cv2.CAP_V4L2

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump(self.profile.model_dump(mode="json"), sort_keys=False), encoding="utf-8")

    def _load_persisted_profile(self) -> None:
        active_models_path = Path(self.config.models.active_models_file)
        if active_models_path.is_absolute() and not active_models_path.is_relative_to(project_root()):
            return
        if not self.path.exists():
            return
        try:
            loaded = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
            self.profile = CameraRuntimeProfile(**loaded)
            self.last_error = None
        except Exception as exc:
            self.last_error = f"camera_profile_load_failed:{exc}"
            self.last_warnings = [self.last_error]

    def _recommendation_score(self) -> int:
        if self.profile.source_type == "mock":
            return 50
        score = 40 if self.profile.source_type == "usb" else 25
        if self.profile.stable_path:
            score += 20
        if self.last_error is None:
            score += 20
        if self.last_probe_result:
            score += 10
        return min(score, 100)

    def _event(self, event_type: str, payload: dict, message: str, level: LogLevel = LogLevel.INFO) -> None:
        payload = {**payload, "no_physical_command_generated": True}
        self.last_event = (event_type, payload)
        self.logger.emit(level, "CAMERA_RUNTIME", message, payload)
