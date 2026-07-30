import json
import time
from pathlib import Path
from typing import Any

from app.schemas.log import LogEvent, LogLevel


class JsonlLogService:
    def __init__(self, log_dir: Path, filename: str = "backend.jsonl") -> None:
        self.log_dir = log_dir
        self.filename = filename
        self.log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self.log_dir / self.filename

    def emit(
        self,
        level: LogLevel,
        subsystem: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> LogEvent:
        event = LogEvent(
            ts=time.time(),
            level=level,
            subsystem=subsystem,
            message=message,
            details=details or {},
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return event


def default_log_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "logs"

