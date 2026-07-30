# gui.py - Tkinter GUI (kamera feed, kontroller, durum paneli + PID Tuning)
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import logging
from typing import Callable, Optional, Tuple
from config import SystemConfig
from settings_manager import SettingsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirDefenseGUI:
    def __init__(self, config: SystemConfig, update_callback: Callable[[], None], initial_mode="IDLE"):
        self.config = config
        self.update_callback = update_callback
        self.initial_mode = initial_mode # Başlangıç modu
        self.root = tk.Tk()
        self.root.title("TEKNOFEST Hava Savunma Sistemi")
        
        # Window size'ı dinamik olarak hesapla
        # Kamera: max 900 pixel genişlik (sağ panele yer bırak), kontrol paneli: 400px
        max_camera_width = 900
        self.display_width = min(self.config.CAMERA_WIDTH, max_camera_width)
        self.display_height = int(self.display_width * self.config.CAMERA_HEIGHT / self.config.CAMERA_WIDTH)
        
        window_width = self.display_width + 420  # 900 + 420 = 1320
        window_height = max(self.display_height + 100, 600)  # Min 600 yükseklik
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg='black')

        # Kamera ayarlarını yükle
        camera_settings = SettingsManager.load_camera_settings()
        self.auto_exposure_state = bool(camera_settings.get("auto_exposure", 1))
        self.autofocus_state = bool(camera_settings.get("autofocus", 1))

        # Değişkenler
        self.current_frame: Optional[np.ndarray] = None
        self.detections = []
        self.crosshair_pos = (self.config.CAMERA_WIDTH//2, self.config.CAMERA_HEIGHT//2)
        self.current_state = "INIT"
        self.x_angle = 0.0
        self.y_angle = 0.0
        self.target_status = "No Target"
        self.fire_ready = False
        self.emergency_active = False

        self.setup_ui()
        self.bind_keys()
        # self.start_update_loop() # ARTIK OTOMATİK DÖNGÜ YOK

    def setup_ui(self):
        # Ana frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Üst başlık
        title_label = tk.Label(main_frame, text="TEKNOFEST Hava Savunma Sistemi", font=('Arial', 16, 'bold'), fg='white', bg='black')
        title_label.pack(pady=(0,10))

        # Sol: Kamera paneli
        camera_frame = tk.LabelFrame(main_frame, text="Kamera Görüntüsü", fg='white', bg='black', font=('Arial', 10))
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))

        # Label yerine Canvas kullanıyoruz (ölçeklenmiş boyut)
        self.camera_canvas = tk.Canvas(camera_frame, bg='black', width=self.display_width, height=self.display_height)
        self.camera_canvas.pack(pady=10)
        self.canvas_image_ref = None # Canvas image referansı

        # Sağ: Durum paneli (SCROLLABLE)
        status_frame = tk.LabelFrame(main_frame, text="Sistem Durumu", fg='white', bg='black', font=('Arial', 10))
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10,0))

        # Scroll Canvas
        scroll_canvas = tk.Canvas(status_frame, bg='black', highlightthickness=0)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=scroll_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Scroll içindeki frame
        scroll_frame = tk.Frame(scroll_canvas, bg='black')
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        
        # Durum bilgileri
        self.state_label = tk.Label(scroll_frame, text="Durum: INIT", fg='yellow', bg='black', font=('Arial', 12))
        self.state_label.pack(anchor='w', pady=2)

        self.angle_label = tk.Label(scroll_frame, text="X: 0.0° Y: 0.0°", fg='cyan', bg='black', font=('Arial', 12))
        self.angle_label.pack(anchor='w', pady=2)

        self.target_label = tk.Label(scroll_frame, text="Hedef: Yok", fg='red', bg='black', font=('Arial', 12))
        self.target_label.pack(anchor='w', pady=2)

        self.fire_label = tk.Label(scroll_frame, text="Ateş: Hazır Değil", fg='orange', bg='black', font=('Arial', 12))
        self.fire_label.pack(anchor='w', pady=2)

        # Mod seçici
        ttk.Separator(scroll_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        mode_label = tk.Label(scroll_frame, text="Mod:", fg='white', bg='black')
        mode_label.pack(anchor='w')

        self.mode_var = tk.StringVar(value=self.initial_mode) # Varsayılan mod
        modes = [("Manuel", "MANUAL"), ("Otomatik", "AUTO"), ("Otonom", "AUTONOMOUS")]
        for text, value in modes:
            tk.Radiobutton(scroll_frame, text=text, variable=self.mode_var, value=value, bg='black', fg='white',
                          selectcolor='gray', activebackground='black',
                          command=self.on_mode_change).pack(anchor='w')

        # Joystick Hız Paneli (MANUEL MOD İÇİN)
        ttk.Separator(scroll_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        joy_label = tk.Label(scroll_frame, text="Joystick Hız (MANUEL):", fg='lightgreen', bg='black', font=('Arial', 11, 'bold'))
        joy_label.pack(anchor='w', pady=(5,2))

        self.joystick_speed_x = tk.Label(scroll_frame, text="Hız X: +0", fg='cyan', bg='black', font=('Arial', 11))
        self.joystick_speed_x.pack(anchor='w', pady=2)

        self.joystick_speed_y = tk.Label(scroll_frame, text="Hız Y: +0", fg='cyan', bg='black', font=('Arial', 11))
        self.joystick_speed_y.pack(anchor='w', pady=2)

        # Acil durdur butonu (büyük kırmızı)
        ttk.Separator(scroll_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        self.emergency_btn = tk.Button(scroll_frame, text="ACİL DURDUR", font=('Arial', 14, 'bold'),
                                      bg='red', fg='white', width=15, height=2,
                                      command=self.on_emergency_stop)
        self.emergency_btn.pack(pady=10)

        # PID Tuning Paneli
        ttk.Separator(scroll_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        pid_label = tk.Label(scroll_frame, text="PID Ayarları:", fg='white', bg='black', font=('Arial', 11, 'bold'))
        pid_label.pack(anchor='w', pady=(5,2))

        # Kaydedilmiş PID ayarlarını yükle
        saved_pid_settings = SettingsManager.load_pid_settings()
        logger.info(f"[GUI] Yüklenen PID değerleri: {saved_pid_settings}")
        print(f"✓ GUI PID yüklendi: {saved_pid_settings}")

        # PID Giriş Kutuları (X Ekseni)
        tk.Label(scroll_frame, text="X Ekseni:", fg='cyan', bg='black', font=('Arial', 9, 'bold')).pack(anchor='w', pady=(5,0))
        self.create_pid_entry(scroll_frame, "KP_X", saved_pid_settings.get("KP_X", 4.0))
        self.create_pid_entry(scroll_frame, "KI_X", saved_pid_settings.get("KI_X", 0.010))
        self.create_pid_entry(scroll_frame, "KD_X", saved_pid_settings.get("KD_X", 0.25))
        
        # Y Ekseni
        tk.Label(scroll_frame, text="Y Ekseni:", fg='cyan', bg='black', font=('Arial', 9, 'bold')).pack(anchor='w', pady=(5,0))
        self.create_pid_entry(scroll_frame, "KP_Y", saved_pid_settings.get("KP_Y", 3.2))
        self.create_pid_entry(scroll_frame, "KI_Y", saved_pid_settings.get("KI_Y", 0.010))
        self.create_pid_entry(scroll_frame, "KD_Y", saved_pid_settings.get("KD_Y", 0.22))

        # PID Kaydet Butonu
        self.save_pid_btn = tk.Button(scroll_frame, text="PID Kaydet", font=('Arial', 10, 'bold'),
                                     bg='green', fg='white', width=15,
                                     command=self.on_save_pid)
        self.save_pid_btn.pack(pady=10)
        self.pid_status_label = tk.Label(scroll_frame, text="", fg='yellow', bg='black', font=('Arial', 8))
        self.pid_status_label.pack()

        # Kamera Kalibrasyonu Butonu (PID Kaydet altında)
        self.camera_cal_btn = tk.Button(scroll_frame, text="🔥 Kamera Kalibrasyonu", 
                                        font=('Arial', 10, 'bold'),
                                        bg='blue', fg='white', width=15,
                                        command=self.open_camera_calibration)
        self.camera_cal_btn.pack(pady=10)
        
        # Scroll regionu güncelle
        scroll_frame.update_idletasks()
        scroll_canvas.config(scrollregion=scroll_canvas.bbox("all"))

        # Alt kontroller
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        controls_text = """Kontroller: WASD=Move | SPACE=Ateş | E=Dur | M=Mod | H=Home | Q=Çıkış"""
        tk.Label(controls_frame, text=controls_text, fg='white', bg='black', font=('Arial', 10)).pack()

    def bind_keys(self):
        # Tüm tuş vuruşlarını dinle
        self.root.bind('<KeyPress>', self.on_key_press)

    def on_key_press(self, event):
        """Klavye olayları"""
        key = event.char.lower()
        if key in ['w', 'a', 's', 'd', ' ', 'h', 'q', 'e', 'm']:
            # Space tuşu ' ' olarak gelir, biz 'space' diyoruz
            if key == ' ': key = 'space'
            self.update_callback(key)

    def on_mode_change(self):
        """Radyo buton değişimi"""
        # Mod değişimini callback ile bildir (Format: 'MODE:MANUAL')
        new_mode = self.mode_var.get()
        self.update_callback(f"MODE:{new_mode}")

    def on_emergency_stop(self):
        """Acil durdur butonu"""
        self.update_callback('emergency_stop')

    def create_pid_entry(self, parent, label, default_val):
        """PID metin giriş kutusu oluştur"""
        frame = tk.Frame(parent, bg='black')
        frame.pack(fill=tk.X, pady=2)
        
        label_widget = tk.Label(frame, text=f"{label}:", fg='white', bg='black', font=('Arial', 9), width=6)
        label_widget.pack(side=tk.LEFT, padx=(0, 5))
        
        entry = tk.Entry(frame, bg='gray20', fg='white', font=('Arial', 10), width=12,
                        insertbackground='white', relief=tk.FLAT, bd=2)
        entry.insert(0, str(default_val))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Entry'leri sakla
        if not hasattr(self, 'pid_entries'):
            self.pid_entries = {}
        self.pid_entries[label] = entry

    def on_save_pid(self):
        """PID değerlerini kaydet"""
        pid_values = {}
        try:
            for key, entry in self.pid_entries.items():
                value_str = entry.get().strip()
                pid_values[key] = float(value_str)
            
            # Dosyaya kaydet
            if SettingsManager.save_pid_settings(pid_values):
                self.pid_status_label.config(text="✓ Kaydedildi!", fg='green')
                # Callback ile ana sisteme bildir (format: PID_UPDATE:{dict})
                self.update_callback(f"PID_UPDATE:{pid_values}")
                logger.info(f"GUI'den PID kaydedildi: {pid_values}")
            else:
                self.pid_status_label.config(text="X Hata!", fg='red')
        except ValueError as e:
            self.pid_status_label.config(text="X Geçersiz değer!", fg='red')
            logger.error(f"PID değer hatasız: {e}")
        
        # 2 saniye sonra mesajı temizle
        self.root.after(2000, lambda: self.pid_status_label.config(text=""))

    def load_pid_to_gui(self, pid_values):
        """Kaydedilmiş PID değerlerini GUI'ye yükle (GUI açılışından sonra çağrılır)"""
        if not hasattr(self, 'pid_entries'):
            logger.warning("PID entries yoksa load_pid_to_gui'de henüz oluşturulmamış")
            return
        
        for key, value in pid_values.items():
            if key in self.pid_entries:
                self.pid_entries[key].delete(0, tk.END)
                self.pid_entries[key].insert(0, str(value))
                logger.debug(f"GUI PID yüklendi: {key}={value}")

    def update_frame(self, frame: np.ndarray, detections: list, crosshair: Tuple[int,int], locked=None):
        """Kamera frame güncelle (thread-safe)"""
        self.current_frame = frame
        self.detections = detections
        self.crosshair_pos = crosshair
        # Draw detections burada veya main'de

    def display_frame(self, frame: np.ndarray):
        """Kamera frame'ini canvas üzerinde göster"""
        if frame is None:
            return
        
        try:
            # OpenCV BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # PIL Image
            img = Image.fromarray(frame_rgb)
            # Canvas boyutuna resize et (yüksek çözünürlükte kaymayı önle)
            img = img.resize((self.display_width, self.display_height), Image.Resampling.LANCZOS)
            # PhotoImage
            photo = ImageTk.PhotoImage(image=img)
            # Canvas'a çiz
            self.camera_canvas.delete("all")  # Önceki resmi temizle
            self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            # Referansı tut (garbage collection önleme)
            self.canvas_image_ref = photo
        except Exception as e:
            logger.error(f"Frame display error: {e}")

    def update_status(self, state: str, x_angle: float, y_angle: float, target_status: str, fire_ready: bool, emergency: bool):
        """Durum güncelle"""
        self.current_state = state
        self.x_angle = x_angle
        self.y_angle = y_angle
        self.target_status = target_status
        self.fire_ready = fire_ready
        self.emergency_active = emergency

        # UI güncelle
        self.state_label.config(text=f"Durum: {state}")
        self.angle_label.config(text=f"X: {x_angle:.1f}° Y: {y_angle:.1f}°")
        self.target_label.config(text=f"Hedef: {target_status}")
        self.fire_label.config(text=f"Ateş: {'Hazır' if fire_ready else 'Değil'}")
        if emergency:
            self.emergency_btn.config(bg='darkred')
        else:
            self.emergency_btn.config(bg='red')

    def update_joystick_speed(self, speed_x: float, speed_y: float):
        """Joystick hız verilerini güncelledeki göster"""
        x_sign = "+" if speed_x >= 0 else ""
        y_sign = "+" if speed_y >= 0 else ""
        
        self.joystick_speed_x.config(text=f"Hız X: {x_sign}{int(speed_x)}")
        self.joystick_speed_y.config(text=f"Hız Y: {y_sign}{int(speed_y)}")

    def process_events(self):
        """Ana döngüden çağrılır, GUI olaylarını işler"""
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            pass # Pencere kapatıldıysa hata verme
    def toggle_auto_exposure(self):
        """Auto Exposure ON/OFF değiştir"""
        current_state = getattr(self, 'auto_exposure_state', True)
        new_state = not current_state
        self.auto_exposure_state = new_state
        
        # Butonu güncelle
        if hasattr(self, 'auto_exposure_btn'):
            btn_text = "Auto Exposure: ON" if new_state else "Auto Exposure: OFF"
            btn_color = 'green' if new_state else 'red'
            self.auto_exposure_btn.config(text=btn_text, bg=btn_color)
        
        # Ayarları kaydet
        SettingsManager.save_camera_settings({
            "auto_exposure": 1 if new_state else 0,
            "autofocus": getattr(self, 'autofocus_state', 1)
        })
        
        # Main'e bildir
        value = 1 if new_state else 0
        self.update_callback(f"CAM_SET:{cv2.CAP_PROP_AUTO_EXPOSURE}:{value}")

    def toggle_autofocus(self):
        """Autofocus ON/OFF değiştir"""
        current_state = getattr(self, 'autofocus_state', True)
        new_state = not current_state
        self.autofocus_state = new_state
        
        # Butonu güncelle
        if hasattr(self, 'autofocus_btn'):
            btn_text = "Autofocus: ON" if new_state else "Autofocus: OFF"
            btn_color = 'green' if new_state else 'red'
            self.autofocus_btn.config(text=btn_text, bg=btn_color)
        
        # Ayarları kaydet
        SettingsManager.save_camera_settings({
            "auto_exposure": getattr(self, 'auto_exposure_state', 1),
            "autofocus": 1 if new_state else 0
        })
        
        # Main'e bildir
        value = 1 if new_state else 0
        self.update_callback(f"CAM_SET:{cv2.CAP_PROP_AUTOFOCUS}:{value}")

    def open_camera_calibration(self):
        """Kamera Kalibrasyonu penceresini aç (sadece sliderlar)"""
        # Callback ile main'den kamera değerlerini al
        self.update_callback("GET_CAMERA")
        
        # Yeni pencere
        cal_window = tk.Toplevel(self.root)
        cal_window.title("🔥 Kamera Kalibrasyonu")
        cal_window.geometry("400x600")
        cal_window.configure(bg='black')
        
        # Başlık
        title = tk.Label(cal_window, text="Kamera Parametreleri", 
                        font=("Arial", 14, "bold"), fg='white', bg='black')
        title.pack(pady=10)
        
        # Açıklama
        info = tk.Label(cal_window, 
                       text="Ana ekranda değişiklikleri göreceksiniz",
                       font=("Arial", 9), fg='yellow', bg='black')
        info.pack(pady=5)
        
        # Sliderlar için frame
        slider_frame = tk.Frame(cal_window, bg='black')
        slider_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Mevcut kamera değerlerini al
        current_values = getattr(self, 'current_camera_values', {})
        
        # Parametreler: (ad, min, max, başlangıç, cv2_property)
        parameters = [
            ("Brightness (Parlaklık)", 0, 100, current_values.get(cv2.CAP_PROP_BRIGHTNESS, 50), cv2.CAP_PROP_BRIGHTNESS),
            ("Contrast (Kontrast)", 0, 100, current_values.get(cv2.CAP_PROP_CONTRAST, 50), cv2.CAP_PROP_CONTRAST),
            ("Saturation (Doygunluk)", 0, 100, current_values.get(cv2.CAP_PROP_SATURATION, 50), cv2.CAP_PROP_SATURATION),
            ("Gain (Kazanç)", 0, 100, current_values.get(cv2.CAP_PROP_GAIN, 50), cv2.CAP_PROP_GAIN),
            ("Sharpness (Keskinlik)", 0, 100, current_values.get(cv2.CAP_PROP_SHARPNESS, 50), cv2.CAP_PROP_SHARPNESS),
            ("Hue (Ton)", -180, 180, current_values.get(cv2.CAP_PROP_HUE, 0), cv2.CAP_PROP_HUE),
            ("Gamma (Işık Eğrisi)", 1, 255, current_values.get(cv2.CAP_PROP_GAMMA, 100), cv2.CAP_PROP_GAMMA),
            ("Exposure Comp. (-6 til +6)", -6, 6, current_values.get("EXPOSURE_COMP", 0), "EXPOSURE_COMP"),
        ]
        
        # Sliderları oluştur
        for param_name, min_val, max_val, start_val, cv2_prop in parameters:
            frame = tk.Frame(slider_frame, bg='black')
            frame.pack(fill=tk.X, pady=8)
            
            # Label
            label = tk.Label(frame, text=param_name, fg='white', bg='black', 
                           font=('Arial', 10), width=20, anchor='w')
            label.pack(side=tk.LEFT, padx=5)
            
            # Değer göster
            value_label = tk.Label(frame, text=str(start_val), fg='cyan', bg='black',
                                  font=('Arial', 10, 'bold'), width=5)
            value_label.pack(side=tk.RIGHT, padx=5)
            
            # Slider
            def on_slider_change(val, prop=cv2_prop, vlbl=value_label):
                int_value = int(float(val))
                vlbl.config(text=str(int_value))
                # Ana GUI'ye kamera ayarı değişikliğini bildir
                if prop == "EXPOSURE_COMP":
                    # Exposure compensation özel işlem
                    self.update_callback(f"CAM_SET:EXPOSURE_COMP:{int_value}")
                else:
                    self.update_callback(f"CAM_SET:{prop}:{int_value}")
            
            slider = tk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                orient=tk.HORIZONTAL,
                command=on_slider_change,
                bg='gray30',
                fg='white',
                highlightthickness=0,
                troughcolor='gray50',
                activebackground='cyan',
                length=200
            )
            slider.set(start_val)
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Butonlar
        button_frame = tk.Frame(cal_window, bg='black')
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Auto Exposure ON/OFF
        self.auto_exposure_btn = tk.Button(button_frame, text="Auto Exposure: ON", 
                                          bg='green', fg='white', font=('Arial', 9, 'bold'),
                                          command=lambda: self.toggle_auto_exposure())
        self.auto_exposure_btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        # Autofocus ON/OFF
        self.autofocus_btn = tk.Button(button_frame, text="Autofocus: ON", 
                                      bg='green', fg='white', font=('Arial', 9, 'bold'),
                                      command=lambda: self.toggle_autofocus())
        self.autofocus_btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        def reset_all():
            """Varsayılana sıfırla"""
            self.update_callback("CAM_RESET")
            cal_window.destroy()
            self.open_camera_calibration()  # Yeniden aç
        
        def set_max():
            """Maksimum parlaklık"""
            self.update_callback("CAM_MAX")
            cal_window.destroy()
            self.open_camera_calibration()  # Yeniden aç
        
        reset_btn = tk.Button(button_frame, text="🔄 Sıfırla", 
                             command=reset_all, bg='orange', fg='white',
                             font=('Arial', 10, 'bold'))
        reset_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        max_btn = tk.Button(button_frame, text="💡 Max Parlaklık", 
                           command=set_max, bg='green', fg='white',
                           font=('Arial', 10, 'bold'))
        max_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    def destroy(self):
        self.root.quit()
        self.root.destroy()