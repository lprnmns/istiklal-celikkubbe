"""Basit FPS testi - Kamera olmadan"""
import sys
sys.path.insert(0, '.')

from config import DetectionConfig
from yolo_detector import create_detector
import numpy as np
import time

print("\n" + "="*60)
print("BASİT FPS TESTİ")
print("="*60)

# Detector oluştur
config = DetectionConfig()
detector = create_detector(config, "YOLO")

# Test frame
test_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)

print("\nWarmup...")
for _ in range(3):
    detector.detect(test_frame)

print("\nFPS Testi (20 frame)...")
times = []
for i in range(20):
    start = time.time()
    detections = detector.detect(test_frame)
    elapsed = time.time() - start
    times.append(elapsed)
    if i % 5 == 0:
        print(f"  Frame {i+1:2d}: {elapsed*1000:6.1f}ms ({1/elapsed:5.1f} FPS)")

avg_time = np.mean(times)
avg_fps = 1 / avg_time

print(f"\nSONUÇ:")
print(f"  Ortalama: {avg_time*1000:.1f}ms")
print(f"  FPS: {avg_fps:.1f}")
print("="*60)
