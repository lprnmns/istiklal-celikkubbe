# safety_manager.py - Sistem güvenlik kontrolleri
import time
import logging
from typing import Tuple
from config import HardwareConfig, SystemConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafetyManager:
    """
    Güvenlik kontrolleri:
    - Açı limitleri
    - Yasak ateş bölgesi
    - Acil durdur
    - Lazer timeout
    """
    def __init__(self, hw_config: HardwareConfig, sys_config: SystemConfig):
        self.hw = hw_config
        self.sys = sys_config
        self.emergency_active = False
        self.laser_start_time = 0.0
        self.max_laser_time = 5.0  # saniye
        self.last_fire_warning_time = 0  # Warning throttle için

    def activate_emergency_stop(self):
        """Acil durdur aktif et"""
        self.emergency_active = True
        logger.warning("ACİL DURDUR AKTİF!")

    def deactivate_emergency_stop(self):
        """Acil durdur pasif et (güvenli ise)"""
        self.emergency_active = False
        logger.info("Acil durdur pasif")

    def is_emergency_stopped(self) -> bool:
        return self.emergency_active

    def can_fire(self, x_angle: float) -> bool:
        """Yasak X bölgesinde mi? (-15° to +15°)"""
        in_forbidden = self.hw.FORBIDDEN_X_MIN <= x_angle <= self.hw.FORBIDDEN_X_MAX
        # Warning throttle - sadece 5 saniyede bir uyar (spam önleme)
        if in_forbidden:
            current_time = time.time()
            if current_time - self.last_fire_warning_time > 5.0:  # 5 saniye
                logger.warning(f"Yasak bölgede ateş: X={x_angle:.1f}°")
                self.last_fire_warning_time = current_time
        return not in_forbidden and not self.emergency_active

    def check_limits(self, x_angle: float, y_angle: float) -> bool:
        """Açı limitleri içinde mi?"""
        x_ok = self.hw.X_MIN <= x_angle <= self.hw.X_MAX
        y_ok = self.hw.Y_MIN <= y_angle <= self.hw.Y_MAX
        if not x_ok or not y_ok:
            logger.warning(f"Limit aşıldı: X={x_angle:.1f}°, Y={y_angle:.1f}°")
        return x_ok and y_ok

    def laser_timeout_check(self) -> bool:
        """Lazer max süre aşıldı mı?"""
        if time.time() - self.laser_start_time > self.max_laser_time:
            logger.warning("Lazer timeout!")
            return False
        return True

    def start_laser(self):
        """Lazer açılış zamanını kaydet"""
        self.laser_start_time = time.time()

    def convert_steps_to_angles(self, steps_x: float, steps_y: float) -> Tuple[float, float]:
        """Steps'i dereceye çevir (gear ratio ile)"""
        angle_x = steps_x / self.hw.X_STEPS_PER_DEG
        angle_y = steps_y / self.hw.Y_STEPS_PER_DEG
        return angle_x, angle_y

    def convert_angles_to_steps(self, angle_x: float, angle_y: float) -> Tuple[float, float]:
        """Dereceyi steps'e çevir"""
        steps_x = angle_x * self.hw.X_STEPS_PER_DEG
        steps_y = angle_y * self.hw.Y_STEPS_PER_DEG
        return steps_x, steps_y