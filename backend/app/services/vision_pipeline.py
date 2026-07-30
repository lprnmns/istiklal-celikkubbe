import time
from pathlib import Path

from app.schemas.vision import AimPoint, BalloonDetection, BBox, VisionConfigUpdate, VisionEvent, VisionStatus
from app.services.body_tracker_service import BodyTrackerService
from app.services.camera_service import CameraService
from app.services.storage_paths import resolve_project_path
from app.services.vision_service import VisionService

try:  # pragma: no cover - host dependent in release packages
    import cv2
    import numpy as np
except Exception:  # pragma: no cover
    cv2 = None
    np = None


EXTERNAL_FRAME_MAX_AGE_S = 0.5


class VisionPipeline:
    def __init__(self, camera: CameraService, vision: VisionService) -> None:
        self.camera = camera
        self.vision = vision
        self.camera_runtime = None
        self.vision_runtime = None
        self.surrogate = None
        self._yolo_models: dict[str, object] = {}
        self.body_tracker = BodyTrackerService()
        self.color_classifier = None
        self.stage3_range = None
        self._frame_id = 0
        self._last_yolo_event: VisionEvent | None = None
        self._last_yolo_at = 0.0
        self._last_external_frame_at = 0.0

    def start(self) -> VisionStatus:
        self.camera.start()
        self.vision.running = True
        self.latest()
        return self.vision.status()

    def stop(self) -> VisionStatus:
        self.vision.running = False
        self.vision.latest_event = None
        if self.surrogate is not None:
            self.surrogate.stop()
        self.camera.stop()
        return self.vision.status()

    def configure(self, config: VisionConfigUpdate) -> VisionStatus:
        return self.vision.configure(config)

    def latest(self) -> VisionEvent:
        # Status polling must never be an implicit camera/YOLO start command.
        # Only the visible Setup action (/api/vision/start) authorizes a run.
        if not self.vision.running:
            return VisionEvent(
                frame_id=0, timestamp_ms=int(time.time() * 1000), source="vision_standby",
                frame_width=0, frame_height=0, fps=0.0, preprocess_ms=0.0,
                inference_ms=0.0, postprocess_ms=0.0, total_latency_ms=0.0,
                body_detections=[], balloon_detections=[], aim_points=[],
                warnings=["VISION_NOT_STARTED"],
            )
        if self.vision_runtime is not None and self.surrogate is not None and self.camera_runtime is not None:
            if self.vision_runtime.profile.inference_adapter == "opencv_live_circle_surrogate":
                self.camera.start()
                self.vision.running = True
                event = self.surrogate.run(self.camera_runtime, self.vision_runtime.profile)
                self.vision.latest_event = event
                return event
            if self.vision_runtime.profile.inference_adapter == "ultralytics_yolo":
                if self._last_yolo_event is not None and self._last_yolo_event.frame_origin in {
                    "browser_upload",
                    "browser_frame_upload",
                } and time.monotonic() - self._last_external_frame_at <= EXTERNAL_FRAME_MAX_AGE_S:
                    self.vision.latest_event = self._last_yolo_event
                    return self._last_yolo_event
                if self._last_yolo_event is not None and self._last_yolo_event.frame_origin in {
                    "browser_upload",
                    "browser_frame_upload",
                }:
                    self._last_yolo_event = None
                self.camera.start()
                self.vision.running = True
                target_fps = min(float(getattr(self.vision_runtime.profile, "target_fps", 30.0) or 30.0), 30.0)
                min_interval_s = 1.0 / max(target_fps, 1.0)
                now = time.perf_counter()
                if self._last_yolo_event is not None and now - self._last_yolo_at < min_interval_s:
                    return self._last_yolo_event
                event = self._latest_ultralytics_event()
                self._last_yolo_event = event
                self._last_yolo_at = now
                self.vision.latest_event = event
                return event
        if not self.camera.mock.running:
            self.camera.start()
        return self.vision.next_event(
            source=self.camera.camera_mode,
            width=self.camera.config.camera.stream_width,
            height=self.camera.config.camera.stream_height,
        )

    def status(self) -> VisionStatus:
        return self.vision.status()

    def _latest_ultralytics_event(self) -> VisionEvent:
        started = time.perf_counter()
        self._frame_id += 1
        profile = self.vision_runtime.profile
        camera_status = self.camera_runtime.status()
        # Inference shares the profile-owned capture worker with preview and
        # evidence. On Windows, opening DirectShow here a second time bypasses
        # the hot-unplug isolation process and can either starve the preview or
        # crash the backend in the vendor UVC driver.
        frame, frame_warnings = self.camera_runtime.live_preview_frame()
        width = int(camera_status.actual_width or camera_status.requested_width or 640)
        height = int(camera_status.actual_height or camera_status.requested_height or 360)
        if frame is not None:
            height, width = int(frame.shape[0]), int(frame.shape[1])
        warnings = [
            "ULTRALYTICS YOLO ACTIVE",
            "ADVISORY ONLY",
            "no_physical_command_generated=true",
            *frame_warnings,
        ]
        return self._ultralytics_event_from_frame(
            frame=frame,
            width=width,
            height=height,
            started=started,
            profile=profile,
            warnings=warnings,
            source="live_camera_ultralytics_yolo",
            camera_source_kind="real_camera" if camera_status.profile.source_type != "mock" else "mock",
            camera_device_path=camera_status.profile.device_path or camera_status.profile.stable_path or camera_status.profile.device_id,
            frame_origin="real_capture" if camera_status.profile.source_type != "mock" else "mock_frame",
            camera_fps=float(camera_status.actual_fps_measured or camera_status.actual_fps or camera_status.requested_fps),
        )

    def latest_from_external_frame(
        self,
        frame,
        source: str,
        camera_source_kind: str,
        frame_origin: str,
        camera_device_path: str | None = None,
    ) -> VisionEvent:
        if self.vision_runtime is None:
            raise RuntimeError("vision_runtime_unavailable")
        started = time.perf_counter()
        self._frame_id += 1
        self.vision.running = True
        height, width = int(frame.shape[0]), int(frame.shape[1])
        event = self._ultralytics_event_from_frame(
            frame=frame,
            width=width,
            height=height,
            started=started,
            profile=self.vision_runtime.profile,
            warnings=[
                "ULTRALYTICS YOLO ACTIVE",
                "BROWSER CAMERA FRAME UPLOAD",
                "ADVISORY ONLY",
                "no_physical_command_generated=true",
            ],
            source=source,
            camera_source_kind=camera_source_kind,
            camera_device_path=camera_device_path,
            frame_origin=frame_origin,
            camera_fps=None,
        )
        self._last_yolo_event = event
        self._last_yolo_at = time.perf_counter()
        self._last_external_frame_at = time.monotonic()
        self.vision.latest_event = event
        return event

    def _ultralytics_event_from_frame(
        self,
        frame,
        width: int,
        height: int,
        started: float,
        profile,
        warnings: list[str],
        source: str,
        camera_source_kind: str,
        camera_device_path: str | None,
        frame_origin: str,
        camera_fps: float | None,
    ) -> VisionEvent:
        body_detections = []
        balloon_detections: list[BalloonDetection] = []
        inference_ms = 0.0
        model_specs = self._active_yolo_model_specs()
        if frame is None:
            warnings.append("real_camera_frame_unavailable")
        elif not model_specs:
            warnings.append("active_yolo_model_missing")
        else:
            try:
                frame_for_inference, preprocess_warnings = self._preprocess_frame_for_ultralytics(frame)
                warnings.extend(preprocess_warnings)
                resolved_device, device_reason = self.vision_runtime.resolve_device(profile)
                if resolved_device is None:
                    warnings.append(f"inference_device_unavailable:{device_reason}")
                    raise RuntimeError(device_reason)
                infer_started = time.perf_counter()
                infer_kwargs = {
                    "imgsz": profile.imgsz,
                    "conf": profile.conf,
                    "iou": profile.iou,
                    "max_det": profile.max_det,
                    "device": resolved_device,
                    "verbose": False,
                }
                if profile.half and resolved_device == "cuda":
                    infer_kwargs["half"] = True
                elif profile.half:
                    warnings.append("half_disabled_without_cuda")
                if profile.classes is not None:
                    infer_kwargs["classes"] = profile.classes
                completed_paths: set[str] = set()
                for spec in model_specs:
                    # One combined detector can populate both semantic types;
                    # do not execute the same heavyweight model twice.
                    if spec["path"] in completed_paths:
                        continue
                    completed_paths.add(spec["path"])
                    model = self._load_yolo_model(spec["path"])
                    # Setup's per-model threshold is the source of truth for
                    # live inference. The generic runtime `profile.conf`
                    # must not silently override the visible model slider.
                    model_kwargs = dict(infer_kwargs)
                    if spec["role"] == "balloon":
                        model_kwargs["conf"] = self.vision.balloon_conf_threshold
                    elif spec["role"] == "body":
                        model_kwargs["conf"] = self.vision.body_conf_threshold
                    else:
                        model_kwargs["conf"] = min(self.vision.body_conf_threshold, self.vision.balloon_conf_threshold)
                    results = model(frame_for_inference, **model_kwargs)
                    bodies, balloons, model_warnings = self._detections_from_results(
                        results,
                        width,
                        height,
                        model_id=spec["model_id"],
                        role=spec["role"],
                        class_names=spec["class_names"],
                    )
                    body_detections.extend(bodies)
                    balloon_detections.extend(balloons)
                    warnings.extend(model_warnings)
                inference_ms = round((time.perf_counter() - infer_started) * 1000, 3)
                warnings.append(f"inference_device:{resolved_device}")
                body_detections = self.body_tracker.update(body_detections)
                if self.color_classifier is not None and body_detections:
                    body_detections = self.color_classifier.classify_frame_bodies(
                        frame_for_inference,
                        self._frame_id,
                        body_detections,
                        balloon_detections,
                    )
                if self.stage3_range is not None and body_detections:
                    body_spec = next((item for item in model_specs if item["role"] in {"body", "combined"}), None)
                    body_detections = self.stage3_range.attach_estimates(
                        body_detections,
                        body_spec["model_id"] if body_spec else None,
                        body_spec["path"] if body_spec else None,
                    )
                if not balloon_detections:
                    # The former red-color fallback generated fixed 0.82
                    # pseudo-confidence boxes. It is useful only as an
                    # explicit test adapter, never alongside a selected YOLO
                    # model: it makes the visible confidence slider untrue.
                    warnings.append("ultralytics_yolo_empty")
            except Exception as exc:  # pragma: no cover - depends on local model/runtime
                warnings.append(f"ultralytics_inference_failed:{exc}")
        preprocess_ms = 1.0
        if inference_ms <= 0:
            inference_ms = round((time.perf_counter() - started) * 1000, 3)
        postprocess_ms = 0.8
        total_ms = round(preprocess_ms + inference_ms + postprocess_ms, 3)
        detector_fps = round(1000.0 / max(total_ms, 1.0), 2)
        event = VisionEvent(
            frame_id=self._frame_id,
            timestamp_ms=int(time.time() * 1000),
            source=source,
            frame_width=width,
            frame_height=height,
            fps=detector_fps,
            camera_fps=camera_fps,
            detector_fps=detector_fps,
            preprocess_ms=preprocess_ms,
            inference_ms=inference_ms,
            postprocess_ms=postprocess_ms,
            total_latency_ms=total_ms,
            total_ms=total_ms,
            camera_source_kind=camera_source_kind,
            camera_device_path=camera_device_path,
            frame_origin=frame_origin,
            detector_kind="ultralytics_yolo",
            body_detections=body_detections,
            balloon_detections=balloon_detections,
            aim_points=[AimPoint(id=det.id, x=det.center_x, y=det.center_y, source=det.source) for det in balloon_detections],
            warnings=warnings,
        )
        return event

    def _active_yolo_model_specs(self) -> list[dict]:
        """Return separate body/balloon model provenance, never a blind path."""
        profile = self.vision_runtime.profile
        specs: list[dict] = []
        seen_roles: set[str] = set()

        # Setup Center is the operator-visible source of truth.  A model
        # selected there must take precedence over a previously activated
        # registry model; otherwise the UI reports the new path as applied
        # while inference silently keeps running the old model.
        for role, path in (("body", self.vision.body_model_path), ("balloon", self.vision.balloon_model_path)):
            if not path:
                continue
            resolved_path = resolve_project_path(path)
            if not resolved_path.is_file():
                continue
            normalized_path = str(resolved_path)
            existing = next((item for item in specs if item["path"] == normalized_path), None)
            if existing is not None:
                existing["role"] = "combined"
            else:
                specs.append(
                    {
                        "role": role,
                        "model_id": f"setup_{role}_path",
                        "path": normalized_path,
                        "class_names": [],
                    }
                )
            seen_roles.add(role)

        # Registry activation is the fallback for roles for which Setup did
        # not provide a path.  This keeps engineering/package workflows
        # working without allowing a stale registry selection to override the
        # operator's current choice.
        for role, model_id in (("body", profile.active_body_model_id), ("balloon", profile.active_balloon_model_id)):
            if not model_id or role in seen_roles:
                continue
            try:
                model = self.vision_runtime.models.get_model(model_id)
            except KeyError:
                continue
            if not model.file_path or not Path(model.file_path).exists():
                continue
            existing = next((item for item in specs if item["path"] == str(model.file_path)), None)
            if existing is not None:
                # Package activation often selects a combined detector for
                # both slots.  Interpret it as combined rather than silently
                # throwing away the second semantic role.
                existing["role"] = "combined"
            else:
                specs.append(
                    {
                        "role": role,
                        "model_id": model.model_id,
                        "path": str(model.file_path),
                        "class_names": list(model.class_names),
                    }
                )
            seen_roles.add(role)
        return specs

    def _load_yolo_model(self, model_path: str):
        if model_path in self._yolo_models:
            return self._yolo_models[model_path]
        try:
            import torch

            torch.set_num_threads(4)
            torch.set_num_interop_threads(2)
        except Exception:
            pass
        from ultralytics import YOLO

        model = YOLO(model_path)
        self._yolo_models[model_path] = model
        return model

    def _preprocess_frame_for_ultralytics(self, frame):
        # Preserve the camera pixels used by the actual YOLO training path.
        # The old alpha/beta enhancement suppresses the weak `dusman`
        # response of eski_sistem_arayüz/models/yolo/best.pt on screen tests.
        return frame, ["ultralytics_raw_camera_frame"]

    def _legacy_color_balloon_detections(self, frame, width: int, height: int) -> list[BalloonDetection]:
        if cv2 is None or np is None or frame is None:
            return []
        blurred = cv2.GaussianBlur(frame, (9, 9), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 38, 35])
        upper_red1 = np.array([20, 255, 255])
        lower_red2 = np.array([160, 38, 35])
        upper_red2 = np.array([180, 255, 255])
        hsv_mask = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))
        # Laptop cameras often overexpose red balloons into pink/washed red.
        # Use a conservative red-dominance mask so YOLO-empty frames still
        # expose the physical red test targets without requiring hardware I/O.
        bgr = blurred.astype(np.int16)
        blue = bgr[:, :, 0]
        green = bgr[:, :, 1]
        red = bgr[:, :, 2]
        red_dominant = (
            (red > 95)
            & ((red - green) > 18)
            & ((red - blue) > 18)
            & (red > (green * 1.08))
            & (red > (blue * 1.08))
        )
        dominance_mask = (red_dominant.astype(np.uint8)) * 255
        mask = cv2.bitwise_or(hsv_mask, dominance_mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: list[BalloonDetection] = []
        frame_area = float(width * height)
        min_contour_area = max(140.0, frame_area * 0.00012)
        max_contour_area = frame_area * 0.04
        max_box_side = min(width, height) * 0.45
        min_box_side = min(width, height) * 0.012
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(contour)
            if area < min_contour_area or area > max_contour_area:
                continue
            perimeter = cv2.arcLength(contour, True)
            if perimeter <= 0:
                continue
            circularity = 4.0 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.5:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w <= 0 or h <= 0:
                continue
            if x <= 0 or y <= 0 or x + w >= width - 1 or y + h >= height - 1:
                continue
            if min(w, h) < min_box_side:
                continue
            if max(w, h) > max_box_side:
                continue
            extent = area / float(w * h)
            if extent < 0.35:
                continue
            aspect_ratio = float(w) / float(h)
            if not 0.55 < aspect_ratio < 1.8:
                continue
            x = max(0, min(width - 1, int(x)))
            y = max(0, min(height - 1, int(y)))
            w = max(1, min(width - x, int(w)))
            h = max(1, min(height - y, int(h)))
            detections.append(
                BalloonDetection(
                    id=len(detections) + 1,
                    confidence=0.82,
                    bbox=BBox(x=x, y=y, w=w, h=h, format="pixel"),
                    center_x=int(x + w / 2),
                    center_y=int(y + h / 2),
                    source="legacy_color_fallback",
                )
            )
        return detections

    def _detections_from_results(
        self,
        results,
        width: int,
        height: int,
        *,
        model_id: str,
        role: str,
        class_names: list[str],
    ) -> tuple[list, list[BalloonDetection], list[str]]:
        """Preserve ``box.cls`` semantics and reject unknown class mappings.

        Previously every YOLO box became a BalloonDetection.  That can make a
        class model look operational while deleting the very evidence A3
        needs.  The parser now has an explicit role plus registry provenance.
        """
        from app.schemas.vision import BodyDetection

        bodies: list[BodyDetection] = []
        balloons: list[BalloonDetection] = []
        warnings: list[str] = []
        body_id = 1
        balloon_id = 1
        registry_names = {index: self._normalise_class_name(name) for index, name in enumerate(class_names)}
        target_map = {
            self._normalise_class_name(name): int(class_id)
            for name, class_id in self.vision_runtime.profile.target_class_map.items()
        }
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            output_names = getattr(result, "names", {}) or {}
            for box in boxes:
                xyxy = self._box_values(box.xyxy[0])
                conf = self._box_scalar(box.conf[0]) if getattr(box, "conf", None) is not None else 0.0
                class_id = int(round(self._box_scalar(box.cls[0]))) if getattr(box, "cls", None) is not None else -1
                output_name = self._normalise_class_name(self._class_name_from_result(output_names, class_id))
                # A direct Setup-selected .pt has no registry metadata yet;
                # its embedded Ultralytics class name is then authoritative.
                registry_name = registry_names.get(class_id) or output_name
                if not registry_name:
                    warnings.append(f"model_class_id_unmapped:{model_id}:{class_id}")
                    continue
                if output_name and output_name != registry_name:
                    warnings.append(f"model_class_mapping_mismatch:{model_id}:{class_id}")
                    continue
                class_name = registry_name
                if target_map and class_name in target_map and target_map[class_name] != class_id:
                    warnings.append(f"runtime_target_class_map_mismatch:{model_id}:{class_name}:{class_id}")
                    continue
                x1, y1, x2, y2 = [int(round(value)) for value in xyxy]
                x1 = max(0, min(width - 1, x1))
                y1 = max(0, min(height - 1, y1))
                x2 = max(x1 + 1, min(width, x2))
                y2 = max(y1 + 1, min(height, y2))
                bbox = BBox(x=x1, y=y1, w=max(1, x2 - x1), h=max(1, y2 - y1), format="pixel")
                # Legacy field models label balloon teams as dost/dusman.
                # In the balloon slot they are real balloon observations; a
                # later association/IFF stage decides engagement eligibility.
                is_balloon = class_name in {"balloon", "dost", "dusman"}
                is_competition_body = class_name in {"f16", "helicopter", "ballistic_missile", "mini_micro_uav"}
                # Aşama 2 does not need class recognition, but it does need a
                # real generic carrier/body for balloon association.  Keep it
                # explicit rather than pretending an unknown A3 class is F16.
                is_generic_body = role == "body" and not is_balloon and not is_competition_body
                is_body = is_competition_body or is_generic_body
                if role == "body" and not is_body:
                    warnings.append(f"body_model_non_body_class_rejected:{model_id}:{class_name}")
                    continue
                if role == "balloon" and not is_balloon:
                    warnings.append(f"balloon_model_non_balloon_class_rejected:{model_id}:{class_name}")
                    continue
                if is_balloon:
                    # A balloon may be small at competition distance, so do
                    # not impose a large minimum area. Reject only geometry
                    # that cannot plausibly be the approximately round target
                    # and edge-truncated fragments that are unsafe to aim at.
                    aspect_ratio = float(bbox.w) / float(max(bbox.h, 1))
                    edge_truncated = x1 <= 0 or y1 <= 0 or x2 >= width or y2 >= height
                    if edge_truncated:
                        warnings.append(f"balloon_geometry_rejected_edge:{model_id}:{class_name}")
                        continue
                    if not 0.55 <= aspect_ratio <= 1.8:
                        warnings.append(f"balloon_geometry_rejected_aspect:{model_id}:{class_name}")
                        continue
                if is_body:
                    bodies.append(
                        BodyDetection(
                            id=body_id,
                            class_name=class_name if is_competition_body else "generic_target",
                            class_id=class_id,
                            confidence=round(conf, 3),
                            bbox=bbox,
                            source=f"ultralytics_yolo:body:{model_id}",
                        )
                    )
                    body_id += 1
                elif is_balloon:
                    balloons.append(
                        BalloonDetection(
                            id=balloon_id,
                            confidence=round(conf, 3),
                            bbox=bbox,
                            center_x=int((x1 + x2) / 2),
                            center_y=int((y1 + y2) / 2),
                            source=f"ultralytics_yolo:balloon:{model_id}",
                        )
                    )
                    balloon_id += 1
                else:
                    warnings.append(f"unsupported_competition_class:{model_id}:{class_name}")
        return bodies, balloons, sorted(set(warnings))

    @staticmethod
    def _box_values(value) -> list[float]:
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        if hasattr(value, "tolist"):
            value = value.tolist()
        return [float(item) for item in value]

    @staticmethod
    def _box_scalar(value) -> float:
        if hasattr(value, "detach"):
            value = value.detach().cpu().item()
        elif hasattr(value, "item"):
            value = value.item()
        return float(value)

    @staticmethod
    def _class_name_from_result(names, class_id: int) -> str:
        if isinstance(names, dict):
            return str(names.get(class_id, ""))
        if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
            return str(names[class_id])
        return ""

    @staticmethod
    def _normalise_class_name(value: str) -> str:
        normalised = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "f_16": "f16",
            "f16": "f16",
            "mini_micro_ua_v": "mini_micro_uav",
            "mini_micro_uav": "mini_micro_uav",
            "ballisticmissile": "ballistic_missile",
        }
        return aliases.get(normalised, normalised)
