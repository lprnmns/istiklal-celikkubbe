# yolo_detector.py - HİBRİT MOD (YOLO + OpenCV)
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging
from config import DetectionConfig

# YOLO için gerekli importlar
try:
    import torch
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Detection:
    class_id: int   # 0: Kırmızı/Hedef
    x: float        # Merkez X
    y: float        # Merkez Y
    w: float        # Genişlik
    h: float        # Yükseklik
    confidence: float

class BaseDetector:
    def detect(self, frame: np.ndarray) -> List[Detection]:
        raise NotImplementedError

    def draw_detections(self, frame: np.ndarray, detections: List[Detection], crosshair: Tuple[float, float] = None, locked: Optional[Detection] = None) -> np.ndarray:
        annotated = frame.copy()
        for det in detections:
            color = (0, 0, 255) if det.class_id == 0 else (255, 0, 0)
            if locked and locked.class_id == det.class_id and abs(locked.x - det.x) < 10:
                color = (0, 255, 0)

            x = int(det.x - det.w/2)
            y = int(det.y - det.h/2)
            w = int(det.w)
            h = int(det.h)
            
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            
            # Label ve güven skoru
            label = f"{'Target' if det.class_id==0 else 'Obj'} {det.confidence:.2f}"
            
            # Text arka planı (okunabilirlik için)
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated, (x, y-text_height-baseline-5), (x+text_width, y), color, -1)
            cv2.putText(annotated, label, (x, y-baseline-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # İç Daire (Hedefleme)
            stop_radius = int(min(w, h) / 4)
            cv2.circle(annotated, (int(det.x), int(det.y)), stop_radius, (0, 255, 255), 2)

        if crosshair:
            cx, cy = int(crosshair[0]), int(crosshair[1])
            cv2.line(annotated, (cx-20, cy), (cx+20, cy), (255, 255, 255), 2)
            cv2.line(annotated, (cx, cy-20), (cx, cy+20), (255, 255, 255), 2)
            
        return annotated

    # Main.py uyumluluk metodları
    def detect_red_balloons(self, frame: np.ndarray) -> List[Detection]:
        # TEST İÇİN: Sadece kırmızıyı değil, ne bulursan onu hedef al (Class 0 ve 1)
        # Normalde: return [d for d in all_dets if d.class_id == 0]
        return self.detect(frame)

    def detect_blue_balloons(self, frame: np.ndarray) -> List[Detection]:
        all_dets = self.detect(frame)
        return [d for d in all_dets if d.class_id == 1]

    def get_closest_target(self, detections: List[Detection], center_x: float, center_y: float) -> Optional[Detection]:
        if not detections: return None
        return min(detections, key=lambda d: ((d.x - center_x)**2 + (d.y - center_y)**2)**0.5)
    
    def get_largest_target(self, detections: List[Detection]) -> Optional[Detection]:
        if not detections: return None
        return max(detections, key=lambda d: d.w * d.h)


class ColorDetector(BaseDetector):
    def __init__(self, config: DetectionConfig):
        self.config = config
        logger.info("Mod: OpenCV Renk Takibi")
        
        # ===== IYILEŞTIRILMIŞ RENK AYARLARI - PEMBE/MAGENTA İÇİN GENİŞLETİLDİ =====
        # Kırmızı/Pembe renk HSV'de iki bölgede: 0-20 ve 160-180
        # Hue aralığını genişlettik (pembe/magenta tonlarını algılasın)
        # Pembe = Hue 320-360 (HSV'de 160-180)
        self.lower_red1 = np.array([0, 50, 30])       # Kırmızı: Hue 0-20, S 50+, V 30+
        self.upper_red1 = np.array([20, 255, 255])    # Genişletildi (10->20)
        self.lower_red2 = np.array([160, 50, 30])     # Pembe/Magenta: Hue 160-180, S 50+, V 30+
        self.upper_red2 = np.array([180, 255, 255])
        
        # Morph kernel'ı (daha güçlü işlem için)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
    def detect(self, frame: np.ndarray) -> List[Detection]:
        detections = []
        
        # ✅ MİNİMAL ön işleme - HAM HALİ (en iyi algılama)
        # Sadece hafif blur ve HSV dönüşümü
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.addWeighted(mask1, 1.0, mask2, 1.0, 0.0)
        
        # Basit morph işlemleri
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, self.kernel, iterations=1)
        
        contours, _ = cv2.findContours(mask_red.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 300: continue  # Normal minimum alan
            
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 0 and h > 0:
                aspect_ratio = float(w) / h
                if 0.3 < aspect_ratio < 3.0:
                    detections.append(Detection(0, x + w/2, y + h/2, w, h, 0.85))
        
        return detections

class YOLODetector(BaseDetector):
    def __init__(self, config: DetectionConfig):
        self.config = config
        if not YOLO_AVAILABLE:
            logger.error("Ultralytics/YOLO kurulu değil! OpenCV moduna geçiliyor.")
            raise ImportError("YOLO not found")
            
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("="*60)
        print(f"[YOLO INIT] Device: {self.device}")
        print(f"[YOLO INIT] CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[YOLO INIT] GPU Name: {torch.cuda.get_device_name(0)}")
        print("="*60)
        
        try:
            print(f"[YOLO INIT] Model yükleniyor: {self.config.MODEL_PATH}")
            self.model = YOLO(self.config.MODEL_PATH)
            self.model.to(self.device)
            print(f"[YOLO INIT] Model {self.device} cihazına taşındı")
            
            # FP16 şimdilik devre dışı (sorun çıkarabilir)
            self.use_half = False
            print("[YOLO INIT] FP16 devre dışı (FP32 kullanılıyor)")
            
            # Warmup
            print("[YOLO INIT] Warmup başlatılıyor...")
            dummy_frame = np.zeros((self.config.IMG_SIZE, self.config.IMG_SIZE, 3), dtype=np.uint8)
            _ = self.model(dummy_frame, imgsz=self.config.IMG_SIZE, verbose=False, device=self.device)
            print("[YOLO INIT] Warmup tamamlandı!")
            print("="*60)
            
        except Exception as e:
            print(f"[YOLO ERROR] Model yüklenemedi: {e}")
            logger.error(f"YOLO Modeli Yüklenemedi: {e}")
            raise e
                
        except Exception as e:
            logger.error(f"YOLO Modeli Yüklenemedi: {e}")
            raise e

    def detect(self, frame: np.ndarray) -> List[Detection]:
        # ✅ MİNİMAL ön işleme - HAM HALİ (en iyi algılama)
        # Sadece hafif parlaklık/kontrast düzeltmesi
        alpha = 1.3  # Hafif kontrast
        beta = 20    # Hafif parlaklık
        frame_enhanced = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        
        # YOLO çıkarımı (minimal işlenmiş görüntü ile)
        results = self.model(
            frame_enhanced,
            conf=self.config.CONFIDENCE, 
            iou=self.config.IOU, 
            imgsz=self.config.IMG_SIZE, 
            verbose=False,
            device=self.device
        )
        
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    cls = int(box.cls[0].cpu().numpy())
                    
                    detections.append(Detection(cls, (x1+x2)/2, (y1+y2)/2, x2-x1, y2-y1, conf))
        
        return detections

# Factory Method
def create_detector(config: DetectionConfig, mode: str) -> BaseDetector:
    print(f"\n[DETECTOR FACTORY] Mod: {mode}")
    print(f"[DETECTOR FACTORY] YOLO Available: {YOLO_AVAILABLE}")
    
    if mode == "YOLO" and YOLO_AVAILABLE:
        try:
            print("[DETECTOR FACTORY] YOLODetector oluşturuluyor...")
            detector = YOLODetector(config)
            print("[DETECTOR FACTORY] YOLODetector başarıyla oluşturuldu!\n")
            return detector
        except Exception as e:
            print(f"[DETECTOR FACTORY] YOLO başarısız: {e}")
            print("[DETECTOR FACTORY] ColorDetector'a geçiliyor...\n")
            return ColorDetector(config)
    else:
        print("[DETECTOR FACTORY] ColorDetector kullanılıyor\n")
        return ColorDetector(config)