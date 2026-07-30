from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--backend", choices=("dshow", "msmf", "any"), default="dshow")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        print("0")
        return 1

    import cv2  # type: ignore[import-not-found]

    backend = {
        "dshow": cv2.CAP_DSHOW,
        "msmf": cv2.CAP_MSMF,
        "any": cv2.CAP_ANY,
    }[args.backend]
    capture = cv2.VideoCapture(args.index, backend)
    try:
        if not capture.isOpened():
            print("0")
            return 1
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        for _ in range(3):
            ok, frame = capture.read()
            if ok and frame is not None:
                if args.output is not None:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    cv2.imwrite(str(args.output), frame)
                print("1")
                return 0
        print("0")
        return 1
    finally:
        capture.release()


if __name__ == "__main__":
    raise SystemExit(main())
