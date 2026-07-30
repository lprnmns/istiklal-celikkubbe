from __future__ import annotations

import json
import math
import time
import uuid
from pathlib import Path
from typing import Any

from app.schemas.tracking import TrackingConfigUpdate, TrackingState, TrackingUpdate


TRACKING_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "preset_id": "field_baseline_pd",
        "name": "Saha Referansı",
        "algorithm": "Doğrudan PD",
        "description": "Şu an fiziksel testte çalışan hızlı referans ayarı.",
        "config": {"pid_kp_x": 1800.0, "pid_ki_x": 0.0, "pid_kd_x": 80.0, "pid_kp_y": 1600.0, "pid_ki_y": 0.0, "pid_kd_y": 80.0, "smoothing_alpha": 0.90, "command_rate_hz": 30.0, "max_speed": 1000, "min_move_speed": 0.0, "deadband_lock_ratio": 0.0, "deadband_slow_ratio": 0.0, "deadband_medium_ratio": 0.0, "lead_enabled": False, "invert_x": False, "invert_y": True},
    },
    {
        "preset_id": "smooth_precision_pd",
        "name": "Yumuşak Hassas",
        "algorithm": "Filtreli PD + kilit bölgesi",
        "description": "Salınımı azaltır; hedefe yaklaşırken hızı kademeli düşürür.",
        "config": {"pid_kp_x": 1450.0, "pid_ki_x": 0.0, "pid_kd_x": 150.0, "pid_kp_y": 1300.0, "pid_ki_y": 0.0, "pid_kd_y": 140.0, "smoothing_alpha": 0.62, "command_rate_hz": 30.0, "max_speed": 850, "min_move_speed": 45.0, "deadband_lock_ratio": 0.45, "deadband_slow_ratio": 1.25, "deadband_medium_ratio": 2.2, "lead_enabled": False, "invert_x": False, "invert_y": True},
    },
    {
        "preset_id": "fast_intercept_pd",
        "name": "Hızlı Yakalama",
        "algorithm": "Agresif PD",
        "description": "Kadraj kenarındaki hızlı hedefe çabuk yetişmeyi dener.",
        "config": {"pid_kp_x": 2200.0, "pid_ki_x": 0.0, "pid_kd_x": 95.0, "pid_kp_y": 1950.0, "pid_ki_y": 0.0, "pid_kd_y": 90.0, "smoothing_alpha": 0.94, "command_rate_hz": 30.0, "max_speed": 1000, "min_move_speed": 0.0, "deadband_lock_ratio": 0.25, "deadband_slow_ratio": 0.9, "deadband_medium_ratio": 1.7, "lead_enabled": False, "invert_x": False, "invert_y": True},
    },
    {
        "preset_id": "kalman_lead_pd",
        "name": "Kalman Öngörülü",
        "algorithm": "Kalman hız öngörüsü + PD",
        "description": "Hareketli hedefin ölçülen hızını kullanarak gecikmeyi telafi eder.",
        "config": {"pid_kp_x": 1650.0, "pid_ki_x": 0.0, "pid_kd_x": 120.0, "pid_kp_y": 1500.0, "pid_ki_y": 0.0, "pid_kd_y": 115.0, "smoothing_alpha": 0.80, "command_rate_hz": 30.0, "max_speed": 950, "min_move_speed": 35.0, "deadband_lock_ratio": 0.35, "deadband_slow_ratio": 1.1, "deadband_medium_ratio": 2.0, "lead_enabled": True, "lead_latency_multiplier": 1.0, "lead_max_horizon_ms": 120.0, "invert_x": False, "invert_y": True},
    },
)


