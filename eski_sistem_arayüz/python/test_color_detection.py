# test_color_detection.py - Renk Algılama Hızlı Test
"""
YOLO yerine ColorDetector'ı test etmek için.

Kullanım:
    python test_color_detection.py --camera 1
    python test_color_detection.py --video video.mp4
"""

import cv2
import numpy as np
import argparse
import sys
from pathlib import Path

# Config'i import et
sys.path.insert(0, str(Path(__file__).parent))
from config import DetectionConfig
from yolo_detector import ColorDetector

def main():
    parser = argparse.ArgumentParser(description="Renk Algılama Testi")
    parser.add_argument("--camera", type=int, help="Kamera numarası")
    parser.add_argument("--video", type=str, help="Video dosyası")
    args = parser.parse_args()
    
    # Video kaynağını seç
    if args.video:
        cap = cv2.VideoCapture(args.video)
        print(f"📹 Video: {args.video}")
    else:
        camera_idx = args.camera or 1
        cap = cv2.VideoCapture(camera_idx)
        print(f"📷 Kamera: {camera_idx}")
    
    if not cap.isOpened():
        print("❌ Kamera/Video açılamadı!")
        return
    
    # Detektörü oluştur
    config = DetectionConfig()
    detector = ColorDetector(config)
    
    print("✅ Detektör başlatıldı (ColorDetector)")
    print("Tuş: Q = çık, M = morph sonucunu göster, R = renk maskesini göster")
    
    show_morph = False
    show_mask = False
    frame_count = 0
    
    cv2.namedWindow("Detection", cv2.WINDOW_AUTOSIZE)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video bitti")
            break
        
        frame_count += 1
        
        # Algıla
        detections = detector.detect(frame)
        
        # UI çiz
        display = detector.draw_detections(frame, detections)
        
        # Bilgi paneli
        info = [
            f"Frame: {frame_count}",
            f"Tespit: {len(detections)}",
            "",
        ]
        
        for i, det in enumerate(detections):
            info.append(f"  {i+1}. ({det.x:.0f},{det.y:.0f}) W:{det.w:.0f} H:{det.h:.0f} Conf:{det.confidence:.2f}")
        
        # Ayrıntılı sonuç
        if detections:
            best = max(detections, key=lambda d: d.w * d.h)
            info.extend([
                "",
                f"En Büyük: ({best.x:.0f},{best.y:.0f})",
                f"  Alan: {best.w * best.h:.0f} px"
            ])
        
        y_pos = 20
        for line in info:
            cv2.putText(display, line, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            y_pos += 20
        
        cv2.imshow("Detection", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            show_mask = not show_mask
            if show_mask:
                print("🔴 Renk maskesi gösteriliyor")
            else:
                print("🔴 Renk maskesi kapatıldı")
        elif key == ord('m'):
            show_morph = not show_morph
            if show_morph:
                print("🔄 Morph sonucu gösteriliyor")
            else:
                print("🔄 Morph sonucu kapatıldı")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Seçme Tamamlandı")

if __name__ == "__main__":
    main()
