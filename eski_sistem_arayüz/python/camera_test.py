import cv2
import tkinter as tk
from tkinter import ttk
import threading
import numpy as np
from PIL import Image, ImageTk

class CameraTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kamera Parametreleri Test - Camera Parameter Tester")
        self.root.geometry("1400x900")
        
        # Kamera aç
        self.cap = cv2.VideoCapture(1)  # İndeks 1 değil ise 0 dene
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Buffer flush
        for _ in range(30):
            self.cap.grab()
        
        # Video frame
        self.video_label = tk.Label(root, bg="black")
        self.video_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sağ panel - Kontroller
        right_frame = ttk.Frame(root, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(right_frame, text="Kamera Parametreleri", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Sliderlar dictionary'si
        self.sliders = {}
        
        # Parametreler: (ad, min, max, başlangıç, cv2_property)
        self.parameters = [
            ("Brightness (Parlaklık)", 0, 100, 50, cv2.CAP_PROP_BRIGHTNESS),
            ("Contrast (Kontrast)", 0, 100, 50, cv2.CAP_PROP_CONTRAST),
            ("Saturation (Doygunluk)", 0, 100, 50, cv2.CAP_PROP_SATURATION),
            ("Gain (Kazanç)", 0, 100, 50, cv2.CAP_PROP_GAIN),
            ("Sharpness (Keskinlik)", 0, 100, 50, cv2.CAP_PROP_SHARPNESS),
            ("Exposure (Pozlama)", -13, 0, -6, cv2.CAP_PROP_EXPOSURE),
            ("White Balance (Beyaz Balans)", 2000, 6500, 4000, cv2.CAP_PROP_AUTO_WB),
            ("Autofocus", 0, 1, 1, cv2.CAP_PROP_AUTOFOCUS),
            ("Auto Exposure", 0, 1, 1, cv2.CAP_PROP_AUTO_EXPOSURE),
        ]
        
        # Slider frame
        slider_frame = ttk.Frame(right_frame)
        slider_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(slider_frame, bg="lightgray")
        scrollbar = ttk.Scrollbar(slider_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Sliderları oluştur
        for param_name, min_val, max_val, start_val, cv2_prop in self.parameters:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Label
            label = ttk.Label(frame, text=param_name, width=25)
            label.pack(side=tk.LEFT, padx=5)
            
            # Değer göster
            value_label = ttk.Label(frame, text=str(start_val), width=8)
            value_label.pack(side=tk.RIGHT, padx=5)
            
            # Slider
            slider = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                orient=tk.HORIZONTAL,
                command=lambda val, prop=cv2_prop, vlbl=value_label: self.on_slider_change(val, prop, vlbl)
            )
            slider.set(start_val)
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            self.sliders[cv2_prop] = (slider, start_val)
            self.cap.set(cv2_prop, start_val)
        
        # Bilgi panel
        info_frame = ttk.LabelFrame(right_frame, text="Bilgi - Information", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.info_label = ttk.Label(info_frame, text="", justify=tk.LEFT, font=("Courier", 9))
        self.info_label.pack()
        
        # Reset butonu
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        reset_btn = ttk.Button(button_frame, text="🔄 Sıfırla (Reset)", command=self.reset_all)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        preset_btn = ttk.Button(button_frame, text="💡 Maksimum Parlaklık", command=self.set_max_brightness)
        preset_btn.pack(side=tk.LEFT, padx=5)
        
        # Video loop başlat
        self.running = True
        self.thread = threading.Thread(target=self.video_loop, daemon=True)
        self.thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_slider_change(self, value, cv2_prop, value_label):
        """Slider değiştiğinde"""
        int_value = int(float(value))
        value_label.config(text=str(int_value))
        
        try:
            self.cap.set(cv2_prop, int_value)
        except Exception as e:
            print(f"Hata: {e}")
    
    def reset_all(self):
        """Varsayılana sıfırla"""
        defaults = [
            (cv2.CAP_PROP_BRIGHTNESS, 50),
            (cv2.CAP_PROP_CONTRAST, 50),
            (cv2.CAP_PROP_SATURATION, 50),
            (cv2.CAP_PROP_GAIN, 50),
            (cv2.CAP_PROP_SHARPNESS, 50),
            (cv2.CAP_PROP_EXPOSURE, -6),
            (cv2.CAP_PROP_AUTOFOCUS, 1),
            (cv2.CAP_PROP_AUTO_EXPOSURE, 1),
        ]
        
        for prop, value in defaults:
            if prop in self.sliders:
                slider, _ = self.sliders[prop]
                slider.set(value)
                self.cap.set(prop, value)
    
    def set_max_brightness(self):
        """Maksimum parlaklık ayarları"""
        settings = [
            (cv2.CAP_PROP_BRIGHTNESS, 100),
            (cv2.CAP_PROP_CONTRAST, 64),
            (cv2.CAP_PROP_SATURATION, 100),
            (cv2.CAP_PROP_GAIN, 100),
            (cv2.CAP_PROP_SHARPNESS, 100),
            (cv2.CAP_PROP_AUTOFOCUS, 1),
            (cv2.CAP_PROP_AUTO_EXPOSURE, 1),
        ]
        
        for prop, value in settings:
            if prop in self.sliders:
                slider, _ = self.sliders[prop]
                slider.set(value)
                self.cap.set(prop, value)
    
    def video_loop(self):
        """Video akışı"""
        while self.running:
            ret, frame = self.cap.read()
            
            if ret:
                # Çevir (BGR -> RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # PIL formatına
                img = Image.fromarray(frame_rgb)
                
                # Tkinter için
                img_tk = ImageTk.PhotoImage(img)
                
                self.video_label.config(image=img_tk)
                self.video_label.image = img_tk
                
                # İstatistik göster
                brightness = frame.mean()
                info_text = f"""
FRAME İSTATİSTİKLERİ - FRAME STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Ortalama Parlaklık: {brightness:.1f}
📐 Çözünürlük: 640x480
🎬 FPS: 30
⚙️ Codec: YUY2 (Sıkıştırmasız)

💾 CURRENT SETTINGS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brightness: {int(self.cap.get(cv2.CAP_PROP_BRIGHTNESS))}
Contrast: {int(self.cap.get(cv2.CAP_PROP_CONTRAST))}
Saturation: {int(self.cap.get(cv2.CAP_PROP_SATURATION))}
Gain: {int(self.cap.get(cv2.CAP_PROP_GAIN))}
Sharpness: {int(self.cap.get(cv2.CAP_PROP_SHARPNESS))}
Autofocus: {'ON' if self.cap.get(cv2.CAP_PROP_AUTOFOCUS) else 'OFF'}
"""
                self.info_label.config(text=info_text)
            
            self.root.update()
    
    def on_closing(self):
        """Kapatma"""
        self.running = False
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraTestGUI(root)
    root.mainloop()
