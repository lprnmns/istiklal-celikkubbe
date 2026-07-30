"""Geometry and persistence for distinct turret motion/fire exclusion zones."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from app.schemas.config import AngularSafetyZone, AppConfig
from app.schemas.log import LogLevel
from app.schemas.safety_zone import SafetyZoneProfile, SafetyZoneProfileUpdate


def active_zone_name(zones: list[AngularSafetyZone], pan_deg: float, tilt_deg: float) -> str | None:
    """Return the first enabled exclusion sector containing turret state."""
    for zone in zones:
        if zone.enabled and zone.pan_min_deg <= pan_deg <= zone.pan_max_deg and zone.tilt_min_deg <= tilt_deg <= zone.tilt_max_deg:
            return zone.name
    return None


class SafetyZoneProfileService:
    """Own the active zone profile and mirror it into the canonical config.

    The YAML configuration remains the immutable baseline.  Field changes are
    persisted separately under ``config/runtime`` so an operator never has to
    edit source or an environment file, and the profile hash can be attached
    to a run record.
    """

    def __init__(self, config: AppConfig, logger, path: Path) -> None:
        self.config = config
        self.logger = logger
        self.path = path
        self._baseline = SafetyZoneProfileUpdate(
            motion_zones=list(config.motion.motion_forbidden_zones),
            fire_zones=list(config.decision.fire_forbidden_zones),
        )
        self._active = self._baseline
        self._source = "config_baseline"
        self._updated_at = time.time()
        self._load()

    def status(self) -> SafetyZoneProfile:
        payload = self._active.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return SafetyZoneProfile(
            **payload,
            profile_hash=hashlib.sha256(encoded).hexdigest(),
            source=self._source,
            updated_at=self._updated_at,
        )

    def replace(self, update: SafetyZoneProfileUpdate) -> SafetyZoneProfile:
        self._validate_within_motion_limits(update)
        self._active = update
        self._source = "runtime_persisted"
        self._updated_at = time.time()
        self._apply_to_config(update)
        self._persist()
        profile = self.status()
        self.logger.emit(LogLevel.INFO, "SAFETY_ZONE", "Safety-zone profile updated", profile.model_dump(mode="json"))
        return profile

    def _validate_within_motion_limits(self, update: SafetyZoneProfileUpdate) -> None:
        motion = self.config.motion
        for zone in [*update.motion_zones, *update.fire_zones]:
            if (
                zone.pan_min_deg < motion.pan_min_deg
                or zone.pan_max_deg > motion.pan_max_deg
                or zone.tilt_min_deg < motion.tilt_min_deg
                or zone.tilt_max_deg > motion.tilt_max_deg
            ):
                raise ValueError(f"SAFETY_ZONE_OUTSIDE_SOFT_LIMITS:{zone.name}")

    def _apply_to_config(self, profile: SafetyZoneProfileUpdate) -> None:
        self.config.motion.motion_forbidden_zones = list(profile.motion_zones)
        self.config.decision.fire_forbidden_zones = list(profile.fire_zones)
        # A non-empty fire sector must be evaluated by DecisionEngine as well
        # as by CommandGateway.  Empty profiles keep the explicit config value.
        if profile.fire_zones:
            self.config.decision.forbidden_zone_check_enabled = True

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            candidate = SafetyZoneProfileUpdate.model_validate(raw)
            self._validate_within_motion_limits(candidate)
            self._active = candidate
            self._source = "runtime_persisted"
            self._updated_at = float(raw.get("updated_at", time.time())) if isinstance(raw, dict) else time.time()
            self._apply_to_config(candidate)
        except (OSError, ValueError, TypeError):
            # An invalid persisted profile may never silently widen authority:
            # retain the reviewed YAML baseline and leave no live side effect.
            self._active = self._baseline
            self._source = "config_baseline"
            self._apply_to_config(self._baseline)

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.status().model_dump_json(indent=2), encoding="utf-8")
