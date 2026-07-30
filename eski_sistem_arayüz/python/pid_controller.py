# pid_controller.py - PID kontrolcü (X/Y ayrı)
import logging
from typing import Tuple
from config import PIDConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PIDController:
    """
    Basit PID kontrolcü anti-windup ile.
    Error: piksel (crosshair - target), output: steps/s hız.
    """
    def __init__(self, kp: float, ki: float, kd: float, min_out: float, max_out: float, integral_max: float = 100.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_out = min_out
        self.max_out = max_out
        self.integral_max = integral_max

        self.prev_error = 0.0
        self.integral = 0.0
        self.reset()

    def reset(self):
        """Integral ve prev_error sıfırla (yeni hedefte)"""
        self.integral = 0.0
        self.prev_error = 0.0

    def compute(self, error: float, dt: float) -> float:
        """
        PID hesapla: P + I + D
        Anti-windup: integral clamp
        """
        # Proportional
        p_term = self.kp * error

        # Integral (dt ile)
        self.integral += error * dt
        self.integral = max(-self.integral_max, min(self.integral_max, self.integral))
        i_term = self.ki * self.integral

        # Derivative
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        d_term = self.kd * derivative
        self.prev_error = error

        # Toplam output clamp
        output = p_term + i_term + d_term
        output = max(self.min_out, min(self.max_out, output))

        logger.debug(f"PID: e={error:.1f}, out={output:.1f}")
        return output

class DualPID:
    """
    X ve Y için ayrı PID'ler.
    """
    def __init__(self, config: PIDConfig):
        self.pid_x = PIDController(config.KP_X, config.KI_X, config.KD_X,
                                  config.OUTPUT_MIN, config.OUTPUT_MAX, config.INTEGRAL_MAX)
        self.pid_y = PIDController(config.KP_Y, config.KI_Y, config.KD_Y,
                                  config.OUTPUT_MIN, config.OUTPUT_MAX, config.INTEGRAL_MAX)
        
        # Canlı güncelleme için attribute'ler
        self.kp_x = config.KP_X
        self.ki_x = config.KI_X
        self.kd_x = config.KD_X
        self.kp_y = config.KP_Y
        self.ki_y = config.KI_Y
        self.kd_y = config.KD_Y

    def reset(self):
        self.pid_x.reset()
        self.pid_y.reset()
    
    def update_from_attributes(self):
        """Attribute'lerden PID'leri güncelle (canlı ayarlar için)"""
        self.pid_x.kp = self.kp_x
        self.pid_x.ki = self.ki_x
        self.pid_x.kd = self.kd_x
        self.pid_y.kp = self.kp_y
        self.pid_y.ki = self.ki_y
        self.pid_y.kd = self.kd_y

    def compute(self, error_x: float, error_y: float, dt: float) -> Tuple[float, float]:
        # Her frame öncesi attribute'lerden güncelle (canlı ayarlamalar için)
        self.update_from_attributes()
        
        speed_x = self.pid_x.compute(error_x, dt)
        speed_y = self.pid_y.compute(error_y, dt)
        return speed_x, speed_y