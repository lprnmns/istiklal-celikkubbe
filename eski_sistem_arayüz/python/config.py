# config.py - Tüm sistem sabitleri (Raspberry Pi Pico 2 + CNC Shield)
# MİKRODENETLEYİCİ: Raspberry Pi Pico 2
# MOTOR SÜRÜCÜ: CNC Shield (A4988, DRV8825 veya TMC2209)
# PROGRAMLAMA: Arduino IDE ile

from dataclasses import dataclass
from typing import Tuple

@dataclass
class HardwareConfig:
    # ========== MICROSTEPPING AYARI (AYRILI X/Y) ==========
    # CNC Shield jumper konumlarını buna göre ayarla!
    # 1  = Full Step    (MS1=LOW,  MS2=LOW,  MS3=LOW)
    # 2  = Half Step    (MS1=HIGH, MS2=LOW,  MS3=LOW)
    # 4  = Quarter Step (MS1=LOW,  MS2=HIGH, MS3=LOW)
    # 8  = Eighth Step  (MS1=HIGH, MS2=HIGH, MS3=LOW)
    # 16 = Sixteenth    (MS1=LOW,  MS2=LOW,  MS3=HIGH)
    # 32 = Thirty-second (MS1=HIGH, MS2=HIGH, MS3=HIGH) - TMC2209 special
    
    MICROSTEPPING_MODE_X: int = 8   # X ekseni: 1/8 microstepping
    MICROSTEPPING_MODE_Y: int = 8   # Y ekseni: 1/8 microstepping
    
    # Motor parametreleri
    STEPS_PER_REV: int = 200  # Motor baseband adım sayısı (full step)
    X_GEAR_RATIO: float = 30.0  # Dişli oranı varsa burayı değiştirin
    Y_GEAR_RATIO: float = 20.0

    # ⚡ HESAPLANAN: Ayrı microstepping ile gerçek step sayıları
    # X: 200 * 8 = 1600 step/rev (1/8 + TMC2209 256 interp)
    # Y: 200 * 8 = 1600 step/rev (1/8 + TMC2209 256 interp)
    ACTUAL_STEPS_PER_REV_X: float = STEPS_PER_REV * MICROSTEPPING_MODE_X
    ACTUAL_STEPS_PER_REV_Y: float = STEPS_PER_REV * MICROSTEPPING_MODE_Y

    # Steps per degree (microstepping dahil - AYRILI)
    X_STEPS_PER_DEG: float = (ACTUAL_STEPS_PER_REV_X * X_GEAR_RATIO) / 360
    Y_STEPS_PER_DEG: float = (ACTUAL_STEPS_PER_REV_Y * Y_GEAR_RATIO) / 360

    # Raspberry Pi Pico 2 Pinleri (CNC Shield Uyumlu)
    # Pico - CNC Shield Bağlantısı:
    # GPIO14 → X-STEP (CNC: STEP_X)
    # GPIO12 → X-DIR  (CNC: DIR_X)
    # GPIO15 → Y-STEP (CNC: STEP_Y)
    # GPIO13 → Y-DIR  (CNC: DIR_Y)
    # GPIO10 → ENABLE (CNC: EN)
    # GPIO11 → Lazer
    # GPIO18 → E-STOP
    
    STEP_X_PIN: int = 1    # GPIO1 (M1_STEP)
    DIR_X_PIN: int = 0     # GPIO0 (M1_DIR)
    
    STEP_Y_PIN: int = 9    # GPIO9 (M2_STEP)
    DIR_Y_PIN: int = 8     # GPIO8 (M2_DIR)
    
    ENABLE_PIN: int = 6   # GPIO6 (M1_EN)
    LASER_PIN: int = 15   # GPIO15 (SERVO_PIN Tetik)
    EMERGENCY_STOP_PIN: int = 18  # GPIO18 (BTN_PIN)

    # --- YÖN AYARLARI (Yazılımsal Ters Çevirme) ---
    # Eğer motor doğru eksende ama TERS yöne gidiyorsa bunları True yapın
    INVERT_X: bool = False # X ekseni tersine dönüyordu, şimdi düzeltildi
    INVERT_Y: bool = False  # Y genellikle terstir (Kamera koordinatı vs Motor)

    # --- EKSİK OLAN LİMİTLER GERİ EKLENDİ ---
    X_MIN: float = -135.0
    X_MAX: float = 135.0
    Y_MIN: float = -30.0
    Y_MAX: float = 30.0
    FORBIDDEN_X_MIN: float = -15.0
    FORBIDDEN_X_MAX: float = 15.0

