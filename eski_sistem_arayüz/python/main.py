import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import time
import logging
from typing import Optional, Tuple
import signal

from config import HardwareConfig, PIDConfig, DetectionConfig, SerialConfig, SystemConfig
from yolo_detector import create_detector, Detection
from kalman_filter import KalmanFilter
from pid_controller import DualPID
from serial_comm import SerialComm
from safety_manager import SafetyManager
from state_machine import StateMachine, SystemState
from gui import AirDefenseGUI
from launcher import Launcher # Launcher importu
from threaded_camera import ThreadedCamera  # Threaded camera (yavaş kameralar için)
from threaded_pipeline import DetectionThread, SerialThread  # Multi-threading pipeline
from settings_manager import SettingsManager  # PID ayarlar için
import queue

# Logging seviyesini ERROR'a çıkar (sadece kritik hatalar)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AirDefenseSystem:
    def __init__(self, settings: dict):
        # Ayarları Yükle
        self.apply_settings(settings)
        
        self.hw_config = HardwareConfig()
        self.pid_config = PIDConfig()
        
        # Kaydedilmiş PID ayarlarını yükle
        saved_pid = SettingsManager.load_pid_settings()
        self.apply_pid_settings(saved_pid)
        logger.info(f"PID ayarları yüklendi: {saved_pid}")
        
        self.det_config = DetectionConfig()
        
        # Launcher'dan gelen özel ayarlar
        if settings["model_type"] == "YOLO":
            self.det_config.MODEL_PATH = settings["model_path"]
        
        # Motor Hızı Ayarı
        self.apply_motor_speed(settings["motor_speed"])

        self.serial_config = SerialConfig()
        self.serial_config.PORT = settings["port"] # Portu ayarla
        self.serial_config.BAUDRATE = 460800 # Maksimum hız
        self.serial_config.ENABLE_TX = bool(settings.get("enable_serial_tx", False))
        self.serial_config.SAFE_DRY_RUN = not self.serial_config.ENABLE_TX
        self.serial_config.NO_PHYSICAL_COMMAND_GENERATED = True
        
        self.sys_config = SystemConfig()
        self.sys_config.CAMERA_INDEX = settings["camera_index"]
        res = settings["resolution"].split('x')
        self.sys_config.CAMERA_WIDTH = int(res[0])
        self.sys_config.CAMERA_HEIGHT = int(res[1])
        self.sys_config.FPS_TARGET = settings["fps"]

        self.cap: Optional[cv2.VideoCapture] = None
        self.use_threaded_camera = True  # Yavaş kameralar için threaded mode
        
        # Dedektör Fabrikası (Factory)
        self.detector = create_detector(self.det_config, settings["model_type"])
        
        # Multi-threading Pipeline (MAXIMUM FPS için)
        self.detection_queue_in = queue.Queue(maxsize=2)  # Frame'ler buraya
        self.detection_queue_out = queue.Queue(maxsize=1)  # Detection sonuçları buraya
        self.detection_thread = DetectionThread(
            self.detector, 
            self.detection_queue_in, 
            self.detection_queue_out
        )
        self.detection_thread.start()
        print("🔥 Detection Thread başlatıldı (paralel işlem)")
        
        self.kalman = KalmanFilter()
        self.pid = DualPID(self.pid_config)
        self.serial = SerialComm(self.serial_config)
        
        # Serial Thread (non-blocking communication)
        self.serial_thread = SerialThread(self.serial)
        self.serial_thread.start()
        print("⚡ Serial Thread başlatıldı (non-blocking)")
        self.safety = SafetyManager(self.hw_config, self.sys_config)
        self.state_machine = StateMachine()

        self.current_frame = None
        self.detections = []
        self.target_detection: Optional[Detection] = None
        self.last_target_detection: Optional[Detection] = None  # Hedef kalıcılığı için
        self.target_lost_frames = 0  # Kaç frame hedef kayıp kaldı
        
        # Crosshair tam görüntü merkezinde
        self.crosshair = (self.sys_config.CAMERA_WIDTH // 2, self.sys_config.CAMERA_HEIGHT // 2)
        
        self.current_x_steps = 0
        self.current_y_steps = 0
        self.current_x_angle = 0.0
        self.current_y_angle = 0.0
        self.speed_x = 0
        self.speed_y = 0
        self.laser_active = False
        self.running = True
        self.mode = settings.get("startup_mode", "IDLE") # Ayarlardan gelen mod
        self.last_time = time.time()
        
        self.last_serial_time = 0
        self.serial_interval = 0.012  # 12ms (≈83Hz) - daha hızlı komut güncelleme
        self.last_manual_input_time = 0
        
        # Joystick Manuel Kontrol (MANUEL MOD)
        self.joy_speed_x = 0  # Joystick'ten gelen hız
        self.joy_speed_y = 0
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
                # Performance timing (debug)
        self.detect_time = 0
        self.camera_time = 0
        self.total_frame_time = 0
        # Frame skip optimization (multi-threading ile artık her frame işlenebilir)
        self.frame_counter = 0
        self.detection_interval = 1  # Multi-threading ile her frame işle
        signal.signal(signal.SIGINT, self.signal_handler)

    def apply_settings(self, settings):
        """Genel ayar (placeholder)"""
        pass

    def apply_pid_settings(self, pid_values):
        """PID ayarlarını sisteme uygula"""
        self.pid_config.KP_X = pid_values.get('KP_X', 2.5)
        self.pid_config.KI_X = pid_values.get('KI_X', 0.002)
        self.pid_config.KD_X = pid_values.get('KD_X', 0.45)
        self.pid_config.KP_Y = pid_values.get('KP_Y', 1.0)
        self.pid_config.KI_Y = pid_values.get('KI_Y', 0.002)
        self.pid_config.KD_Y = pid_values.get('KD_Y', 0.45)
        
        # Eğer PID controller zaten varsa güncelle
        if hasattr(self, 'pid'):
            self.pid.kp_x = self.pid_config.KP_X
            self.pid.ki_x = self.pid_config.KI_X
            self.pid.kd_x = self.pid_config.KD_X
            self.pid.kp_y = self.pid_config.KP_Y
            self.pid.ki_y = self.pid_config.KI_Y
            self.pid.kd_y = self.pid_config.KD_Y
            logger.info("PID controller değerleri canlı güncellendi")

    def apply_motor_speed(self, speed_mode):
        """Hız moduna göre PID ve Limitleri ayarla"""
        if speed_mode == "Slow":
            self.pid_config.OUTPUT_MAX = 100.0
            self.pid_config.OUTPUT_MIN = -100.0
            self.pid_config.MIN_MOVE_SPEED = 20.0
            self.manual_speed = 200
        elif speed_mode == "Medium":
            self.pid_config.OUTPUT_MAX = 200.0
            self.pid_config.OUTPUT_MIN = -200.0
            self.pid_config.MIN_MOVE_SPEED = 30.0
            self.manual_speed = 300
        elif speed_mode == "Fast":
            self.pid_config.OUTPUT_MAX = 1000.0  # Arduino SPD ölçeğiyle hizalı (maks 1000)
            self.pid_config.OUTPUT_MIN = -1000.0
            self.pid_config.MIN_MOVE_SPEED = 60.0
            self.manual_speed = 1000
        else:
            self.manual_speed = 400

    def signal_handler(self, sig, frame):
        logger.info("Shutdown sinyali alındı")
        self.stop()

    def init_hardware(self) -> bool:
        logger.info(f"Kamera başlatılıyor (Index {self.sys_config.CAMERA_INDEX})...")
        
        if self.use_threaded_camera:
            # Threaded camera (yavaş kameralar için 2-3x FPS artışı)
            print("🚀 Threaded Camera modu aktif (yavaş kameralar için)")
            try:
                self.cap = ThreadedCamera(
                    src=self.sys_config.CAMERA_INDEX,
                    width=self.sys_config.CAMERA_WIDTH,
                    height=self.sys_config.CAMERA_HEIGHT,
                    fps=self.sys_config.FPS_TARGET,
                )
            except Exception as e:
                logger.error(f"Threaded camera başarısız: {e}")
                self.use_threaded_camera = False
        
        if not self.use_threaded_camera:
            # Normal camera (standart)
            print("📷 Normal Camera modu")
            # Önce DSHOW dene
            if isinstance(self.sys_config.CAMERA_INDEX, str) and self.sys_config.CAMERA_INDEX.startswith("/dev/"):
                self.cap = cv2.VideoCapture(self.sys_config.CAMERA_INDEX, cv2.CAP_V4L2)
            else:
                self.cap = cv2.VideoCapture(self.sys_config.CAMERA_INDEX, cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                # DSHOW başarısızsa default backend dene
                logger.warning("DSHOW başarısız, default backend deneniyor...")
                self.cap = cv2.VideoCapture(self.sys_config.CAMERA_INDEX)
            
            # Kamera optimizasyonları (sıralama önemli!)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.sys_config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.sys_config.CAMERA_HEIGHT)
            # YUY2 codec deneyelim, yoksa raw
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))  # Sıkıştırmasız
            self.cap.set(cv2.CAP_PROP_FPS, self.sys_config.FPS_TARGET)  # Ayarlardan gelen FPS
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer'ı minimize et
            
            # Titreşim azaltma (Stabilization)
            stabilization = settings.get("stabilization", "Normal")
            if stabilization == "Kapalı":
                self.cap.set(cv2.CAP_PROP_STABILIZATION, 0)
            elif stabilization == "Düşük":
                self.cap.set(cv2.CAP_PROP_STABILIZATION, 1)
            elif stabilization == "Normal":
                self.cap.set(cv2.CAP_PROP_STABILIZATION, 2)
            elif stabilization == "Yüksek":
                self.cap.set(cv2.CAP_PROP_STABILIZATION, 3)
            
            # Otomatik ayarları AÇ (PC'deki gibi)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # 🔥 Autofocus AÇ
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 🔥 Otomatik exposure
            self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)  # 🔥 Otomatik white balance
            
            # Maksimum kalite için
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)  # 🔥 ARTIRILDI - oynat oto ayarlar da
            self.cap.set(cv2.CAP_PROP_CONTRAST, 25)    # 🔥 Maksimum contrast
            self.cap.set(cv2.CAP_PROP_SATURATION, 64)  # 🔥 Maksimum renk
            self.cap.set(cv2.CAP_PROP_GAMMA, 100)      # 🔥 YENİ - Gamma maksimum
            
            # İlk frame'leri flush et (autofocus kapatma için)
            for _ in range(30):  # Daha fazla flush
                self.cap.grab()

        if not self.cap.isOpened():
            logger.error("Kamera açılamadı!")
            return False
        
        # Gerçek çözünürlüğü kontrol et (sadece normal camera için)
        if not self.use_threaded_camera:
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            print(f"Kamera: {actual_width}x{actual_height} @ {actual_fps}FPS")
        
        # OpenCV penceresi kaldırıldı - GUI içinde gösterilecek
        # cv2.namedWindow kaldırıldı

        if not self.serial.connect(self.serial_config.PORT):
            logger.warning("Arduino bağlanamadı (simülasyon modu)")
            self.sys_config.SIMULATION_MODE = True
        if not self.serial_config.ENABLE_TX:
            print("🛡️ Serial TX kapalı: motor/tetik komutu gönderilmeyecek; no_physical_command_generated=true")

        logger.info("Hardware init tamam")
        return True

    def on_gui_input(self, input_str: str):
        if input_str.startswith("MODE:"):
            new_mode = input_str.split(":")[1]
            self.mode = new_mode
            # Arduino'ya mod bildir
            result = self.serial.set_mode(new_mode)
            print(f"🎮 [MODE DEĞIŞTI] {self.mode} - Arduino yanıt: {result}")
            logger.info(f"Mod Değiştirildi (GUI): {self.mode}")
        elif input_str.startswith("PID_UPDATE:"):
            # PID değerleri GUI'den güncellendi
            import ast
            pid_str = input_str.split(":", 1)[1]
            pid_values = ast.literal_eval(pid_str)
            self.apply_pid_settings(pid_values)
            logger.info(f"PID değerleri canlı güncellendi: {pid_values}")
        elif input_str == "GET_CAMERA":
            # Mevcut kamera değerlerini gönder
            if self.cap:
                cap_obj = self.cap.cap if self.use_threaded_camera else self.cap
                camera_values = {
                    cv2.CAP_PROP_BRIGHTNESS: int(cap_obj.get(cv2.CAP_PROP_BRIGHTNESS)),
                    cv2.CAP_PROP_CONTRAST: int(cap_obj.get(cv2.CAP_PROP_CONTRAST)),
                    cv2.CAP_PROP_SATURATION: int(cap_obj.get(cv2.CAP_PROP_SATURATION)),
                    cv2.CAP_PROP_GAIN: int(cap_obj.get(cv2.CAP_PROP_GAIN)),
                    cv2.CAP_PROP_SHARPNESS: int(cap_obj.get(cv2.CAP_PROP_SHARPNESS)),
                    cv2.CAP_PROP_HUE: int(cap_obj.get(cv2.CAP_PROP_HUE)),
                    cv2.CAP_PROP_GAMMA: int(cap_obj.get(cv2.CAP_PROP_GAMMA)),
                }
                # White Balance sadece varsa ekle
                try:
                    camera_values[cv2.CAP_PROP_WHITE_BALANCE_BLUE_U] = int(cap_obj.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U))
                    camera_values[cv2.CAP_PROP_WHITE_BALANCE_RED_U] = int(cap_obj.get(cv2.CAP_PROP_WHITE_BALANCE_RED_U))
                except:
                    pass
                self.gui.current_camera_values = camera_values
        elif input_str.startswith("CAM_SET:"):
            # Kamera ayarı: CAM_SET:property:value
            parts = input_str.split(":")
            if len(parts) == 3:
                prop = parts[1]
                value = int(parts[2])
                if self.cap:
                    cap_obj = self.cap.cap if self.use_threaded_camera else self.cap
                    if prop == "EXPOSURE_COMP":
                        # Exposure Compensation (-6 ile +6) → cv2.CAP_PROP_EXPOSURE (-13 ile 0)
                        # Mapping: -6 → -13, 0 → -4, +6 → 0
                        # Linear interpolation: value * (13/6) - 4
                        exposure_value = int(value * (13.0/6.0) - 4)
                        exposure_value = max(-13, min(0, exposure_value))
                        cap_obj.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
                        logger.info(f"Exposure Compensation: {value} → Exposure: {exposure_value}")
                    else:
                        # Normal cv2 property
                        prop_int = int(prop)
                        cap_obj.set(prop_int, value)
                        logger.info(f"Kamera parametresi güncellendi: {prop}={value}")
        elif input_str == "CAM_RESET":
            # Kamera ayarlarını sıfırla
            defaults = [
                (cv2.CAP_PROP_BRIGHTNESS, 50),
                (cv2.CAP_PROP_CONTRAST, 50),
                (cv2.CAP_PROP_SATURATION, 50),
                (cv2.CAP_PROP_GAIN, 50),
                (cv2.CAP_PROP_SHARPNESS, 50),
                (cv2.CAP_PROP_HUE, 0),
                (cv2.CAP_PROP_GAMMA, 100),
                (cv2.CAP_PROP_AUTOFOCUS, 1),
                (cv2.CAP_PROP_AUTO_EXPOSURE, 1),
            ]
            if self.cap:
                cap_obj = self.cap.cap if self.use_threaded_camera else self.cap
                for prop, val in defaults:
                    try:
                        cap_obj.set(prop, val)
                    except:
                        pass
                # White Balance varsa ayarla
                try:
                    cap_obj.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 128)
                    cap_obj.set(cv2.CAP_PROP_WHITE_BALANCE_RED_U, 128)
                except:
                    pass
                logger.info("Kamera parametreleri sıfırlandı")
        elif input_str == "CAM_MAX":
            # Maksimum parlaklık
            settings = [
                (cv2.CAP_PROP_BRIGHTNESS, 100),
                (cv2.CAP_PROP_CONTRAST, 64),
                (cv2.CAP_PROP_SATURATION, 100),
                (cv2.CAP_PROP_GAIN, 100),
                (cv2.CAP_PROP_SHARPNESS, 100),
                (cv2.CAP_PROP_HUE, 0),
                (cv2.CAP_PROP_GAMMA, 200),
                (cv2.CAP_PROP_AUTOFOCUS, 1),
                (cv2.CAP_PROP_AUTO_EXPOSURE, 1),
            ]
            if self.cap:
                cap_obj = self.cap.cap if self.use_threaded_camera else self.cap
                for prop, val in settings:
                    try:
                        cap_obj.set(prop, val)
                    except:
                        pass
                # White Balance varsa ayarla
                try:
                    cap_obj.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 128)
                    cap_obj.set(cv2.CAP_PROP_WHITE_BALANCE_RED_U, 128)
                except:
                    pass
                logger.info("Kamera maksimum parlaklık ayarlandı")
        elif input_str == 'emergency_stop':
            self.safety.activate_emergency_stop()
        elif input_str == 'm':
            self.cycle_mode()
        elif input_str in ['w', 's', 'a', 'd', 'space', 'h', 'q', 'e']:
             if input_str == 'q': self.stop()
             elif input_str == 'e': self.mode = "IDLE"; self.speed_x=0; self.speed_y=0
             else: self.handle_manual_input(input_str)

    def cycle_mode(self):
        modes = ["IDLE", "MANUAL", "AUTO", "AUTONOMOUS"]
        idx = (modes.index(self.mode) + 1) % len(modes)
        self.mode = modes[idx]
        logger.info(f"Mod: {self.mode}")

    def handle_manual_input(self, key: str):
        if self.mode != "MANUAL":
            return
        
        # DEBUG: Tuş basımını gör
        logger.info(f"Manuel Tuş Algılandı: {key}")
        
        self.last_manual_input_time = time.time()
        speed_step = self.manual_speed
        
        if key == 'w': self.speed_y = speed_step
        elif key == 's': self.speed_y = -speed_step
        elif key == 'a': self.speed_x = -speed_step
        elif key == 'd': self.speed_x = speed_step
        elif key == 'space': self.fire_laser()
        elif key == 'h': self.serial.home()

    def process_step(self):
        loop_start = time.time()
        dt = time.time() - self.last_time
        if dt <= 0: dt = 0.033
        self.last_time = time.time()
        
        # FPS hesapla
        self.fps_counter += 1
        if time.time() - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = time.time()

        # 1. Görüntü Al
        if self.cap is not None and self.cap.isOpened():
            cam_start = time.time()
            
            if self.use_threaded_camera:
                # Threaded mode - sadece read() çağır
                ret, frame = self.cap.read()
            else:
                # Normal mode - grab + retrieve
                self.cap.grab()
                ret, frame = self.cap.retrieve()
            
            self.camera_time = time.time() - cam_start
            
            if ret and frame is not None:
                self.current_frame = frame
            elif self.current_frame is None:
                self.current_frame = np.zeros((self.sys_config.CAMERA_HEIGHT, self.sys_config.CAMERA_WIDTH, 3), dtype=np.uint8) + 50
        else:
            self.current_frame = np.zeros((self.sys_config.CAMERA_HEIGHT, self.sys_config.CAMERA_WIDTH, 3), dtype=np.uint8)

        # 2. İşle ve Göster
        if self.current_frame is not None:
            try:
                # Frame'i işle (parlaklık normalleştirme + saturation azaltma)
                processed_frame = self._preprocess_frame(self.current_frame)
                
                # Manuel Modda Otomatik Durdurma
                if self.mode == "MANUAL":
                    if time.time() - self.last_manual_input_time > 0.5: # Süre uzatıldı
                        self.speed_x = 0
                        self.speed_y = 0

                # Multi-threaded Detection (Queue-based, non-blocking)
                self.frame_counter += 1
                
                # Frame'i detection queue'ya gönder (non-blocking)
                if self.frame_counter % self.detection_interval == 0:
                    try:
                        # Eğer queue doluysa eski frame'i at
                        if self.detection_queue_in.full():
                            try:
                                self.detection_queue_in.get_nowait()
                            except queue.Empty:
                                pass
                        self.detection_queue_in.put_nowait(processed_frame.copy())  # PROCESSED FRAME
                    except queue.Full:
                        pass  # Queue doluysa skip
                
                # Detection sonuçlarını al (non-blocking)
                try:
                    result = self.detection_queue_out.get_nowait()
                    self.detections, self.detect_time = result
                except queue.Empty:
                    # Henüz sonuç yoksa eski detection'ları kullan
                    pass
                
                self.select_target()
                
                # Joystick verilerini oku (Arduino'dan gelen)
                self.read_joystick_from_arduino()
                
                self.update_state_machine(dt)
                self.compute_control(dt)
                self.perform_safety_checks()
                self.send_to_arduino()
                self.update_gui()
                
                annotated_frame = self.detector.draw_detections(processed_frame, self.detections, self.crosshair, self.target_detection)
                
                # FPS göstergesi ekle (sol üst köşe)
                fps_text = f"FPS: {self.current_fps}"
                cv2.putText(annotated_frame, fps_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
                
                # Detect time (debug)
                if self.detect_time > 0:
                    detect_ms = self.detect_time * 1000
                    detect_text = f"Detect: {detect_ms:.0f}ms"
                    cv2.putText(annotated_frame, detect_text, (10, 130), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
                
                # Camera time (debug)
                if self.camera_time > 0:
                    camera_ms = self.camera_time * 1000
                    camera_text = f"Camera: {camera_ms:.0f}ms"
                    cv2.putText(annotated_frame, camera_text, (10, 160), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2, cv2.LINE_AA)
                
                # Mod göstergesi ekle (sol üst, ikinci satır)
                mode_text = f"Mode: {self.mode}"
                cv2.putText(annotated_frame, mode_text, (10, 65), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)
                
                # Tespit sayısı (sol üst, üçüncü satır)
                detection_text = f"Detections: {len(self.detections)}"
                cv2.putText(annotated_frame, detection_text, (10, 95), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Motor Speed Debug (sağ üst köşe)
                speed_text = f"Speed X:{int(self.speed_x)} Y:{int(self.speed_y)}"
                cv2.putText(annotated_frame, speed_text, (annotated_frame.shape[1] - 320, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
                
                # Target Debug (sağ üst, ikinci satır)
                if self.target_detection:
                    target_text = f"Target: ({self.target_detection.x},{self.target_detection.y})"
                    cv2.putText(annotated_frame, target_text, (annotated_frame.shape[1] - 320, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2, cv2.LINE_AA)
                else:
                    no_target_text = "Target: NONE"
                    cv2.putText(annotated_frame, no_target_text, (annotated_frame.shape[1] - 320, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
                
                # Serial Connected (sağ üst, üçüncü satır)
                serial_status = "Serial: OK" if self.serial.connected else "Serial: DISCONNECTED"
                serial_color = (0, 255, 0) if self.serial.connected else (0, 0, 255)
                cv2.putText(annotated_frame, serial_status, (annotated_frame.shape[1] - 320, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, serial_color, 2, cv2.LINE_AA)
                
                # Error Debug (sağ üst, dördüncü satır)
                if self.target_detection:
                    cx, cy = self.crosshair
                    error_x = self.target_detection.x - cx
                    error_y = self.target_detection.y - cy
                    error_text = f"Err X:{int(error_x)} Y:{int(error_y)}"
                    cv2.putText(annotated_frame, error_text, (annotated_frame.shape[1] - 320, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 128, 0), 2, cv2.LINE_AA)
                
                # Annotated frame'i GUI'ye gönder (tek pencere)
                if hasattr(self, 'gui'):
                    self.gui.display_frame(annotated_frame)
            
            except Exception as e:
                logger.error(f"Dongu Hatasi: {e}")
                if hasattr(self, 'gui'):
                    self.gui.display_frame(self.current_frame)

        # 3. OpenCV Tuş Kontrolü
        key_code = cv2.waitKey(1) & 0xFF
        if key_code != 255:
            # Tuş karakterini al ve küçült
            try:
                char_code = chr(key_code).lower()
            except:
                char_code = ''

            if char_code == 'q':
                self.stop()
            elif char_code == 'm':
                self.cycle_mode()
            elif char_code == ' ':
                self.fire_laser()
            elif char_code == 'h':
                self.serial.home()
            elif char_code in ['w', 'a', 's', 'd']:
                self.handle_manual_input(char_code)
            elif char_code == 'e':
                self.mode = "IDLE"
                self.speed_x = 0
                self.speed_y = 0

        # FPS limitleyici (opsiyonel - max performans için kaldırılabilir)
        elapsed = time.time() - loop_start
        target_sleep = max(0, (1.0/self.sys_config.FPS_TARGET) - elapsed)
        if target_sleep > 0.001:  # 1ms altındaki sleep'leri atla
            time.sleep(target_sleep)

    def select_target(self):
        """Mevcut detections listesinden hedef seç + Kalıcılık (persistence) + Kalman Prediction"""
        cx, cy = self.crosshair
        
        if self.mode in ["AUTONOMOUS", "AUTO"]:
            # Yeni hedef ara
            new_target = self.detector.get_closest_target(self.detections, cx, cy)
            
            if new_target:
                # Yeni hedef bulundu - Kalman'ı update et
                self.target_detection = new_target
                self.last_target_detection = new_target
                self.target_lost_frames = 0
                # Kalman'ı update et (ölçüm)
                self.kalman.update(np.array([new_target.x, new_target.y]))
            else:
                # Hedef bulunamadı - takip modundaysa eski hedefi tut (max 10 frame)
                if self.target_detection and self.target_lost_frames < 10:
                    # Eski hedefi tut ama sayaç artır
                    self.target_lost_frames += 1
                    
                    # Kalman prediction'ı kullan (daha akıllı tahmin)
                    pred_state = self.kalman.predict()  # Tahmin et
                    predicted_x = float(pred_state[0][0])
                    predicted_y = float(pred_state[1][0])
                    
                    # Tahmin konumunu güncelle
                    self.target_detection.x = predicted_x
                    self.target_detection.y = predicted_y
                    
                    print(f"🔮 Hedef tahmin (lost frame {self.target_lost_frames}): ({predicted_x:.0f},{predicted_y:.0f})")
                else:
                    # 10 frameden fazla hedef yoksa bırak
                    self.target_detection = None
                    self.kalman.reset()
                    
        elif self.mode == "MANUAL":
            blues = [d for d in self.detections if d.class_id == 1]  # Class 1 = mavi
            new_target = self.detector.get_largest_target(blues) if blues else None
            
            if new_target:
                self.target_detection = new_target
                self.target_lost_frames = 0
                self.kalman.update(np.array([new_target.x, new_target.y]))
            else:
                self.target_detection = None
                self.target_lost_frames = 0
        else:
            self.target_detection = None
            self.target_lost_frames = 0

    def update_state_machine(self, dt: float):
        detections = bool(self.target_detection)
        locked = False
        if self.target_detection:
             dx = abs(self.target_detection.x - self.crosshair[0])
             dy = abs(self.target_detection.y - self.crosshair[1])
             if dx < self.det_config.DEAD_ZONE and dy < self.det_config.DEAD_ZONE:
                 locked = True

        # can_fire sadece locked durumunda kontrol et (performans)
        can_fire = self.safety.can_fire(self.current_x_angle) if locked else False
        emergency = self.safety.is_emergency_stopped()
        mode_input = self.mode.lower()
        self.state_machine.update(detections, locked, can_fire, emergency, mode_input)

    def compute_control(self, dt: float):
        if self.mode not in ["AUTO", "AUTONOMOUS"]:
            if self.mode == "IDLE":
                self.speed_x = 0
                self.speed_y = 0
            return

        if not self.target_detection:
            self.speed_x = 0
            self.speed_y = 0
            self.pid.reset()
            self.kalman.reset()
            return

        cx, cy = self.crosshair
        target_x, target_y = self.target_detection.x, self.target_detection.y

        # Basit hata hesabı (velocity prediction kaldırıldı - smooth için)
        error_x = target_x - cx
        error_y = target_y - cy

        raw_x, raw_y = self.pid.compute(error_x, error_y, dt)
        
        # Exponential smoothing (yumuşatma) - salınımı önle, daha stabil
        if not hasattr(self, 'smooth_x'):
            self.smooth_x = 0
            self.smooth_y = 0
        
        alpha = 0.5  # Maksimum agresif tepki (daha az yumuşatma)
        self.smooth_x = alpha * raw_x + (1 - alpha) * self.smooth_x
        self.smooth_y = alpha * raw_y + (1 - alpha) * self.smooth_y
        
        self.speed_x = self.smooth_x
        self.speed_y = self.smooth_y
        
        # DEBUG
        print(f"🔍 Error X:{int(error_x)} Y:{int(error_y)} | Raw X:{int(raw_x)} Y:{int(raw_y)} | Smooth X:{int(self.speed_x)} Y:{int(self.speed_y)}")
        
        if self.hw_config.INVERT_X:
            self.speed_x *= -1
        if self.hw_config.INVERT_Y:
            self.speed_y *= -1
            
        min_speed = self.pid_config.MIN_MOVE_SPEED
        
        # ADAPTİF Dead Zone - box boyutuna göre hassasiyet
        if self.target_detection:
            # Box boyutu ve yuvarlak yarıçapı (SARI DAİRE İLE TAM EŞLEŞTİRİLDİ)
            box_size = (self.target_detection.w + self.target_detection.h) / 2
            # Sarı daire yarıçapı: min(w,h)/4 - yolo_detector.py satır 59
            target_radius = min(self.target_detection.w, self.target_detection.h) / 4.0
            distance_to_center = (error_x**2 + error_y**2)**0.5
            
            # Hedefe daha iyi ortalama için eşikleri ayarla (tolerans azaltıldı)
            lock_threshold = target_radius * 0.85   # Kilit bölgesi biraz daha geniş
            slow_threshold = target_radius * 1.8    # Yakın bölge
            medium_threshold = target_radius * 2.8  # Orta bölge
            
            # DEBUG: Threshold değerleri
            print(f"📊 Box:{int(box_size)} Radius:{int(target_radius)} | Lock:{int(lock_threshold)} Slow:{int(slow_threshold)} Med:{int(medium_threshold)} Dist:{int(distance_to_center)}")
            
            # Hedefe olan mesafeye göre hız ölçekle (ADAPTİF EŞİKLER)
            if distance_to_center <= lock_threshold:
                # Near-zone nudge: çok hassas olmayacak şekilde az itmeler
                # 3 pikselden küçük hata varsa sıfırla, aksi halde hafif nudge
                if abs(error_x) < 3:
                    self.speed_x = 0
                else:
                    self.speed_x = max(min(self.speed_x, 8), -8)  # Nudge kuvveti azaltıldı
                if abs(error_y) < 3:
                    self.speed_y = 0
                else:
                    self.speed_y = max(min(self.speed_y, 8), -8)
                print(f"🎯 LOCKED-NUDGE - Hafif düzeltme (dist:{int(distance_to_center)} <= {int(lock_threshold)})")
            elif distance_to_center < slow_threshold:
                # Yakın - yavaş ama sıfırın üstünde yeterli hız
                self.speed_x *= 0.4
                self.speed_y *= 0.4
                print(f"🐌 VERY SLOW - Çok yavaş (dist:{int(distance_to_center)} < {int(slow_threshold)})")
            elif distance_to_center < medium_threshold:
                # Orta mesafe - daha hızlı yaklaşım
                self.speed_x *= 0.85
                self.speed_y *= 0.85
                print(f"🐎 SLOW - Yavaş (dist:{int(distance_to_center)} < {int(medium_threshold)})")
            else:
                # Uzak - FULL HIZ
                print(f"🚀 FULL SPEED - Uzak (dist:{int(distance_to_center)})")
                pass  # Normal PID hızı
        
        # Dinamik minimum hız kontrolü
        near_zone = False
        if self.target_detection:
            near_zone = distance_to_center <= slow_threshold
        threshold_factor = 0.2 if near_zone else 0.5
        if 0 < abs(self.speed_x) < min_speed * threshold_factor:
            self.speed_x = 0
        if 0 < abs(self.speed_y) < min_speed * threshold_factor:
            self.speed_y = 0

    def perform_safety_checks(self):
        if self.safety.is_emergency_stopped():
            self.serial.emergency_stop()
            self.laser_active = False
            return

        if not self.safety.check_limits(self.current_x_angle, self.current_y_angle):
            self.serial.set_speed(0, 0)

        if self.laser_active and not self.safety.laser_timeout_check():
            self.laser_off()

    def send_to_arduino(self):
        if self.sys_config.SIMULATION_MODE:
            return
        
        if time.time() - self.last_serial_time < self.serial_interval:
            return
        self.last_serial_time = time.time()
        
        # Threaded serial (non-blocking, NO-ACK mode)
        # Arduino SPD,X,Y formatında bekliyor - doğru sırada gönder
        self.serial_thread.send_command("speed", (int(self.speed_x), int(self.speed_y)))
        
        # Status read kapalı (NO-ACK modunda)

    def fire_laser(self):
        if self.safety.can_fire(self.current_x_angle):
             self.serial_thread.send_command("laser_on", None)
             self.safety.start_laser()
             self.laser_active = True
             logger.info("LAZER AÇIK")
        else:
            logger.warning("Ateş edilemez!")

    def laser_off(self):
        self.serial_thread.send_command("laser_off", None)
        self.laser_active = False
        logger.info("Lazer kapatıldı")

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Kamera zaten exposure/brightness ayarlı, ek işlem yok (FPS)"""
        return frame

    def read_joystick_from_arduino(self):
        """Arduino'dan joystick hız verilerini oku ve parse et"""
        if not self.serial.connected:
            return
        
        try:
            # Arduino'dan tüm bekleyen satırları oku
            while self.serial.ser and self.serial.ser.in_waiting > 0:
                line = self.serial.ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Format: JOY,joy_x_raw,joy_y_raw,speed_x,speed_y
                if line.startswith("JOY,"):
                    try:
                        parts = line.split(',')
                        if len(parts) == 5:
                            # parts[0] = "JOY"
                            joy_x_raw = int(parts[1])
                            joy_y_raw = int(parts[2])
                            self.joy_speed_x = float(parts[3])
                            self.joy_speed_y = float(parts[4])
                            print(f"📊 [JOY] X:{int(self.joy_speed_x)} Y:{int(self.joy_speed_y)} Mode:{self.mode}")
                    except (ValueError, IndexError) as e:
                        # Parse hatası, skip
                        pass
        except Exception as e:
            pass  # Sessiz hata

    def update_gui(self):
        if hasattr(self, 'gui'):
            target_status = "None"
            if self.target_detection:
                 target_status = f"Class {self.target_detection.class_id}"
            
            fire_ready = self.safety.can_fire(self.current_x_angle)
            
            self.gui.update_status(
                self.state_machine.get_state_str(),
                self.current_x_angle, self.current_y_angle,
                target_status,
                fire_ready,
                self.safety.is_emergency_stopped()
            )
            
            # MANUEL modda joystick hız verilerini göster
            if self.mode == "MANUAL":
                self.gui.update_joystick_speed(self.joy_speed_x, self.joy_speed_y)

    def run(self):
        if not self.init_hardware():
            logger.error("Hardware init başarısız")
            return
        
        print("\n" + "="*60)
        print("PERFORMANS AYARLARI:")
        print(f"  - Kamera: {self.sys_config.CAMERA_WIDTH}x{self.sys_config.CAMERA_HEIGHT}")
        print(f"  - Detection Interval: Her {self.detection_interval} frame'de 1")
        print(f"  - YOLO Image Size: {self.det_config.IMG_SIZE}")
        print(f"  - FPS Target: {self.sys_config.FPS_TARGET}")
        print("="*60 + "\n")

        self.gui = AirDefenseGUI(self.sys_config, self.on_gui_input, initial_mode=self.mode)
        # GUI setup_ui() sırasında zaten PID'ler yüklendi, tekrar çağırmaya gerek yok
        
        try:
            while self.running:
                self.process_step()
                self.gui.process_events()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.running = False
        
        # Thread'leri durdur
        print("🛑 Thread'ler durduruluyor...")
        if hasattr(self, 'detection_thread'):
            self.detection_thread.stop()
            self.detection_thread.join(timeout=1.0)
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()
            self.serial_thread.join(timeout=1.0)
        
        if self.cap:
            self.cap.release()
        self.serial.disconnect()
        cv2.destroyAllWindows()
        logger.info("Sistem durduruldu")
        if hasattr(self, 'gui'):
            try:
                self.gui.destroy()
            except:
                pass  # GUI zaten kapanmışsa hata verme
        # sys.exit'i kaldırdık - exception çıkmasın

if __name__ == "__main__":
    # ÖNCE LAUNCHER ÇALIŞIR
    launcher = Launcher()
    settings = launcher.run()
    
    # EĞER AYARLAR GELDİYSE SİSTEMİ BAŞLAT
    if settings:
        logger.info("Ayarlar alındı, sistem başlatılıyor...")
        system = AirDefenseSystem(settings)
        system.run()
    else:
        logger.info("Başlatıcı kapatıldı, çıkış yapılıyor.")
