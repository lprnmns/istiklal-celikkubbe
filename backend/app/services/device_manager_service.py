import glob
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from app.schemas.config import AppConfig
from app.schemas.device_manager import CameraCapability, CameraProbeResult, DeviceInventory, DeviceKind, ManagedDevice
from app.schemas.log import LogLevel
from app.services.log_service import JsonlLogService


class DeviceManagerService:
    def __init__(self, config: AppConfig, logger: JsonlLogService) -> None:
        self.config = config
        self.logger = logger
        self.last_inventory = DeviceInventory(devices=[], cameras=[], serial=[], pico_candidates=[])
        self.last_event: tuple[str, dict] | None = None

    def scan(self) -> DeviceInventory:
        self._event("devices.scan_started", {"no_physical_command_generated": True}, "Device scan started")
        devices: list[ManagedDevice] = []
        devices.extend(self._serial_devices())
        devices.extend(self._camera_devices())
        unique: dict[str, ManagedDevice] = {device.device_id: device for device in devices}
        devices = sorted(unique.values(), key=lambda item: (item.kind.value, item.device_path))
        cameras = [item for item in devices if item.kind == DeviceKind.CAMERA]
        serial = [item for item in devices if item.kind in {DeviceKind.SERIAL, DeviceKind.PICO_CANDIDATE}]
        pico_candidates = [item for item in serial if item.kind == DeviceKind.PICO_CANDIDATE]
        inventory = DeviceInventory(
            devices=devices,
            cameras=cameras,
            serial=serial,
            pico_candidates=pico_candidates,
            warnings=[] if devices else ["No serial or camera devices discovered."],
        )
        self.last_inventory = inventory
        self._event(
            "devices.scan_completed",
            {
                "device_count": len(devices),
                "camera_count": len(cameras),
                "serial_count": len(serial),
                "pico_candidate_count": len(pico_candidates),
                "no_physical_command_generated": True,
            },
            "Device scan completed",
        )
        for candidate in pico_candidates:
            self._event("devices.pico_candidate_found", candidate.model_dump(mode="json"), "Pico candidate found")
        return inventory

    def inventory(self) -> DeviceInventory:
        return self.last_inventory if self.last_inventory.devices else self.scan()

    def serial_devices(self) -> list[ManagedDevice]:
        return self.inventory().serial

    def cameras(self) -> list[ManagedDevice]:
        return self.inventory().cameras

    def pico_candidates(self) -> list[ManagedDevice]:
        return self.inventory().pico_candidates

    def camera_capabilities(self, device_id: str) -> CameraCapability:
        device = self._find_device(device_id)
        if device is None or device.kind != DeviceKind.CAMERA:
            return CameraCapability(
                device_id=device_id,
                device_path=device_id,
                warnings=["Camera device not found."],
                suggested_action="Refresh devices and select a listed camera.",
            )
        return self._probe_camera(device)

    def probe_camera(self, device_id: str) -> CameraProbeResult:
        device = self._find_device(device_id)
        if device is None or device.kind != DeviceKind.CAMERA:
            return CameraProbeResult(
                accepted=False,
                warnings=["Camera device not found."],
                suggested_action="Refresh devices and select a listed camera.",
            )
        capability = self._probe_camera(device)
        result = CameraProbeResult(
            accepted=capability.open_ok,
            device=device,
            capabilities=capability,
            warnings=capability.warnings,
            suggested_action=capability.suggested_action,
        )
        self._event("devices.camera_probe", result.model_dump(mode="json"), "Camera probe completed", LogLevel.INFO if result.accepted else LogLevel.WARN)
        return result

    def _serial_devices(self) -> list[ManagedDevice]:
        devices: list[ManagedDevice] = []
        try:
            from serial.tools import list_ports  # type: ignore[import-not-found]

            for port in list_ports.comports():
                text = " ".join(str(item or "") for item in (port.device, port.description, port.hwid, port.manufacturer))
                score = self._pico_score(text)
                vid = f"{port.vid:04x}" if getattr(port, "vid", None) is not None else self._extract_usb_id(port.hwid or "", "VID")
                pid = f"{port.pid:04x}" if getattr(port, "pid", None) is not None else self._extract_usb_id(port.hwid or "", "PID")
                devices.append(
                    ManagedDevice(
                        device_id=self._id("serial", port.device),
                        device_path=port.device,
                        stable_path=self._stable_serial_path(port.device),
                        kind=DeviceKind.PICO_CANDIDATE if score >= 50 else DeviceKind.SERIAL,
                        name=port.device,
                        description=port.description or port.device,
                        manufacturer=port.manufacturer,
                        vid=vid,
                        pid=pid,
                        serial_number=getattr(port, "serial_number", None),
                        bus_path=getattr(port, "location", None),
                        permissions_ok=True if os.name == "nt" else os.access(port.device, os.R_OK | os.W_OK),
                        candidate_score=score,
                        recommendation_score=score,
                        warnings=[] if score >= 50 else ["Serial device is not verified as Pico."],
                        suggested_action="Use read-only telemetry verification before trusting this Pico candidate." if score >= 50 else "Leave unselected unless physically confirmed.",
                    )
                )
        except Exception as exc:
            self._event("devices.scan_warning", {"warning": f"pyserial_unavailable:{exc}"}, "pyserial port scan unavailable", LogLevel.WARN)

        seen = {device.device_path for device in devices}
        for path in sorted(set(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))):
            if path in seen:
                continue
            score = self._pico_score(path)
            devices.append(
                ManagedDevice(
                    device_id=self._id("serial", path),
                    device_path=path,
                    stable_path=self._stable_serial_path(path),
                    kind=DeviceKind.PICO_CANDIDATE if score >= 30 else DeviceKind.SERIAL,
                    name=Path(path).name,
                    description="glob detected serial device",
                    permissions_ok=os.access(path, os.R_OK | os.W_OK),
                    candidate_score=score,
                    recommendation_score=score,
                    warnings=[] if score >= 30 else ["Serial device is not identified as Pico."],
                    suggested_action="Verify with telemetry-only firmware.",
                )
            )
        return devices

    def _camera_devices(self) -> list[ManagedDevice]:
        if os.name == "nt":
            return self._windows_camera_devices()
        by_id = self._video_by_id()
        devices: list[ManagedDevice] = []
        for path in sorted(glob.glob("/dev/video*")):
            permissions_ok = os.access(path, os.R_OK | os.W_OK)
            stable = by_id.get(os.path.realpath(path))
            name = Path(stable).name if stable else Path(path).name
            devices.append(
                ManagedDevice(
                    device_id=self._id("camera", path),
                    device_path=path,
                    stable_path=stable,
                    kind=DeviceKind.CAMERA,
                    name=name,
                    description=self._v4l2_name(path) or "Video capture device",
                    driver="v4l2",
                    permissions_ok=permissions_ok,
                    candidate_score=0,
                    recommendation_score=self._camera_recommendation(path, stable, permissions_ok),
                    warnings=[] if permissions_ok else ["Permission denied for camera device."],
                    suggested_action=None if permissions_ok else "Add user to video group or close permission blocker.",
                )
            )
        return devices

    def _windows_camera_devices(self) -> list[ManagedDevice]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Get-PnpDevice -PresentOnly | Where-Object { $_.Class -in @('Camera','Image') } | "
            "Select-Object FriendlyName,InstanceId,Manufacturer | ConvertTo-Json -Compress",
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
            raw = completed.stdout.strip()
            payload = json.loads(raw) if raw else []
        except (FileNotFoundError, subprocess.SubprocessError, json.JSONDecodeError):
            payload = []
        if isinstance(payload, dict):
            payload = [payload]

        # Get-PnpDevice does not return cameras in the same order used by
        # OpenCV/DirectShow and DirectShow indexes can contain gaps or virtual
        # cameras.  Sort physical PnP devices laptop-first, then bind them to
        # the first indexes that actually yield a frame.  This prevents a PnP
        # list of two cameras from being blindly labelled camera-index:0/1
        # when the real capture indexes are, for example, 1/2.
        if isinstance(payload, list):
            payload = sorted(
                payload,
                key=lambda item: (
                    0
                    if re.search(
                        r"integrated|internal|built.?in|front|user.?facing|uvc.?webcam|usb2\.0.*webcam",
                        str(item.get("FriendlyName") or ""),
                        re.IGNORECASE,
                    )
                    else 1,
                    str(item.get("FriendlyName") or ""),
                ),
            )

        physical_count = len(payload) if isinstance(payload, list) else 0
        capture_indices = self._windows_capture_indices(physical_count)
        if len(capture_indices) < physical_count:
            used = set(capture_indices)
            capture_indices.extend(index for index in range(max(physical_count + 3, 6)) if index not in used)

        devices: list[ManagedDevice] = []
        for ordinal, item in enumerate(payload if isinstance(payload, list) else []):
            index = capture_indices[ordinal]
            friendly = str(item.get("FriendlyName") or f"Windows Camera {index}")
            instance_id = str(item.get("InstanceId") or "")
            usb_match = re.search(r"VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})", instance_id)
            device_path = f"camera-index:{index}"
            integrated = bool(re.search(
                r"integrated|internal|built.?in|front|user.?facing|uvc.?webcam|usb2\.0.*webcam",
                friendly,
                re.IGNORECASE,
            ))
            external = not integrated and bool(re.search(r"usb|external|hd camera", friendly, re.IGNORECASE))
            devices.append(
                ManagedDevice(
                    device_id=f"camera_index_{index}",
                    device_path=device_path,
                    stable_path=instance_id or None,
                    kind=DeviceKind.CAMERA,
                    name=friendly,
                    description=f"{friendly} · OpenCV index {index}",
                    manufacturer=str(item.get("Manufacturer") or "") or None,
                    vid=usb_match.group(1).lower() if usb_match else None,
                    pid=usb_match.group(2).lower() if usb_match else None,
                    bus_path=instance_id or None,
                    driver="dshow",
                    permissions_ok=True,
                    candidate_score=0,
                    recommendation_score=90 if external else 65,
                    warnings=[],
                    suggested_action="Use the external USB camera for turret capture." if external else "Laptop camera is suitable for development tests.",
                )
            )
        return devices

    @staticmethod
    def _windows_capture_indices(required_count: int, max_index: int = 5) -> list[int]:
        if required_count <= 0:
            return []
        # Never load DirectShow camera drivers in the long-lived backend while
        # enumerating indexes. Some virtual camera drivers (observed with
        # NVIDIA Broadcast VCAMDS) can raise native heap corruption that Python
        # cannot catch. Each candidate is therefore opened in a disposable
        # child; a crash/timeout rejects only that index and keeps the API alive.
        discovered: list[int] = []
        for index in range(max_index + 1):
            if DeviceManagerService.windows_camera_path_responds(f"camera-index:{index}"):
                discovered.append(index)
                if len(discovered) >= required_count:
                    break
        return discovered

    @staticmethod
    def windows_camera_path_responds(device_path: str, timeout_s: float = 6.0) -> bool:
        if os.name != "nt" or not device_path.startswith("camera-index:"):
            return False
        try:
            index = int(device_path.split(":", 1)[1])
            completed = subprocess.run(
                [sys.executable, "-m", "app.services.windows_camera_probe_worker", "--index", str(index)],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return False
        return completed.returncode == 0 and completed.stdout.strip().endswith("1")

    def _probe_camera(self, device: ManagedDevice) -> CameraCapability:
        warnings: list[str] = []
        formats, resolutions, fps_values = self._v4l2_formats(device.device_path)
        open_ok = False
        frame_grab_ok = False
        actual_width = None
        actual_height = None
        actual_fps = None
        latency_ms = None
        started = time.time()
        try:
            import cv2  # type: ignore[import-not-found]

            source: str | int = device.device_path
            backend = cv2.CAP_ANY
            if os.name == "nt" and device.device_path.startswith("camera-index:"):
                source = int(device.device_path.split(":", 1)[1])
                backend = cv2.CAP_DSHOW
            capture = cv2.VideoCapture(source, backend)
            open_ok = bool(capture.isOpened())
            if open_ok:
                capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ok = False
                _frame = None
                for _ in range(3):
                    ok, _frame = capture.read()
                    if ok and _frame is not None:
                        break
                frame_grab_ok = bool(ok)
                actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or None
                actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or None
                actual_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0) or None
            capture.release()
        except Exception as exc:
            warnings.append(f"opencv_probe_unavailable:{exc}")
        latency_ms = round((time.time() - started) * 1000, 3)
        if not open_ok:
            warnings.append("Camera could not be opened or OpenCV is unavailable.")
        if open_ok and not frame_grab_ok:
            warnings.append("Camera opened but frame grab failed; device may be busy.")
        return CameraCapability(
            device_id=device.device_id,
            device_path=device.device_path,
            stable_path=device.stable_path,
            supported_resolutions=resolutions or ["640x480", "1280x720"],
            supported_fps=fps_values or [15, 30],
            supported_pixel_formats=formats or ["auto", "MJPG", "YUYV"],
            open_ok=open_ok,
            frame_grab_ok=frame_grab_ok,
            actual_width=actual_width,
            actual_height=actual_height,
            actual_fps=actual_fps,
            latency_ms=latency_ms,
            warnings=warnings,
            suggested_action=None if open_ok else "Select mock camera or verify permissions/device availability.",
        )

    def _find_device(self, device_id: str) -> ManagedDevice | None:
        return next((device for device in self.inventory().devices if device.device_id == device_id), None)

    def _camera_recommendation(self, path: str, stable: str | None, permissions_ok: bool) -> int:
        score = 35 if path.endswith("video0") else 50
        if stable:
            score += 20
        if permissions_ok:
            score += 20
        else:
            score -= 30
        return max(0, min(score, 100))

    @staticmethod
    def _id(prefix: str, path: str) -> str:
        safe = path.strip("/").replace("/", "_").replace(".", "_").replace("-", "_")
        return f"{prefix}_{safe}"

    @staticmethod
    def _pico_score(text: str) -> int:
        lowered = text.lower()
        score = 0
        if "pico" in lowered:
            score += 55
        if any(token in lowered for token in ("rp2040", "rp2350", "raspberry pi")):
            score += 35
        if "2e8a" in lowered:
            # Raspberry Pi's official USB vendor ID is sufficient to present
            # the port as a Pico candidate; handshake still verifies identity.
            score += 55
        if "ttyacm" in lowered:
            score += 20
        if "ttyusb" in lowered:
            score += 10
        return min(score, 100)

    @staticmethod
    def _extract_usb_id(hwid: str, key: str) -> str | None:
        match = re.search(rf"{key}:PID=([0-9A-Fa-f]{{4}}):([0-9A-Fa-f]{{4}})", hwid)
        if match:
            return match.group(1 if key == "VID" else 2).lower()
        return None

    @staticmethod
    def _stable_serial_path(device_path: str) -> str | None:
        for path in glob.glob("/dev/serial/by-id/*"):
            if os.path.realpath(path) == os.path.realpath(device_path):
                return path
        return None

    @staticmethod
    def _video_by_id() -> dict[str, str]:
        mapping: dict[str, str] = {}
        for path in glob.glob("/dev/v4l/by-id/*"):
            mapping[os.path.realpath(path)] = path
        return mapping

    @staticmethod
    def _v4l2_name(device_path: str) -> str | None:
        try:
            result = subprocess.run(["v4l2-ctl", "-d", device_path, "--info"], capture_output=True, text=True, timeout=1.5, check=False)
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        for line in result.stdout.splitlines():
            if "Card type" in line:
                return line.split(":", 1)[-1].strip()
        return None

    @staticmethod
    def _v4l2_formats(device_path: str) -> tuple[list[str], list[str], list[int]]:
        try:
            result = subprocess.run(["v4l2-ctl", "-d", device_path, "--list-formats-ext"], capture_output=True, text=True, timeout=2, check=False)
        except (FileNotFoundError, subprocess.SubprocessError):
            return [], [], []
        formats = sorted(set(re.findall(r"'([A-Z0-9]{4})'", result.stdout)))
        resolutions = sorted(set(re.findall(r"Size: Discrete ([0-9]+x[0-9]+)", result.stdout)))
        fps_values = sorted({int(round(float(value))) for value in re.findall(r"Interval: Discrete [^(]+\\(([0-9.]+) fps\\)", result.stdout)})
        return formats, resolutions, fps_values

    def _event(self, event_type: str, payload: dict, message: str, level: LogLevel = LogLevel.INFO) -> None:
        payload = {**payload, "no_physical_command_generated": True}
        self.last_event = (event_type, payload)
        self.logger.emit(level, "DEVICES", message, payload)
