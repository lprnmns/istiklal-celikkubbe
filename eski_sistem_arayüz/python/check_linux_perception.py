#!/usr/bin/env python3
"""Linux perception smoke test for the legacy tracker.

This script reads one camera frame and runs the OpenCV color detector only.
It does not open serial ports and does not send any hardware command.
"""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import cv2

from config import DetectionConfig
from settings_manager import SettingsManager
from yolo_detector import ColorDetector, YOLO_AVAILABLE


def main() -> int:
    settings = SettingsManager.load_settings()
    source = settings.get("camera_index", "/dev/video2")
    width, height = [int(v) for v in settings.get("resolution", "1280x720").split("x", 1)]
    fps = int(settings.get("fps", 30))

    cap = cv2.VideoCapture(source, cv2.CAP_V4L2 if str(source).startswith("/dev/") else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame = None
    for _ in range(20):
        ok, candidate = cap.read()
        if ok and candidate is not None:
            frame = candidate
            break
        time.sleep(0.05)
    cap.release()

    if frame is None and str(source).startswith("/dev/"):
        fallback_url = os.environ.get("LEGACY_TRACKER_CAMERA_FALLBACK_URL", "http://127.0.0.1:8005/api/camera/stream.mjpg")
        cap = cv2.VideoCapture(fallback_url)
        for _ in range(20):
            ok, candidate = cap.read()
            if ok and candidate is not None:
                frame = candidate
                source = fallback_url
                break
            time.sleep(0.05)
        cap.release()

    if frame is None and str(source).startswith("/dev/"):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "v4l2",
                "-input_format",
                "mjpeg",
                "-video_size",
                f"{width}x{height}",
                "-i",
                str(source),
                "-frames:v",
                "1",
                "-update",
                "1",
                tmp.name,
            ]
            try:
                subprocess.run(cmd, check=True, timeout=4)
                frame = cv2.imread(tmp.name)
            except Exception:
                frame = None

    result = {
        "camera_source": source,
        "requested_width": width,
        "requested_height": height,
        "requested_fps": fps,
        "frame_read": frame is not None,
        "yolo_available": YOLO_AVAILABLE,
        "detector": "legacy_opencv_color_detector",
        "detections_count": 0,
        "detections": [],
        "advisory_only": True,
        "physical_command_enabled": False,
        "serial_tx_enabled": False,
        "no_physical_command_generated": True,
    }
    if frame is not None:
        detector = ColorDetector(DetectionConfig())
        detections = detector.detect(frame)
        result["actual_width"] = int(frame.shape[1])
        result["actual_height"] = int(frame.shape[0])
        result["detections_count"] = len(detections)
        result["detections"] = [
            {
                "class_id": int(d.class_id),
                "x": round(float(d.x), 2),
                "y": round(float(d.y), 2),
                "w": round(float(d.w), 2),
                "h": round(float(d.h), 2),
                "confidence": round(float(d.confidence), 3),
            }
            for d in detections[:20]
        ]

    out_dir = Path(__file__).resolve().parents[1] / "reports"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "linux_perception_smoke_result.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["frame_read"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
