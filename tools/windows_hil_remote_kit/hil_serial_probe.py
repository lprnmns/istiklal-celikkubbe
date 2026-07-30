"""Read-only Pico HIL probe for Windows.

This tool intentionally sends only the identity/health commands ``PING`` and
``STAT``.  It never sends driver, motion, arm, servo, or fire commands.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import serial


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_available(port: serial.Serial, duration_s: float) -> list[str]:
    deadline = time.monotonic() + duration_s
    lines: list[str] = []
    while time.monotonic() < deadline:
        raw = port.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            lines.append(line)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Pico PING/STAT read-only probe")
    parser.add_argument("--port", default="COM7")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=0.25)
    parser.add_argument("--settle", type=float, default=1.5)
    parser.add_argument("--response-window", type=float, default=1.5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output or Path(
        f"hil_serial_probe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    evidence: dict[str, object] = {
        "schema": "istiklal.hil.serial_probe.v1",
        "started_at": utc_now(),
        "port": args.port,
        "baud": args.baud,
        "safety_boundary": "PING_STAT_ONLY",
        "events": [],
        "pass": False,
    }
    events: list[dict[str, object]] = evidence["events"]  # type: ignore[assignment]

    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baud,
            timeout=args.timeout,
            write_timeout=1.0,
        ) as pico:
            events.append({"at": utc_now(), "event": "PORT_OPEN"})
            boot_lines = read_available(pico, args.settle)
            for line in boot_lines:
                events.append({"at": utc_now(), "event": "RX", "line": line})

            responses: dict[str, list[str]] = {}
            for command in ("PING", "STAT"):
                pico.write((command + "\n").encode("ascii"))
                pico.flush()
                events.append({"at": utc_now(), "event": "TX", "command": command})
                lines = read_available(pico, args.response_window)
                responses[command] = lines
                for line in lines:
                    events.append({"at": utc_now(), "event": "RX", "line": line})

            pong = any("PONG" in line for line in responses["PING"])
            status_line = next(
                (
                    line
                    for line in responses["STAT"]
                    if "STATUS,ESTOP=" in line or "OK,STAT,ESTOP=" in line
                ),
                None,
            )
            evidence["pong"] = pong
            evidence["status_line"] = status_line
            evidence["pass"] = bool(pong and status_line)
    except Exception as exc:  # serial failures must still produce evidence
        evidence["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        evidence["finished_at"] = utc_now()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
