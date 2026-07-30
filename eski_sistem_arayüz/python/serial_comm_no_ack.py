# serial_comm_no_ack.py - Pico 2 ile ACK beklemeden komut gönder
# Not: Bu dosya geriye uyumluluk için tutuluyor. serial_comm.py kullanın.
import serial
import serial.tools.list_ports
import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from config import SerialConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PicoResponse:
    """Pico 2 cevap yapısı"""
    success: bool
    message: str
    data: Optional[dict] = None

# Geriye uyumluluk
ArduinoResponse = PicoResponse

class SerialComm:
    def __init__(self, config: SerialConfig):
        self.config = config
        self.ser: Optional[serial.Serial] = None
        self.connected = False
        self.buffer = ''
        self.last_response_time = 0
        
        # Error throttling (spam önleme)
        self.last_error_time = 0
        self.error_throttle_interval = 2.0  # 2 saniyede 1 error log

    def connect(self, port: Optional[str] = None) -> bool:
        """Pico 2 portuna bağlan (otomatik detect veya belirtilen port)"""
        if port:
            self.config.PORT = port

        # Otomatik port detect (Pico 2 için)
        if not port:
            ports = serial.tools.list_ports.comports()
            for p in ports:
                if 'Pico' in p.description or 'RP2040' in p.description:
                    self.config.PORT = p.device
                    break
                # Fallback: herhangi bir COM port
                elif p.device:
                    self.config.PORT = p.device
                    break

        try:
            self.ser = serial.Serial(
                port=self.config.PORT,
                baudrate=self.config.BAUDRATE,
                timeout=0.05,  # Çok kısa timeout
                write_timeout=0.05
            )
            time.sleep(1)  # Pico 2 reset bekle
            self.connected = True
            logger.info(f"Pico 2 bağlı: {self.config.PORT} (NO-ACK MODE)")
            return True
        except Exception as e:
            logger.error(f"Pico 2 bağlantı hatası: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False

    def send_command(self, cmd: str) -> ArduinoResponse:
        """Fire-and-forget komut gönder (ACK bekleme)"""
        if not self.connected or not self.ser:
            return ArduinoResponse(False, "Not connected")

        try:
            full_cmd = f"{cmd}\n".encode('utf-8')
            self.ser.write(full_cmd)
            self.ser.flush()
            
            # ACK BEKLEME - direkt başarılı say
            # print(f"📤 Serial TX: {cmd}")  # DEBUG kapalı
            return ArduinoResponse(True, "SENT")
            
        except Exception as e:
            # Error throttling (2 saniyede 1 log)
            current_time = time.time()
            if current_time - self.last_error_time >= self.error_throttle_interval:
                logger.error(f"Komut gönderme hatası: {e}")
                self.last_error_time = current_time
            return ArduinoResponse(False, str(e))

    def set_speed(self, speed_x: int, speed_y: int) -> ArduinoResponse:
        """SPD,{speed_x},{speed_y}"""
        cmd = f"SPD,{speed_x},{speed_y}"
        return self.send_command(cmd)

    def set_position(self, pos_x: int, pos_y: int) -> ArduinoResponse:
        """POS,{pos_x},{pos_y}"""
        return self.send_command(f"POS,{pos_x},{pos_y}")

    def laser_on(self) -> ArduinoResponse:
        """LZR,1"""
        return self.send_command("LZR,1")

    def laser_off(self) -> ArduinoResponse:
        """LZR,0"""
        return self.send_command("LZR,0")

    def emergency_stop(self) -> ArduinoResponse:
        """STP"""
        return self.send_command("STP")

    def home(self) -> ArduinoResponse:
        """HOM"""
        return self.send_command("HOM")

    def get_status(self) -> Optional[Tuple[str, int, int]]:
        """Arduino'dan status oku (NO-ACK modunda kullanma)"""
        return None  # Status okuma kapalı

    def _read_response(self, timeout_ms: int = 200) -> ArduinoResponse:
        """Response okuma kapalı"""
        return ArduinoResponse(False, "NO-ACK MODE")
