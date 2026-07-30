# state_machine.py - Sistem durum yönetimi (Finite State Machine)
from enum import Enum
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemState(Enum):
    """Sistem durumları"""
    INIT = "INIT"              # Başlangıç (bağlantılar)
    IDLE = "IDLE"              # Boşta
    MANUAL = "MANUAL"          # Manuel kontrol (klavye)
    AUTO_SEARCH = "AUTO_SEARCH" # Otomatik arama
    AUTO_TRACK = "AUTO_TRACK"  # Takip
    AUTO_LOCKED = "AUTO_LOCKED" # Kilitli (dead zone)
    AUTO_FIRING = "AUTO_FIRING" # Ateş
    AUTONOMOUS = "AUTONOMOUS"  # Tam otonom (multi-target)
    EMERGENCY_STOP = "EMERGENCY_STOP"  # Acil durdur
    ERROR = "ERROR"            # Hata

class StateMachine:
    def __init__(self):
        self.current_state: SystemState = SystemState.INIT
        self.prev_state: Optional[SystemState] = None
        self.target_count = 0  # Otonom için vurulan hedef sayısı

    def transition_to(self, new_state: SystemState, reason: str = "") -> bool:
        """Durum geçişi yap (geçerli mi kontrol et)"""
        if new_state == self.current_state:
            return True

        # Geçiş kuralları (ARCHITECTURE.md'ye göre)
        allowed_transitions = {
            SystemState.INIT: [SystemState.IDLE],
            SystemState.IDLE: [SystemState.MANUAL, SystemState.AUTO_SEARCH, SystemState.AUTONOMOUS],
            SystemState.MANUAL: [SystemState.IDLE, SystemState.AUTO_SEARCH, SystemState.EMERGENCY_STOP],
            SystemState.AUTO_SEARCH: [SystemState.AUTO_TRACK, SystemState.IDLE, SystemState.EMERGENCY_STOP],
            SystemState.AUTO_TRACK: [SystemState.AUTO_LOCKED, SystemState.AUTO_SEARCH, SystemState.EMERGENCY_STOP],
            SystemState.AUTO_LOCKED: [SystemState.AUTO_FIRING, SystemState.AUTO_TRACK, SystemState.EMERGENCY_STOP],
            SystemState.AUTO_FIRING: [SystemState.AUTO_LOCKED, SystemState.AUTO_SEARCH, SystemState.EMERGENCY_STOP],
            SystemState.AUTONOMOUS: [SystemState.AUTO_SEARCH, SystemState.IDLE, SystemState.EMERGENCY_STOP],
            SystemState.EMERGENCY_STOP: [SystemState.IDLE],  # Manuel reset
        }

        if new_state in allowed_transitions.get(self.current_state, []):
            self.prev_state = self.current_state
            self.current_state = new_state
            logger.info(f"Durum geçişi: {self.prev_state.value} -> {new_state.value} ({reason})")
            return True
        else:
            logger.warning(f"Geçersiz geçiş: {self.current_state.value} -> {new_state.value}")
            return False

    def update(self, detections: bool, locked: bool, can_fire: bool, emergency: bool, mode_input: str) -> None:
        """Ana döngüde durum güncelle (otomatik geçişler)"""
        if emergency:
            self.transition_to(SystemState.EMERGENCY_STOP, "Emergency")
            return

        if self.current_state == SystemState.INIT:
            self.transition_to(SystemState.IDLE, "Init complete")

        elif self.current_state == SystemState.IDLE:
            if mode_input == "manual":
                self.transition_to(SystemState.MANUAL, "Manual mode")
            elif mode_input == "auto":
                self.transition_to(SystemState.AUTO_SEARCH, "Auto mode")
            elif mode_input == "autonomous":
                self.transition_to(SystemState.AUTONOMOUS, "Autonomous mode")

        elif self.current_state == SystemState.MANUAL:
            if mode_input == "idle":
                self.transition_to(SystemState.IDLE, "Exit manual")

        elif self.current_state == SystemState.AUTO_SEARCH:
            if detections:
                self.transition_to(SystemState.AUTO_TRACK, "Target detected")
            elif mode_input != "auto":
                self.transition_to(SystemState.IDLE, "Mode change")

        elif self.current_state == SystemState.AUTO_TRACK:
            if locked:
                self.transition_to(SystemState.AUTO_LOCKED, "Target locked")
            elif not detections:
                self.transition_to(SystemState.AUTO_SEARCH, "Target lost")

        elif self.current_state == SystemState.AUTO_LOCKED:
            if can_fire:
                self.transition_to(SystemState.AUTO_FIRING, "Can fire")
            elif not locked:
                self.transition_to(SystemState.AUTO_TRACK, "Lock lost")

        elif self.current_state == SystemState.AUTO_FIRING:
            # Hedef yok say (destroyed)
            self.transition_to(SystemState.AUTO_SEARCH, "Firing complete")
            self.target_count += 1

        elif self.current_state == SystemState.AUTONOMOUS:
            # Cycle through AUTO states, count targets
            if self.target_count >= 3:  # 3 kırmızı vur
                self.transition_to(SystemState.IDLE, "Mission complete")
            else:
                # Delegate to AUTO_SEARCH etc.
                pass

        elif self.current_state == SystemState.EMERGENCY_STOP:
            if mode_input == "reset":
                self.transition_to(SystemState.IDLE, "Emergency reset")

    def reset(self):
        """Sıfırla"""
        self.current_state = SystemState.IDLE
        self.target_count = 0

    def is_autonomous_mode(self) -> bool:
        return self.current_state in [SystemState.AUTO_SEARCH, SystemState.AUTO_TRACK, SystemState.AUTO_LOCKED, SystemState.AUTO_FIRING]

    def get_state_str(self) -> str:
        return self.current_state.value