@dataclass
class PIDConfig:
    # ✅ X EKSENİ GÜÇLENDIRILDI - Daha az kaçırma
    
    # X EKSENI (Yatay - Pan, 1/8 microstepping + 256 interp)
    # UI/Ayar menüsü ile senkron (pid_settings.json): 4.0 / 0.01 / 0.25
    KP_X: float = 4.0
    KP_X: float = 8.0   # ⚡ 30x Dişli için tepki gücü artırıldı
    KI_X: float = 0.01
    KD_X: float = 0.25
    KD_X: float = 0.50  # ⚡ Yüksek hızı frenlemek için artırıldı

    # Y EKSENI (Dikey - Tilt, 1/16 microstepping + 256 interp, dişli oranı 2:1)
    # ⚖ Salınım kontrolü: KD düşük (faz gecikmesi önleme), Ki minimal, Kp orta
    KP_Y: float = 0.35
    KP_Y: float = 4.0   # ⚡ 20x Dişli için tepki gücü artırıldı
    KI_Y: float = 0.002
    KD_Y: float = 0.10
    KD_Y: float = 0.30

    # Output limitleri (Motor speed) - X için biraz artırıldı
    OUTPUT_MIN: float = -38000.0  # ⚡ ARTIRILDI (3500→3800) - X daha güçlü
    OUTPUT_MAX: float = 38000.0   # ⚡ ARTIRILDI (3500→3800)
    OUTPUT_MIN: float = -1000.0  # Arduino'nun limiti ile %100 eşleştirildi
    OUTPUT_MAX: float = 1000.0   
    
    # Minimum hareket eşiği
    MIN_MOVE_SPEED: float = 35.0  # ⚡ AZALTILDI (30→28) - daha hassas

    # Integral limite
    INTEGRAL_MAX: float = 25000.0  # ⚡ ARTIRILDI (20000→22000)

@dataclass
class DetectionConfig:
    # Dead zone - ⚡ Biraz daha hassas
    DEAD_ZONE: int = 12       # ⚡ AZALTILDI (15→12) - daha hassas hareket
    DEAD_ZONE_STOP: int = 4   # ⚡ AZALTILDI (5→4)
    
    MODEL_PATH: str = 'models/yolo2/best.pt'
    CONFIDENCE: float = 0.30  # ⚡ AZALTILDI (0.35→0.30) - biraz daha hassas algılama
    IOU: float = 0.25  # ✅ Sabit (iyi çalışıyor)
    IMG_SIZE: int = 416
    CLASS_RED_BALLOON: int = 0
    CLASS_BLUE_BALLOON: int = 1
    
    # ✅ Kamera ayarları - MAKSIMUM KALİTE
    CAMERA_BRIGHTNESS: float = 100  # 🔥 MAX (65→100) - PC'deki kadar aydınlık
    CAMERA_CONTRAST: float = 2.0    # 🔥 ARTIRILDI (1.6→2.0) - PC'deki kadar net
    CAMERA_SATURATION: float = 1.5  # 🔥 ARTIRILDI (1.3→1.5) - renkler canlı

@dataclass
class SerialConfig:
    BAUDRATE: int = 460800  # ⚡ Maksimum performans (Pico 2 desteği)
    PORT: str = '/dev/ttyACM0'
    TIMEOUT: float = 0.02   # ⚡ Düşürüldü (0.1->0.02) - daha hızlı timeout
    ENABLE_TX: bool = False
    SAFE_DRY_RUN: bool = True
    NO_PHYSICAL_COMMAND_GENERATED: bool = True

@dataclass
class SystemConfig:
    WINDOW_WIDTH: int = 1200
    WINDOW_HEIGHT: int = 700
    CAMERA_WIDTH: int = 800   # Launcher varsayılanı ile uyumlu
    CAMERA_HEIGHT: int = 600  # Launcher varsayılanı ile uyumlu
    FPS_TARGET: int = 30
    SIMULATION_MODE: bool = False
    CAMERA_INDEX = "/dev/video2"  # Harici USB kamera
