"""Isolated Windows DirectShow frame producer.

This process intentionally contains no backend/Gateway state. If a vendor UVC
driver crashes OpenCV during hot-unplug, Windows terminates only this helper.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--fps", type=int, required=True)
    parser.add_argument("--pixel-format", default="MJPG")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    capture = cv2.VideoCapture(args.index, cv2.CAP_DSHOW)
    if args.pixel_format == "MJPG":
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    elif args.pixel_format == "YUYV":
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    capture.set(cv2.CAP_PROP_FPS, args.fps)
    if not capture.isOpened():
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    black_frames = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                failures += 1
                if failures >= 5:
                    return 3
                time.sleep(0.03)
                continue
            failures = 0
            bright_fraction = float((frame > 8).mean())
            if float(frame.mean()) < 2.0 and bright_fraction < 0.005:
                black_frames += 1
                if black_frames >= 15:
                    # Several Windows UVC drivers keep returning synthetic
                    # black frames after hot-unplug instead of failing read().
                    return 4
                time.sleep(0.01)
                continue
            black_frames = 0
            encoded_ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            if not encoded_ok:
                continue
            temporary = args.output.with_suffix(".jpg.tmp")
            try:
                temporary.write_bytes(encoded.tobytes())
                replaced = False
                for _attempt in range(10):
                    try:
                        os.replace(temporary, args.output)
                        replaced = True
                        break
                    except PermissionError:
                        # cv2.imread may briefly hold the destination on
                        # Windows. Dropping one frame is preferable to killing
                        # the isolated capture process.
                        time.sleep(0.005)
                if not replaced:
                    temporary.unlink(missing_ok=True)
            except OSError:
                temporary.unlink(missing_ok=True)
                time.sleep(0.01)
    finally:
        capture.release()


if __name__ == "__main__":
    raise SystemExit(main())
