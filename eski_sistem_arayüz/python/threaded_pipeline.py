"""Multi-threaded Detection Pipeline - Maximum FPS için
Mikrodenetleyici: Raspberry Pi Pico 2 (Arduino IDE ile)
Serial Communication: Pico 2 ile NO-ACK modunda iletişim
"""
import threading
import queue
import time
import logging

logger = logging.getLogger(__name__)

class DetectionThread(threading.Thread):
    """
    Ayrı thread'de detection yapar.
    Frame queue'dan frame alır, detection yapar, sonuç queue'ya koyar.
    """
    def __init__(self, detector, input_queue, output_queue):
        super().__init__(daemon=True)
        self.detector = detector
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.running = True
        
    def run(self):
        """Thread loop - sürekli detection yapar"""
        while self.running:
            try:
                # Queue'dan frame al (timeout ile)
                frame = self.input_queue.get(timeout=0.1)
                
                # Detection yap
                start = time.time()
                detections = self.detector.detect(frame)
                detect_time = time.time() - start
                
                # Sonucu queue'ya koy (eski sonuçları temizle)
                if not self.output_queue.empty():
                    try:
                        self.output_queue.get_nowait()  # Eski sonucu at
                    except queue.Empty:
                        pass
                
                self.output_queue.put((detections, detect_time))
                self.input_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection thread error: {e}")
    
    def stop(self):
        self.running = False


class SerialThread(threading.Thread):
    """
    Ayrı thread'de serial communication yapar.
    Command queue'dan komut alır, Pico 2'ye gönderir.
    Rate limiting ile Pico 2'yi boğmayı önler.
    """
    def __init__(self, serial_comm):
        super().__init__(daemon=True)
        self.serial_comm = serial_comm
        self.command_queue = queue.Queue(maxsize=3)  # Küçült (overflow önle)
        self.running = True
        self.last_send_time = 0
        self.min_send_interval = 0.012  # 12ms minimum (≈83Hz) daha hızlı takip
        
    def run(self):
        """Thread loop - rate limited komut gönderir"""
        while self.running:
            try:
                # Queue'dan komut al
                cmd_type, args = self.command_queue.get(timeout=0.1)
                
                # Rate limiting (Pico 2 yetişemiyorsa bekle)
                time_since_last = time.time() - self.last_send_time
                if time_since_last < self.min_send_interval:
                    time.sleep(self.min_send_interval - time_since_last)
                
                # Komutu gönder
                try:
                    if cmd_type == "speed":
                        self.serial_comm.set_speed(args[0], args[1])
                    elif cmd_type == "laser_on":
                        self.serial_comm.laser_on()
                    elif cmd_type == "laser_off":
                        self.serial_comm.laser_off()
                    elif cmd_type == "home":
                        self.serial_comm.home()
                    
                    self.last_send_time = time.time()
                except Exception:
                    # Error'ları sessizce yut (serial_comm kendi log'lar)
                    pass
                
                self.command_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Serial thread error: {e}")
    
    def send_command(self, cmd_type, args=None):
        """Non-blocking komut gönder (agresif overflow temizleme)"""
        try:
            # Queue doluysa TÜM eski komutları at (en güncel komut önemli)
            while self.command_queue.full():
                try:
                    self.command_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Yeni komutu ekle
            self.command_queue.put_nowait((cmd_type, args or []))
        except queue.Full:
            # Hala doluysa skip (FPS düşmez)
            pass
    
    def stop(self):
        self.running = False