class TrackingTuningService:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.active: dict[str, Any] | None = None
        self.results: list[dict[str, Any]] = self._load()

    def status(self) -> dict[str, Any]:
        return {"presets": list(TRACKING_PRESETS), "active_trial": self._active_payload(), "results": self.results[-20:]}

    def apply_preset(self, preset_id: str, tracker) -> dict[str, Any]:
        preset = self._preset(preset_id)
        tracker.update_config(TrackingConfigUpdate(**preset["config"]))
        return preset

    def start(self, preset_id: str, tracker) -> dict[str, Any]:
        preset = self.apply_preset(preset_id, tracker)
        self.active = {
            "trial_id": f"trial-{uuid.uuid4().hex[:10]}",
            "preset_id": preset_id,
            "preset_name": preset["name"],
            "algorithm": preset["algorithm"],
            "started_at": time.time(),
            "samples": 0,
            "target_frames": 0,
            "lost_frames": 0,
            "locked_frames": 0,
            "errors": [],
            "commands": [],
            "reversals": 0,
            "reacquisitions": 0,
            "last_sign_x": 0,
            "last_sign_y": 0,
            "had_target": False,
            "first_lock_ms": None,
        }
        return self.status()

    def observe(self, update: TrackingUpdate) -> None:
        trial = self.active
        if trial is None:
            return
        trial["samples"] += 1
        has_target = update.target_center_x is not None and update.target_center_y is not None
        if has_target:
            trial["target_frames"] += 1
            if not trial["had_target"] and trial["lost_frames"] > 0:
                trial["reacquisitions"] += 1
            trial["had_target"] = True
            trial["errors"].append(float(update.distance_to_center))
            trial["commands"].append(math.hypot(update.speed_x, update.speed_y))
            if update.state == TrackingState.LOCKED or update.deadband_zone == "locked":
                trial["locked_frames"] += 1
                if trial["first_lock_ms"] is None:
                    trial["first_lock_ms"] = round((time.time() - trial["started_at"]) * 1000)
            for axis, value in (("x", update.speed_x), ("y", update.speed_y)):
                sign = 1 if value > 20 else -1 if value < -20 else 0
                previous = trial[f"last_sign_{axis}"]
                if sign and previous and sign != previous:
                    trial["reversals"] += 1
                if sign:
                    trial[f"last_sign_{axis}"] = sign
        else:
            trial["lost_frames"] += 1
            trial["had_target"] = False

    def finish(self) -> dict[str, Any]:
        if self.active is None:
            return self.status()
        trial = self.active
        errors = sorted(trial.pop("errors"))
        commands = trial.pop("commands")
        samples = max(1, trial["samples"])
        mean_error = sum(errors) / max(1, len(errors))
        p95_error = errors[min(len(errors) - 1, int(len(errors) * 0.95))] if errors else 0.0
        loss_ratio = trial["lost_frames"] / samples
        mean_command = sum(commands) / max(1, len(commands))
        technical_score = max(0.0, min(100.0, 100.0 - mean_error * 0.12 - p95_error * 0.06 - loss_ratio * 35.0 - trial["reversals"] * 0.025))
        result = {
            **{key: value for key, value in trial.items() if not key.startswith("last_sign") and key != "had_target"},
            "finished_at": time.time(),
            "duration_s": round(time.time() - trial["started_at"], 2),
            "mean_error_px": round(mean_error, 2),
            "p95_error_px": round(p95_error, 2),
            "loss_ratio": round(loss_ratio, 4),
            "mean_command": round(mean_command, 2),
            "technical_score": round(technical_score, 1),
            "operator_rating": None,
            "operator_note": "",
        }
        self.results.append(result)
        self.active = None
        self._persist()
        return self.status()

    def rate(self, trial_id: str, rating: int, note: str = "") -> dict[str, Any]:
        for result in self.results:
            if result["trial_id"] == trial_id:
                result["operator_rating"] = max(1, min(5, int(rating)))
                result["operator_note"] = note.strip()[:300]
                self._persist()
                break
        return self.status()

    def _active_payload(self) -> dict[str, Any] | None:
        if self.active is None:
            return None
        return {key: value for key, value in self.active.items() if key not in {"errors", "commands", "last_sign_x", "last_sign_y", "had_target"}} | {"elapsed_s": round(time.time() - self.active["started_at"], 1)}

    @staticmethod
    def _preset(preset_id: str) -> dict[str, Any]:
        preset = next((item for item in TRACKING_PRESETS if item["preset_id"] == preset_id), None)
        if preset is None:
            raise ValueError("TRACKING_PRESET_NOT_FOUND")
        return preset

    def _load(self) -> list[dict[str, Any]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _persist(self) -> None:
        self.path.write_text(json.dumps(self.results[-100:], ensure_ascii=False, indent=2), encoding="utf-8")
