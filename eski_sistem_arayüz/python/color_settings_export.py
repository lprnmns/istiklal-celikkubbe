# color_settings_export.py - Renk Ayarlarını JSON Olarak Kaydet/Yükle
"""
color_tuner.py'den bulduğun optimal ayarları buraya kaydet ve kullan.

Kullanım:
    python color_settings_export.py --export > optimal_colors.json
    python color_settings_export.py --apply optimal_colors.json
    python color_settings_export.py --show
"""

import json
import argparse
from pathlib import Path

# Varsayılan ayarlar
DEFAULT_SETTINGS = {
    "lower_red1": [0, 80, 50],
    "upper_red1": [10, 255, 255],
    "lower_red2": [170, 80, 50],
    "upper_red2": [180, 255, 255],
    "min_area": 300,
    "close_iter": 2,
    "open_iter": 1,
    "blur_size": 9,
    "description": "Standart - Toleranslı kırmızı algılama"
}

# Hazır presetler
PRESETS = {
    "strict": {
        "lower_red1": [0, 120, 70],
        "upper_red1": [10, 255, 255],
        "lower_red2": [170, 120, 70],
        "upper_red2": [180, 255, 255],
        "min_area": 500,
        "close_iter": 2,
        "open_iter": 1,
        "blur_size": 11,
        "description": "Katı - Az gürültü, daha az tespit"
    },
    "sensitive": {
        "lower_red1": [0, 50, 30],
        "upper_red1": [10, 255, 255],
        "lower_red2": [170, 50, 30],
        "upper_red2": [180, 255, 255],
        "min_area": 200,
        "close_iter": 3,
        "open_iter": 1,
        "blur_size": 7,
        "description": "Hassas - Çok tespit, daha fazla gürültü"
    },
    "balanced": {
        "lower_red1": [0, 80, 50],
        "upper_red1": [10, 255, 255],
        "lower_red2": [170, 80, 50],
        "upper_red2": [180, 255, 255],
        "min_area": 300,
        "close_iter": 2,
        "open_iter": 1,
        "blur_size": 9,
        "description": "Dengeli - Standard ayarlar"
    },
    "bright_light": {
        "lower_red1": [0, 100, 100],
        "upper_red1": [10, 255, 255],
        "lower_red2": [170, 100, 100],
        "upper_red2": [180, 255, 255],
        "min_area": 400,
        "close_iter": 2,
        "open_iter": 1,
        "blur_size": 9,
        "description": "Parlak aydınlatma için"
    },
    "dim_light": {
        "lower_red1": [0, 60, 40],
        "upper_red1": [10, 255, 255],
        "lower_red2": [170, 60, 40],
        "upper_red2": [180, 255, 255],
        "min_area": 200,
        "close_iter": 3,
        "open_iter": 1,
        "blur_size": 9,
        "description": "Karanlık aydınlatma için"
    }
}

def generate_python_code(settings):
    """Settings'i Python kodu olarak üret"""
    code = f"""# Renk Algılama Ayarları (yolo_detector.py'ye yapıştır)
import numpy as np

# ColorDetector.__init__() içine yapıştır:
self.lower_red1 = np.array({settings['lower_red1']})
self.upper_red1 = np.array({settings['upper_red1']})
self.lower_red2 = np.array({settings['lower_red2']})
self.upper_red2 = np.array({settings['upper_red2']})

self.min_area = {settings['min_area']}
self.close_iter = {settings['close_iter']}
self.open_iter = {settings['open_iter']}
self.blur_size = {settings['blur_size']}
"""
    return code

def show_settings(settings, name=""):
    """Ayarları güzelce göster"""
    print("\n" + "="*70)
    if name:
        print(f"📋 {name}")
    print("="*70)
    print(f"Açıklama: {settings.get('description', 'N/A')}")
    print(f"\n🎨 Hue:")
    print(f"   Range 1: {settings['lower_red1'][0]:3d}-{settings['upper_red1'][0]:3d}")
    print(f"   Range 2: {settings['lower_red2'][0]:3d}-{settings['upper_red2'][0]:3d}")
    print(f"\n📊 Saturation: {settings['lower_red1'][1]:3d}-{settings['upper_red1'][1]:3d}")
    print(f"📊 Value:      {settings['lower_red1'][2]:3d}-{settings['upper_red1'][2]:3d}")
    print(f"\n⚙️  Min Area:     {settings['min_area']}")
    print(f"⚙️  Close Iter:   {settings['close_iter']}")
    print(f"⚙️  Open Iter:    {settings['open_iter']}")
    print(f"⚙️  Blur Size:    {settings['blur_size']}")
    print("="*70)

def main():
    parser = argparse.ArgumentParser(description="Renk Ayarlarını Yönet")
    parser.add_argument("--export", action="store_true", help="Ayarları JSON olarak çıkart")
    parser.add_argument("--show", action="store_true", help="Mevcut ayarları göster")
    parser.add_argument("--apply", type=str, help="JSON dosyasından ayarları yükle")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Hazır preset'i kullan")
    parser.add_argument("--list-presets", action="store_true", help="Tüm presetleri listele")
    parser.add_argument("--compare", action="store_true", help="Tüm presetleri karşılaştır")
    
    args = parser.parse_args()
    
    if args.list_presets:
        print("\n📦 Mevcut Presetler:")
        for name in PRESETS.keys():
            print(f"  - {name}")
        return
    
    if args.compare:
        print("\n📊 TÜM PRESETLER KARŞILAŞTIRMASI\n")
        for name, settings in PRESETS.items():
            show_settings(settings, name.upper())
        return
    
    if args.preset:
        settings = PRESETS[args.preset]
        show_settings(settings, f"PRESET: {args.preset.upper()}")
        print(f"\n{generate_python_code(settings)}")
        return
    
    if args.show:
        show_settings(DEFAULT_SETTINGS, "MEVCUT AYARLAR")
        return
    
    if args.export:
        print(json.dumps(DEFAULT_SETTINGS, indent=2))
        return
    
    if args.apply:
        try:
            with open(args.apply) as f:
                settings = json.load(f)
            show_settings(settings, f"YÜKLENEN: {args.apply}")
            print(f"\n{generate_python_code(settings)}")
        except FileNotFoundError:
            print(f"❌ Dosya bulunamadı: {args.apply}")
        except json.JSONDecodeError:
            print(f"❌ Geçersiz JSON: {args.apply}")
        return
    
    # Varsayılan: Tüm presetleri göster
    parser.print_help()

if __name__ == "__main__":
    main()
