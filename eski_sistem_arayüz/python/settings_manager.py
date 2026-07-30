import json
import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
PID_SETTINGS_FILE = os.path.join(BASE_DIR, "pid_settings.json")  # Ayrı PID ayarlar dosyası
CAMERA_SETTINGS_FILE = os.path.join(BASE_DIR, "camera_settings.json")  # Kamera ayarları dosyası

DEFAULT_SETTINGS = {
    "model_type": "OPENCV", # "YOLO" veya "OPENCV"
    "model_path": os.path.join(PROJECT_DIR, "models", "yolo2", "best.pt"),
    "camera_index": "/dev/video2",
    "resolution": "1280x720",
    "fps": 30,
    "port": "/dev/ttyACM0",
    "motor_speed": "Medium", # "Slow", "Medium", "Fast"
    "startup_mode": "IDLE", # "IDLE", "MANUAL", "AUTO"
    "stabilization": "Normal", # "Kapalı", "Düşük", "Normal", "Yüksek"
    "enable_serial_tx": False,
    "safe_dry_run": True,
    "no_physical_command_generated": True
}

DEFAULT_PID_SETTINGS = {
    # Daha agresif varsayılan PID (yüksek tepki, clamp ile kontrol)
    "KP_X": 4.0,
    "KD_X": 0.25,
    "KP_Y": 3.2,
    "KI_Y": 0.0
}

DEFAULT_CAMERA_SETTINGS = {
    "enable": 1,     # 1=ON, 0=OFF
    "autofocus": 1,         # 1=ON, 0=OFF
}

class SettingsManager:
    @staticmethod
    def load_settings():
        if not os.path.exists(SETTINGS_FILE):
            return DEFAULT_SETTINGS.copy()
        
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Eksik anahtar varsa defaulttan tamamla
                for key, val in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = val
                return settings
        except Exception as e:
            logging.error(f"Ayarlar yüklenemedi: {e}")
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(settings):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logging.error(f"Ayarlar kaydedilemedi: {e}")

    @staticmethod
    def load_pid_settings():
        """PID ayarlarını yükle (JSON dosyasından)"""
        if not os.path.exists(PID_SETTINGS_FILE):
            return DEFAULT_PID_SETTINGS.copy()
        
        try:
            with open(PID_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Eksik anahtar varsa defaulttan tamamla
                for key, val in DEFAULT_PID_SETTINGS.items():
                    if key not in settings:
                        settings[key] = val
                return settings
        except Exception as e:
            logging.error(f"PID ayarları yüklenemedi: {e}")
            return DEFAULT_PID_SETTINGS.copy()

    @staticmethod
    def save_pid_settings(pid_values):
        """PID ayarlarını kaydet (JSON dosyasına)"""
        try:
            with open(PID_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(pid_values, f, indent=4)
            logging.info(f"PID ayarları kaydedildi: {pid_values}")
            return True
        except Exception as e:
            logging.error(f"PID ayarları kaydedilemedi: {e}")
            return False

    @staticmethod
    def load_camera_settings():
        """Kamera ayarlarını yükle (JSON dosyasından)"""
        if not os.path.exists(CAMERA_SETTINGS_FILE):
            return DEFAULT_CAMERA_SETTINGS.copy()
        
        try:
            with open(CAMERA_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Eksik anahtar varsa defaulttan tamamla
                for key, val in DEFAULT_CAMERA_SETTINGS.items():
                    if key not in settings:
                        settings[key] = val
                return settings
        except Exception as e:
            logging.error(f"Kamera ayarları yüklenemedi: {e}")
            return DEFAULT_CAMERA_SETTINGS.copy()

    @staticmethod
    def save_camera_settings(camera_values):
        """Kamera ayarlarını kaydet (JSON dosyasına)"""
        try:
            with open(CAMERA_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(camera_values, f, indent=4)
            logging.info(f"Kamera ayarları kaydedildi: {camera_values}")
            return True
        except Exception as e:
            logging.error(f"Kamera ayarları kaydedilemedi: {e}")
            return False
