#!/usr/bin/env python
"""YOLO GPU performans test scripti"""

import torch
import cv2
import numpy as np
import time
from ultralytics import YOLO

print("="*60)
print("YOLO GPU TEST")
print("="*60)

# 1. PyTorch CUDA kontrolü
print(f"\n[1] PyTorch CUDA Durumu:")
print(f"    Version: {torch.__version__}")
print(f"    CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"    CUDA Version: {torch.version.cuda}")
    print(f"    GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"    GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# 2. YOLO model yükleme
print(f"\n[2] YOLO Model Yükleniyor...")
model_path = "models/yolo/best.pt"
try:
    model = YOLO(model_path)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    print(f"    ✓ Model yüklendi: {model_path}")
    print(f"    ✓ Device: {device}")
except Exception as e:
    print(f"    ✗ Hata: {e}")
    exit(1)

# 3. Dummy frame ile test
print(f"\n[3] Warmup ve FPS Testi:")
img_size = 416
dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

# Warmup
print(f"    Warmup yapılıyor...")
for _ in range(3):
    _ = model(dummy_frame, imgsz=img_size, verbose=False, device=device)

# FPS testi
print(f"    FPS testi başlıyor (10 frame)...")
times = []
for i in range(10):
    start = time.time()
    results = model(dummy_frame, imgsz=img_size, verbose=False, device=device)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"      Frame {i+1}: {elapsed*1000:.1f}ms ({1/elapsed:.1f} FPS)")

avg_time = np.mean(times)
avg_fps = 1 / avg_time
print(f"\n    Ortalama: {avg_time*1000:.1f}ms ({avg_fps:.1f} FPS)")

# 4. GPU kullanım kontrolü
if torch.cuda.is_available():
    print(f"\n[4] GPU Memory Kullanımı:")
    print(f"    Allocated: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
    print(f"    Cached: {torch.cuda.memory_reserved(0) / 1024**2:.1f} MB")

print("\n" + "="*60)
print("TEST TAMAMLANDI")
print("="*60)

if avg_fps < 10:
    print("\n⚠️  FPS ÇOK DÜŞÜK!")
    print("Olası sorunlar:")
    print("  - YOLO CPU'da çalışıyor olabilir (device'i kontrol et)")
    print("  - Model çok büyük (img_size düşür)")
    print("  - GPU memory yetersiz")
elif avg_fps < 20:
    print("\n⚠️  FPS orta seviyede")
    print("İyileştirmeler:")
    print("  - img_size düşür (320'ye)")
    print("  - confidence threshold artır")
else:
    print("\n✅ FPS İYİ!")
