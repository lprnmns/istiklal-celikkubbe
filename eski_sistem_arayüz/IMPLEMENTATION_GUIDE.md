# 📝 Uygulama Rehberi - Kod Detayları

## Dosya Yapısı ve Görevler

```
final/
├── python/
│   ├── main.py                 # Ana uygulama
│   ├── config.py               # Tüm sabitler
│   ├── yolo_detector.py        # YOLO balon tespiti
│   ├── kalman_filter.py        # Kalman tahmin
│   ├── pid_controller.py       # PID kontrolcü
│   ├── serial_comm.py          # Arduino haberleşme
│   ├── safety_manager.py       # Güvenlik kontrolleri
│   ├── state_machine.py        # Durum yönetimi
│   └── gui.py                  # Arayüz
├── arduino/
│   └── motor_control/
│       └── motor_control.ino   # Arduino kodu
├── models/
│   └── (YOLO modeli)
└── README.md
```

---

## 1. config.py

**Görev:** Tüm sistem sabitlerini tek yerden yönetmek.

```python
"""
Tüm sistem sabitleri burada tanımlanır.
Donanım değişikliğinde sadece bu dosya düzenlenir.
"""

# Motor, kamera, PID, güvenlik tüm sabitler...
# HARDWARE_CONFIG.md dosyasındaki şablonu kullan
```

---

## 2. yolo_detector.py

**Görev:** YOLO modeli ile balon tespiti yapmak.

**Sınıf: YOLODetector**
```python
class YOLODetector:
    def __init__(self, model_path, confidence=0.5):
        """YOLO modelini yükle"""
        
    def detect(self, frame) -> List[Detection]:
        """
        Frame'de tüm balonları tespit et
        Return: [Detection(class_id, x, y, w, h, conf), ...]
        """
        
    def detect_red_balloons(self, frame) -> List[Detection]:
        """Sadece kırmızı balonları döndür"""
        
    def detect_blue_balloons(self, frame) -> List[Detection]:
        """Sadece mavi balonları döndür"""
        
    def get_largest_target(self, detections) -> Detection:
        """En büyük balonu seç (alan bazında)"""
        
    def get_closest_to_center(self, detections, center) -> Detection:
        """Merkeze en yakın balonu seç"""
```

**Detection Veri Yapısı:**
```python
@dataclass
class Detection:
    class_id: int       # 0=kırmızı, 1=mavi
    x: float           # Merkez X
    y: float           # Merkez Y
    width: float       # Genişlik
    height: float      # Yükseklik
    confidence: float  # Güven skoru
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    @property
    def area(self) -> float:
        return self.width * self.height
```

---

## 3. kalman_filter.py

**Görev:** Balonun gelecek pozisyonunu tahmin etmek.

**Referans:** `laser_guided_object_tracker` reposundan adapte et.

**Sınıf: KalmanFilter2D**
```python
class KalmanFilter2D:
    def __init__(self, dt=0.033):
        """
        2D Kalman Filter başlat
        Durum: [x, y, vx, vy]
        dt: Frame arası süre (varsayılan 30 FPS için 0.033)
        """
        
    def predict(self) -> Tuple[float, float]:
        """
        Bir sonraki durumu tahmin et
        Return: (predicted_x, predicted_y)
        """
        
    def update(self, measurement: Tuple[float, float]):
        """
        Ölçümle durumu güncelle
        measurement: (measured_x, measured_y)
        """
        
    def get_predicted_position(self, time_ahead: float) -> Tuple[float, float]:
        """
        Belirli süre sonrası pozisyonu tahmin et
        time_ahead: İleriye dönük tahmin süresi (saniye)
        Return: (predicted_x, predicted_y)
        """
        
    def reset(self):
        """Filtreyi sıfırla (yeni hedef seçildiğinde)"""
```

---

## 4. pid_controller.py

**Görev:** Hata değerine göre motor hızını hesaplamak.

**Sınıf: PIDController**
```python
class PIDController:
    def __init__(self, kp, ki, kd, output_min, output_max):
        """
        PID kontrolcü başlat
        kp, ki, kd: PID katsayıları
        output_min/max: Çıktı limitleri
        """
        
    def compute(self, error: float) -> float:
        """
        Hata değerinden kontrol çıktısı hesapla
        error: Hedef - Mevcut değer
        Return: Motor hızı (output_min ile output_max arası)
        """
        
    def reset(self):
        """Integral ve önceki hata değerlerini sıfırla"""
        
    def set_tunings(self, kp, ki, kd):
        """PID katsayılarını güncelle"""
```

**Kullanım:**
```python
pid_x = PIDController(kp=0.5, ki=0.01, kd=0.1, 
                      output_min=-500, output_max=500)

error_x = FRAME_CENTER_X - balloon_x
speed_x = pid_x.compute(error_x)
```

---

## 5. serial_comm.py

**Görev:** Arduino ile haberleşmek.

