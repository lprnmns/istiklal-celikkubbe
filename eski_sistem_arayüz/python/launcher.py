import tkinter as tk
from tkinter import ttk, filedialog
import serial.tools.list_ports
from settings_manager import SettingsManager

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hava Savunma Sistemi - Başlatıcı")
        self.root.geometry("500x550")
        
        self.settings = SettingsManager.load_settings()
        self.result = None # Main.py bu sonucu bekleyecek

        self.setup_ui()

    def setup_ui(self):
        # Stil
        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Başlık
        ttk.Label(main_frame, text="Sistem Ayarları", font=('Arial', 16, 'bold')).pack(pady=(0, 20))

        # --- Model Seçimi ---
        model_frame = ttk.LabelFrame(main_frame, text="Tespit Modeli", padding="10")
        model_frame.pack(fill=tk.X, pady=5)

        self.model_type_var = tk.StringVar(value=self.settings["model_type"])
        ttk.Radiobutton(model_frame, text="OpenCV (Renk Takibi - Hızlı)", variable=self.model_type_var, value="OPENCV", command=self.toggle_path_entry).pack(anchor=tk.W)
        ttk.Radiobutton(model_frame, text="YOLO (Yapay Zeka - Akıllı)", variable=self.model_type_var, value="YOLO", command=self.toggle_path_entry).pack(anchor=tk.W)

        # Path Frame
        self.path_frame = ttk.Frame(model_frame)
        self.path_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(self.path_frame, text="Model Yolu:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(self.path_frame)
        self.path_entry.insert(0, self.settings["model_path"])
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self.path_frame, text="...", width=3, command=self.browse_file).pack(side=tk.LEFT)

        self.toggle_path_entry() # Başlangıç durumu

        # --- Kamera Ayarları ---
        cam_frame = ttk.LabelFrame(main_frame, text="Kamera & Görüntü", padding="10")
        cam_frame.pack(fill=tk.X, pady=5)

        # Grid layout for camera settings
        ttk.Label(cam_frame, text="Kamera Index:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cam_idx_var = tk.StringVar(value=str(self.settings["camera_index"]))
        ttk.Combobox(
            cam_frame,
            textvariable=self.cam_idx_var,
            values=["/dev/video2", "/dev/video0", "/dev/video1", "/dev/video3", "0", "1", "2", "3"],
            width=14,
        ).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(cam_frame, text="Çözünürlük:").grid(row=0, column=2, sticky=tk.W, padx=(10,0))
        self.res_var = tk.StringVar(value=self.settings["resolution"])
        ttk.Combobox(cam_frame, textvariable=self.res_var, 
                    values=["320x240", "640x480", "800x600", "1024x768", "1280x720", "1920x1080", "2560x1440"], 
                    width=12).grid(row=0, column=3, sticky=tk.W)

        ttk.Label(cam_frame, text="FPS Hedefi:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fps_var = tk.StringVar(value=str(self.settings["fps"]))
        ttk.Combobox(cam_frame, textvariable=self.fps_var, 
                    values=["15", "24", "30", "60", "120"], 
                    width=5).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(cam_frame, text="Titreşim Azaltma:").grid(row=1, column=2, sticky=tk.W, padx=(10,0))
        self.stabilization_var = tk.StringVar(value=self.settings.get("stabilization", "Normal"))
        ttk.Combobox(cam_frame, textvariable=self.stabilization_var, 
                    values=["Kapalı", "Düşük", "Normal", "Yüksek"], 
                    width=10).grid(row=1, column=3, sticky=tk.W)

        # --- Donanım Ayarları ---
        hw_frame = ttk.LabelFrame(main_frame, text="Donanım & Motor", padding="10")
        hw_frame.pack(fill=tk.X, pady=5)

        ttk.Label(hw_frame, text="Arduino Port:").grid(row=0, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value=self.settings["port"])
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports: ports = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"]
        ttk.Combobox(hw_frame, textvariable=self.port_var, values=ports, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(hw_frame, text="Motor Hızı:").grid(row=0, column=2, sticky=tk.W, padx=(10,0))
        self.speed_var = tk.StringVar(value=self.settings["motor_speed"])
        ttk.Combobox(hw_frame, textvariable=self.speed_var, values=["Slow", "Medium", "Fast"], width=10).grid(row=0, column=3, sticky=tk.W)

        self.serial_tx_var = tk.BooleanVar(value=bool(self.settings.get("enable_serial_tx", False)))
        ttk.Checkbutton(
            hw_frame,
            text="Serial TX etkinleştir (varsayılan kapalı)",
            variable=self.serial_tx_var,
        ).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(8, 0))
        ttk.Label(
            hw_frame,
            text="Güvenli mod: motor/tetik komutu gönderilmez; no_physical_command_generated=true",
            foreground="red",
        ).grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(4, 0))

        # --- Başlangıç Ayarları ---
        start_frame = ttk.LabelFrame(main_frame, text="Başlangıç", padding="10")
        start_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(start_frame, text="Başlangıç Modu:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value=self.settings.get("startup_mode", "IDLE"))
        ttk.Combobox(start_frame, textvariable=self.mode_var, values=["IDLE", "MANUAL", "AUTO"], width=10).pack(side=tk.LEFT, padx=5)

        # --- Başlat Butonu ---
        ttk.Button(main_frame, text="SİSTEMİ BAŞLAT", command=self.start_system).pack(fill=tk.X, pady=20, ipady=10)

    def toggle_path_entry(self):
        if self.model_type_var.get() == "YOLO":
            for child in self.path_frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.path_frame.winfo_children():
                child.configure(state='disabled')

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("YOLO Models", "*.pt"), ("All Files", "*.*")])
        if filename:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filename)

    def start_system(self):
        # Ayarları güncelle
        self.settings["model_type"] = self.model_type_var.get()
        self.settings["model_path"] = self.path_entry.get()
        camera_value = self.cam_idx_var.get()
        self.settings["camera_index"] = int(camera_value) if camera_value.isdigit() else camera_value
        self.settings["resolution"] = self.res_var.get()
        self.settings["fps"] = int(self.fps_var.get())
        self.settings["port"] = self.port_var.get()
        self.settings["motor_speed"] = self.speed_var.get()
        self.settings["startup_mode"] = self.mode_var.get()
        self.settings["stabilization"] = self.stabilization_var.get()
        self.settings["enable_serial_tx"] = bool(self.serial_tx_var.get())
        self.settings["safe_dry_run"] = not bool(self.serial_tx_var.get())
        self.settings["no_physical_command_generated"] = True

        # Kaydet
        SettingsManager.save_settings(self.settings)
        
        # Sonucu ayarla ve kapat
        self.result = self.settings
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.result

if __name__ == "__main__":
    l = Launcher()
    print(l.run())
