"""FPS Profiling - Her component'in süresini ölç"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import time
from config import DetectionConfig, SystemConfig
from yolo_detector import create_detector

print("\n" + "="*70)
print("DETAYLI FPS PROFILING")
print("="*70)

# Config
det_config = DetectionConfig()
sys_config = SystemConfig()

# Detector oluştur
print("\n[1] YOLO Detector oluşturuluyor...")
detector = create_detector(det_config, "YOLO")

# Kamera aç
print(f"\n[2] Kamera açılıyor (Index {sys_config.CAMERA_INDEX})...")
cap = cv2.VideoCapture(sys_config.CAMERA_INDEX, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, sys_config.CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, sys_config.CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("❌ Kamera açılamadı!")
    exit(1)

print(f"✅ Kamera açıldı: {sys_config.CAMERA_WIDTH}x{sys_config.CAMERA_HEIGHT}")

# Warmup
print("\n[3] Warmup (5 frame)...")
for _ in range(5):
    ret, frame = cap.read()
    if ret:
        detector.detect(frame)

# Test
print("\n[4] Performans Testi (30 frame)...")
print("-" * 70)

camera_times = []
detect_times = []
draw_times = []
total_times = []

for i in range(30):
    frame_start = time.time()
    
    # Kamera okuma
    cam_start = time.time()
    cap.grab()
    ret, frame = cap.retrieve()
    cam_time = time.time() - cam_start
    camera_times.append(cam_time)
    
    if not ret:
        continue
    
    # Detection (her 5 framede 1)
    detect_time = 0
    if i % 5 == 0:
        det_start = time.time()
        detections = detector.detect(frame)
        detect_time = time.time() - det_start
    detect_times.append(detect_time)
    
    # Draw
    draw_start = time.time()
    annotated = detector.draw_detections(frame, [], (320, 240))
    draw_time = time.time() - draw_start
    draw_times.append(draw_time)
    
    # Total
    total_time = time.time() - frame_start
    total_times.append(total_time)
    
    if i % 5 == 0:
        fps = 1 / total_time if total_time > 0 else 0
        print(f"Frame {i+1:2d}: Camera={cam_time*1000:5.1f}ms  Detect={detect_time*1000:6.1f}ms  Draw={draw_time*1000:4.1f}ms  Total={total_time*1000:6.1f}ms  FPS={fps:5.1f}")

cap.release()

# Sonuçlar
print("\n" + "="*70)
print("SONUÇLAR (Ortalama):")
print("="*70)

avg_camera = np.mean(camera_times) * 1000
avg_detect = np.mean([d for d in detect_times if d > 0]) * 1000 if any(d > 0 for d in detect_times) else 0
avg_draw = np.mean(draw_times) * 1000
avg_total = np.mean(total_times) * 1000
avg_fps = 1 / np.mean(total_times)

print(f"Camera Read:  {avg_camera:6.1f}ms")
print(f"Detection:    {avg_detect:6.1f}ms (her 5 framede 1)")
print(f"Draw:         {avg_draw:6.1f}ms")
print(f"─" * 70)
print(f"TOTAL:        {avg_total:6.1f}ms")
print(f"FPS:          {avg_fps:6.1f}")
print("="*70)

# Analiz
print("\nANALİZ:")
if avg_camera > 50:
    print("  ⚠️  Kamera okuma YAVAŞ (>50ms)")
    print("     → Çözünürlüğü düşür veya farklı codec dene")
elif avg_detect > 100:
    print("  ⚠️  Detection YAVAŞ (>100ms)")
    print("     → GPU kullanılmıyor olabilir veya image_size büyük")
elif avg_draw > 20:
    print("  ⚠️  Drawing YAVAŞ (>20ms)")
    print("     → OpenCV optimizasyonu gerekli")
else:
    print("  ✅ Tüm componentler normal çalışıyor")
    print(f"     Teorik FPS: {avg_fps:.1f}")

print("\n" + "="*70)
