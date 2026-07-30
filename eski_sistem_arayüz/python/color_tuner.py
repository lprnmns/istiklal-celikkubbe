# color_tuner.py - Renk Algılama Parametreleri İçin İnteraktif Tuner
"""
Kızıl balonu algılama parametrelerini gerçek zamanlı test edebilirsin.

Kullanım:
    python color_tuner.py --camera 1
    python color_tuner.py --image test.jpg
    
Kontroller:
    - H: Hue aralığını göster/ayarla
    - S: Saturation aralığını göster/ayarla
    - V: Value aralığını göster/ayarla
    - M: Min alan eşiğini ayarla
    - C: Close iterations'ı ayarla
    - O: Open iterations'ı ayarla
    - R: Reset (varsayılan değerlere)
    - Q: Çık
"""

import cv2
import numpy as np
import argparse
from pathlib import Path

class ColorTuner:
    def __init__(self, camera_index=1):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Kamera {camera_index} açılamadı!")
        
        # Renk aralıkları (HSV)
        self.lower_red1 = np.array([0, 80, 50])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 80, 50])
        self.upper_red2 = np.array([180, 255, 255])
        
        # Morph parametreleri
        self.min_area = 300
        self.close_iter = 2
        self.open_iter = 1
        self.blur_size = 9
        
        # Kernel
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # UI State
        self.show_mask = False
        self.show_contours = True
        self.tuning_mode = None
        
    def process_frame(self, frame):
        """Frame'i işle ve sonuçları döndür"""
        blurred = cv2.GaussianBlur(frame, (self.blur_size, self.blur_size), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        # Mask oluştur
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask = cv2.addWeighted(mask1, 1.0, mask2, 1.0, 0.0)
        
        # Morph işlemleri
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel, iterations=self.close_iter)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel, iterations=self.open_iter)
        
        # Contour'ları bul
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue
            
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 0 and h > 0:
                aspect_ratio = float(w) / h
                if 0.3 < aspect_ratio < 3.0:
                    detections.append((x, y, w, h, area))
        
        return mask, detections, hsv
    
    def draw_ui(self, frame, mask, detections):
        """UI'yi çiz"""
        h, w = frame.shape[:2]
        
        # Solda mask, sağda detections
        if self.show_mask:
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            combined = np.hstack([frame, mask_bgr])
        else:
            combined = frame.copy()
        
        # Detections'ları çiz
        for x, y, box_w, box_h, area in detections:
            cv2.rectangle(combined, (x, y), (x + box_w, y + box_h), (0, 255, 0), 2)
            cv2.circle(combined, (x + box_w//2, y + box_h//2), 5, (0, 255, 255), -1)
            cv2.putText(combined, f"A:{int(area)}", (x, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Info paneli
        info_text = [
            f"Tespit: {len(detections)}",
            f"H1: [{self.lower_red1[0]},{self.upper_red1[0]}] H2: [{self.lower_red2[0]},{self.upper_red2[0]}]",
            f"S: [{self.lower_red1[1]},{self.upper_red1[1]}]",
            f"V: [{self.lower_red1[2]},{self.upper_red1[2]}]",
            f"MinArea: {self.min_area}",
            f"Close:{self.close_iter} Open:{self.open_iter}",
            "",
            "H/S/V/M/C/O ayarla | R:reset | M:mask | Q:çık"
        ]
        
        y_offset = 20
        for text in info_text:
            cv2.putText(combined, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 20
        
        return combined
    
    def handle_input(self, key):
        """Tuş girdisini işle"""
        if key == ord('q'):
            return False
        elif key == ord('m'):
            self.show_mask = not self.show_mask
        elif key == ord('r'):
            self.reset_to_default()
            print("✅ Varsayılan değerlere sıfırlandı")
        elif key == ord('h'):
            self.tune_hue()
        elif key == ord('s'):
            self.tune_saturation()
        elif key == ord('v'):
            self.tune_value()
        elif key == ord('a'):
            self.tune_min_area()
        elif key == ord('c'):
            self.tune_close()
        elif key == ord('o'):
            self.tune_open()
        return True
    
    def tune_hue(self):
        print("\n🎨 HUE TUNING")
        print(f"Hue1: {self.lower_red1[0]}-{self.upper_red1[0]}")
        print(f"Hue2: {self.lower_red2[0]}-{self.upper_red2[0]}")
        try:
            h1_low = int(input("Hue1 Alt Sınır (0-180): ") or self.lower_red1[0])
            h1_high = int(input("Hue1 Üst Sınır (0-180): ") or self.upper_red1[0])
            h2_low = int(input("Hue2 Alt Sınır (0-180): ") or self.lower_red2[0])
            h2_high = int(input("Hue2 Üst Sınır (0-180): ") or self.upper_red2[0])
            
            self.lower_red1[0] = h1_low
            self.upper_red1[0] = h1_high
            self.lower_red2[0] = h2_low
            self.upper_red2[0] = h2_high
            print(f"✅ Ayarlandı: H1=[{h1_low},{h1_high}] H2=[{h2_low},{h2_high}]")
        except ValueError:
            print("❌ Geçersiz giriş!")
    
    def tune_saturation(self):
        print("\n🎨 SATURATION TUNING")
        print(f"Saturation: {self.lower_red1[1]}-{self.upper_red1[1]}")
        try:
            s_low = int(input("Saturation Alt Sınır (0-255): ") or self.lower_red1[1])
            s_high = int(input("Saturation Üst Sınır (0-255): ") or self.upper_red1[1])
            
            self.lower_red1[1] = s_low
            self.upper_red1[1] = s_high
            self.lower_red2[1] = s_low
            self.upper_red2[1] = s_high
            print(f"✅ Ayarlandı: S=[{s_low},{s_high}]")
        except ValueError:
            print("❌ Geçersiz giriş!")
    
    def tune_value(self):
        print("\n🎨 VALUE TUNING")
        print(f"Value: {self.lower_red1[2]}-{self.upper_red1[2]}")
        try:
            v_low = int(input("Value Alt Sınır (0-255): ") or self.lower_red1[2])
            v_high = int(input("Value Üst Sınır (0-255): ") or self.upper_red1[2])
            
            self.lower_red1[2] = v_low
            self.upper_red1[2] = v_high
            self.lower_red2[2] = v_low
            self.upper_red2[2] = v_high
            print(f"✅ Ayarlandı: V=[{v_low},{v_high}]")
        except ValueError:
            print("❌ Geçersiz giriş!")
    
    def tune_min_area(self):
        print(f"\n📏 MIN AREA: {self.min_area}")
        try:
            area = int(input("Min Alan Eşiği: ") or self.min_area)
            self.min_area = area
            print(f"✅ Ayarlandı: {area}")
        except ValueError:
            print("❌ Geçersiz giriş!")
    
    def tune_close(self):
        print(f"\n🔄 CLOSE ITERATIONS: {self.close_iter}")
        try:
            close = int(input("Close Iterations: ") or self.close_iter)
            self.close_iter = close
            print(f"✅ Ayarlandı: {close}")
        except ValueError:
            print("❌ Geçersiz giriş!")
    
    def tune_open(self):
        print(f"\n🔄 OPEN ITERATIONS: {self.open_iter}")
        try:
            open_i = int(input("Open Iterations: ") or self.open_iter)
            self.open_iter = open_i
            print(f"✅ Ayarlandı: {open_i}")
        except ValueError:
            print("❌ Geçersiz giriş!")
    
    def reset_to_default(self):
        self.lower_red1 = np.array([0, 80, 50])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 80, 50])
        self.upper_red2 = np.array([180, 255, 255])
        self.min_area = 300
        self.close_iter = 2
        self.open_iter = 1
    
    def export_settings(self):
        """Ayarları Python kodu olarak çıkart"""
        code = f"""
# === RENK AYARLARI (yolo_detector.py'ye yapıştır) ===
self.lower_red1 = np.array([{self.lower_red1[0]}, {self.lower_red1[1]}, {self.lower_red1[2]}])
self.upper_red1 = np.array([{self.upper_red1[0]}, {self.upper_red1[1]}, {self.upper_red1[2]}])
self.lower_red2 = np.array([{self.lower_red2[0]}, {self.lower_red2[1]}, {self.lower_red2[2]}])
self.upper_red2 = np.array([{self.upper_red2[0]}, {self.upper_red2[1]}, {self.upper_red2[2]}])

self.min_area = {self.min_area}
self.close_iter = {self.close_iter}
self.open_iter = {self.open_iter}
"""
        return code
    
    def run(self):
        print("🎨 Renk Tuner Başlatıldı")
        print("Tuş basınız: H/S/V/A/C/O = ayarla | M = mask göster | R = reset | Q = çık")
        
        cv2.namedWindow("Color Tuner", cv2.WINDOW_AUTOSIZE)
        
        running = True
        while running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            mask, detections, _ = self.process_frame(frame)
            display = self.draw_ui(frame, mask, detections)
            
            cv2.imshow("Color Tuner", display)
            
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                running = self.handle_input(key)
        
        cv2.destroyAllWindows()
        self.cap.release()
        
        print("\n" + "="*60)
        print("🔧 SON AYARLAR:")
        print(self.export_settings())
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Renk Algılama Parametreleri Tuner")
    parser.add_argument("--camera", type=int, default=1, help="Kamera numarası")
    args = parser.parse_args()
    
    tuner = ColorTuner(camera_index=args.camera)
    tuner.run()

if __name__ == "__main__":
    main()