**Sınıf: SerialComm**
```python
class SerialComm:
    def __init__(self, port, baudrate=115200):
        """Serial bağlantı başlat"""
        
    def connect(self) -> bool:
        """Bağlantı kur, başarılıysa True döndür"""
        
    def disconnect(self):
        """Bağlantıyı kapat"""
        
    def send_speed(self, speed_x: int, speed_y: int):
        """Motor hızlarını gönder: SPD,{x},{y}"""
        
    def send_position(self, pos_x: int, pos_y: int):
        """Hedef pozisyon gönder: POS,{x},{y}"""
        
    def laser_on(self):
        """Lazeri aç: LZR,1"""
        
    def laser_off(self):
        """Lazeri kapat: LZR,0"""
        
    def emergency_stop(self):
        """Acil durdur: STP"""
        
    def go_home(self):
        """Home pozisyona git: HOM"""
        
    def get_status(self) -> dict:
        """Durum bilgisi al: STS"""
        
    def read_response(self) -> str:
        """Arduino'dan yanıt oku (non-blocking)"""
```

---

## 6. safety_manager.py

**Görev:** Güvenlik kontrollerini yönetmek.

**Sınıf: SafetyManager**
```python
class SafetyManager:
    def __init__(self, config):
        """Güvenlik yöneticisini başlat"""
        
    def can_fire(self, current_x_angle: float) -> bool:
        """
        Ateş edilebilir mi kontrol et
        - Yasak bölgede değilse True
        - Yasak bölgedeyse False
        """
        
    def check_limits(self, x_angle: float, y_angle: float) -> Tuple[bool, str]:
        """
        Açı limitleri kontrol et
        Return: (geçerli_mi, hata_mesajı)
        """
        
    def is_emergency_stop_active(self) -> bool:
        """Acil durdur aktif mi?"""
        
    def activate_emergency_stop(self):
        """Acil durdur aktif et"""
        
    def reset_emergency_stop(self):
        """Acil durdur sıfırla"""
        
    def check_laser_timeout(self, laser_on_time: float) -> bool:
        """Lazer çok uzun açık mı kontrol et"""
```

---

## 7. state_machine.py

**Görev:** Sistem durumlarını yönetmek.

```python
from enum import Enum, auto

class SystemState(Enum):
    INIT = auto()           # Başlatılıyor
    IDLE = auto()           # Boşta
    MANUAL = auto()         # Manuel mod
    AUTO_SEARCH = auto()    # Otomatik - hedef arıyor
    AUTO_TRACK = auto()     # Otomatik - hedef takip
    AUTO_LOCKED = auto()    # Otomatik - kilitlendi
    AUTO_FIRING = auto()    # Otomatik - ateş ediyor
    AUTONOMOUS = auto()     # Tam otonom mod
    EMERGENCY_STOP = auto() # Acil durdur
    ERROR = auto()          # Hata durumu

class StateMachine:
    def __init__(self):
        self.state = SystemState.INIT
        self.previous_state = None
        
    def transition(self, new_state: SystemState):
        """Durumu değiştir"""
        
    def can_transition(self, new_state: SystemState) -> bool:
        """Bu geçiş geçerli mi?"""
        
    def get_state(self) -> SystemState:
        """Mevcut durumu döndür"""
        
    def is_active(self) -> bool:
        """Sistem aktif mi? (EMERGENCY_STOP veya ERROR değilse)"""
```

---

## 8. gui.py

**Görev:** Kullanıcı arayüzünü oluşturmak ve yönetmek.

**Sınıf: GUI**
```python
class GUI:
    def __init__(self, on_key_press, on_mode_change, on_emergency_stop):
        """
        GUI başlat (Tkinter)
        Callback fonksiyonları:
        - on_key_press(key): Tuş basıldığında
        - on_mode_change(mode): Mod değiştiğinde
        - on_emergency_stop(): Acil durdur basıldığında
        """
        
    def update_frame(self, frame, detections, target):
        """
        Kamera görüntüsünü güncelle
        - Tespitleri çiz
        - Hedefi işaretle
        - Crosshair çiz
        """
        
    def update_status(self, state, x_angle, y_angle, target_locked, can_fire):
        """Durum panelini güncelle"""
        
    def draw_crosshair(self, frame):
        """Nişangah çiz"""
        
    def draw_forbidden_zone_indicator(self, in_forbidden_zone):
        """Yasak bölge göstergesi"""
        
    def show_message(self, message, level="info"):
        """Mesaj göster (info, warning, error)"""
        
    def run(self):
        """GUI döngüsünü başlat"""
```

