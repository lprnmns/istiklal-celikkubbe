"""Enumerate Windows camera indexes and record real capture performance.

No detector/model is loaded. Each index is opened sequentially and released
before the next one, so this tool also checks that camera ownership is clean.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def probe(
    index: int,
    output_dir: Path,
    width: int,
    height: int,
    frames: int,
    backend_id: int,
    backend_name: str,
) -> dict:
    result: dict[str, object] = {"index": index, "opened": False}
    camera = cv2.VideoCapture(index, backend_id)
    try:
        if not camera.isOpened():
            result["error"] = "CAMERA_OPEN_FAILED"
            return result

        result["opened"] = True
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        camera.set(cv2.CAP_PROP_FPS, 30)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        read_ms: list[float] = []
        last_frame: np.ndarray | None = None
        started = time.perf_counter()
        failures = 0
        for _ in range(frames):
            t0 = time.perf_counter()
            ok, frame = camera.read()
            read_ms.append((time.perf_counter() - t0) * 1000.0)
            if not ok or frame is None:
                failures += 1
                continue
            last_frame = frame
        elapsed = time.perf_counter() - started

        result.update(
            {
                "requested": {"width": width, "height": height, "fps": 30, "fourcc": "MJPG"},
                "actual": {
                    "width": int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps_property": float(camera.get(cv2.CAP_PROP_FPS)),
                    "fourcc": int(camera.get(cv2.CAP_PROP_FOURCC)),
                },
                "frames_requested": frames,
                "frames_ok": frames - failures,
                "frames_failed": failures,
                "observed_fps": (frames - failures) / elapsed if elapsed > 0 else 0.0,
                "read_ms_mean": float(np.mean(read_ms)) if read_ms else None,
                "read_ms_p95": float(np.percentile(read_ms, 95)) if read_ms else None,
            }
        )

        if last_frame is not None:
            frame = last_frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sample = output_dir / f"camera_{index}_{backend_name.lower()}_sample.jpg"
            cv2.imwrite(str(sample), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result.update(
                {
                    "sample_path": str(sample),
                    "mean_brightness": float(gray.mean()),
                    "black_pixel_ratio": float(np.mean(gray < 8)),
                    "focus_laplacian_variance": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
                }
            )
        return result
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    finally:
        camera.release()


def main() -> int:
    parser = argparse.ArgumentParser(description="Windows DirectShow camera HIL probe")
    parser.add_argument("--max-index", type=int, default=5)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--backend", choices=("dshow", "msmf", "any"), default="dshow")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/camera_probe"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    backend_id, backend_name = {
        "dshow": (cv2.CAP_DSHOW, "CAP_DSHOW"),
        "msmf": (cv2.CAP_MSMF, "CAP_MSMF"),
        "any": (cv2.CAP_ANY, "CAP_ANY"),
    }[args.backend]
    report = {
        "schema": "istiklal.hil.camera_probe.v1",
        "started_at": utc_now(),
        "backend": backend_name,
        "model_loaded": False,
        "cameras": [
            probe(
                index,
                args.output_dir,
                args.width,
                args.height,
                args.frames,
                backend_id,
                backend_name,
            )
            for index in range(args.max_index + 1)
        ],
        "finished_at": utc_now(),
    }
    report_path = args.output_dir / "camera_probe.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if any(item["opened"] for item in report["cameras"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
