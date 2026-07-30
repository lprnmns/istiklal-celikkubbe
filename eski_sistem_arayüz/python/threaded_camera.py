"""Threaded Camera - Asenkron kamera okuma (FPS artırır)"""
import os

import cv2
import threading
import time

class ThreadedCamera:
    """
    Ayrı thread'de kamera okur, main loop'u bloklamaz.
    Yavaş kameralar için 2-3x FPS artışı sağlar.
    """
    def __init__(self, src=0, width=320, height=240, fps=30):
        print(f"🎥 ThreadedCamera başlatılıyor (src={src})...")
        if isinstance(src, str) and src.startswith("/dev/"):
            self.cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
        else:
            self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            print(f"❌ DSHOW ile kamera açılamadı, default backend deneniyor...")
            self.cap = cv2.VideoCapture(src)

        if not self.cap.isOpened() and isinstance(src, str) and src.startswith("/dev/"):
            fallback_url = os.environ.get("LEGACY_TRACKER_CAMERA_FALLBACK_URL")
            if fallback_url:
                print(f"⚠️ {src} açılamadı, backend stream fallback deneniyor: {fallback_url}")
                self.cap = cv2.VideoCapture(fallback_url)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Kamera açılamadı (src={src})")
        
        print(f"✅ Kamera açıldı (src={src})")
        
        # Kamera ayarları
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -3) # Parlaklık artırıldı (-6 -> -3)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 150) # Ekstra parlaklık
        
        # Thread değişkenleri
        self.frame = None
        self.grabbed = False
        self.stopped = False
        self.lock = threading.Lock()
        
        print(f"🔄 Warmup başlıyor (10 frame)...")
        # Warmup - timeout ile (non-blocking)
        warmup_count = 0
        start_time = time.time()
        for i in range(10):
            if time.time() - start_time > 2.0:  # 2 saniye timeout
                print(f"⚠️ Warmup timeout ({warmup_count}/10 frame)")
                break
            if self.cap.grab():
                warmup_count += 1
            time.sleep(0.05)  # 50ms bekle
        print(f"✅ Warmup tamamlandı ({warmup_count}/10 frame)")
        
        # Thread başlat
        print(f"🚀 Background thread başlatılıyor...")
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        print(f"✅ ThreadedCamera hazır!")
    
    def _update(self):
        """Background thread - sürekli frame okur"""
        while not self.stopped:
            grabbed = self.cap.grab()
            if grabbed:
                ret, frame = self.cap.retrieve()
                if ret:
                    with self.lock:
                        self.frame = frame
                        self.grabbed = True
    
    def read(self):
        """Main thread'den çağrılır - en son frame'i döner"""
        with self.lock:
            return self.grabbed, self.frame.copy() if self.frame is not None else None
    
    def isOpened(self):
        return self.cap.isOpened()
    
    def release(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.cap.release()

    def grab(self):
        """Uyumluluk için - threaded modda gerekli değil"""
        pass
    
    def retrieve(self):
        """Uyumluluk için"""
        return self.read()