**GUI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  TEKNOFEST Hava Savunma Sistemi            [Manuel ▼]  [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────┐  │
│  │                                 │  │ DURUM           │  │
│  │                                 │  │ ─────────────── │  │
│  │         KAMERA GÖRÜNTÜSÜ        │  │ Mod: Manuel     │  │
│  │         (640x480)               │  │ X Açı: 45.2°    │  │
│  │                                 │  │ Y Açı: 12.8°    │  │
│  │              +                  │  │ Hedef: Kilitli  │  │
│  │         (crosshair)             │  │ Ateş: Hazır     │  │
│  │                                 │  │                 │  │
│  └─────────────────────────────────┘  │ ─────────────── │  │
│                                       │ [ACİL DURDUR]   │  │
│  ┌─────────────────────────────────┐  │                 │  │
│  │ Kontroller: WASD=Hareket        │  └─────────────────┘  │
│  │ SPACE=Ateş  E=Acil Durdur       │                       │
│  │ M=Mod Değiştir  H=Home          │                       │
│  └─────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. main.py

**Görev:** Tüm bileşenleri birleştirmek ve ana döngüyü çalıştırmak.

```python
"""
TEKNOFEST Hava Savunma Sistemi - Ana Uygulama
"""

class MainApplication:
    def __init__(self):
        # Bileşenleri başlat
        self.config = Config()
        self.camera = cv2.VideoCapture(self.config.CAMERA_INDEX)
        self.detector = YOLODetector(self.config.YOLO_MODEL_PATH)
        self.kalman = KalmanFilter2D()
        self.pid_x = PIDController(...)
        self.pid_y = PIDController(...)
        self.serial = SerialComm(self.config.SERIAL_PORT)
        self.safety = SafetyManager(self.config)
        self.state = StateMachine()
        self.gui = GUI(...)
        
        # Durum değişkenleri
        self.current_target = None
        self.laser_on = False
        self.laser_on_time = 0
        
    def run(self):
        """Ana döngü"""
        while self.running:
            self.process_frame()
            self.handle_input()
            self.update_motors()
            self.update_gui()
            
    def process_frame(self):
        """Frame işle ve hedef belirle"""
        
    def handle_input(self):
        """Kullanıcı girdilerini işle"""
        
    def update_motors(self):
        """Motor komutlarını gönder"""
        
    def handle_manual_mode(self):
        """Manuel mod işlemleri"""
        
    def handle_auto_mode(self):
        """Otomatik mod işlemleri"""
        
    def handle_autonomous_mode(self):
        """Tam otonom mod işlemleri"""
        
    def fire(self):
        """Ateş et (güvenlik kontrollü)"""
        
    def emergency_stop(self):
        """Acil durdur"""
```

---

## 10. Arduino Kodu (motor_control.ino)

**Görev:** Step motorları ve lazeri kontrol etmek.

```cpp
/*
 * TEKNOFEST Hava Savunma Sistemi - Arduino Motor Kontrolü
 * 
 * Komutlar:
 * SPD,x,y  - Hız ayarla
 * POS,x,y  - Pozisyona git
 * LZR,0/1  - Lazer aç/kapat
 * STP      - Acil durdur
 * HOM      - Home'a git
 * STS      - Durum bilgisi
 */

#include <AccelStepper.h>

// Pin tanımları
#define STEP_X 2
#define DIR_X 3
#define STEP_Y 5
#define DIR_Y 6
#define LASER 8
#define E_STOP 9

// Motor nesneleri
AccelStepper motorX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper motorY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

// Durum değişkenleri
bool emergencyStop = false;
int speedX = 0, speedY = 0;

void setup() {
    Serial.begin(115200);
    
    // Motor ayarları
    motorX.setMaxSpeed(1000);
    motorX.setAcceleration(500);
    motorY.setMaxSpeed(500);
    motorY.setAcceleration(250);
    
    // Pin modları
    pinMode(LASER, OUTPUT);
    pinMode(E_STOP, INPUT_PULLUP);
    
    digitalWrite(LASER, LOW);
    
    Serial.println("READY");
}

void loop() {
    // Acil durdur kontrolü
    if (digitalRead(E_STOP) == LOW) {
        emergencyStop = true;
        motorX.stop();
        motorY.stop();
        digitalWrite(LASER, LOW);
    }
    
    // Serial komut kontrolü
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        parseCommand(cmd);
    }
    
    // Motorları çalıştır (non-blocking)
    if (!emergencyStop) {
        motorX.runSpeed();
        motorY.runSpeed();
    }
}

void parseCommand(String cmd) {
    // Komut parse ve işle...
    // SPD, POS, LZR, STP, HOM, STS
}
```

---

## Geliştirme Sırası

1. **config.py** - İlk olarak sabitler
2. **serial_comm.py** - Arduino bağlantısı
3. **Arduino kodu** - Motor kontrolü
4. **yolo_detector.py** - Balon tespiti
5. **pid_controller.py** - PID kontrolcü
6. **kalman_filter.py** - Tahmin filtresi
7. **safety_manager.py** - Güvenlik
8. **state_machine.py** - Durum yönetimi
9. **gui.py** - Arayüz
10. **main.py** - Her şeyi birleştir
