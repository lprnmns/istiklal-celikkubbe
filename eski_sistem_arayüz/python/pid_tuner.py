# pid_tuner.py - PID Değerlerini Test Edebilmek için CLI Tool
"""
Kullanım:
    python pid_tuner.py --kp-x 1.2 --ki-x 0.0005 --kd-x 0.8
    python pid_tuner.py --preset stable
    python pid_tuner.py --preset aggressive
    python pid_tuner.py --preset default
"""

from config import PIDConfig
import argparse

# Preset konfigürasyonları
PRESETS = {
    "stable": {
        "KP_X": 1.2, "KI_X": 0.0005, "KD_X": 0.8,
        "KP_Y": 0.9, "KI_Y": 0.0003, "KD_Y": 0.7,
        "OUTPUT_MIN": -8000.0, "OUTPUT_MAX": 8000.0,
        "MIN_MOVE_SPEED": 120.0, "INTEGRAL_MAX": 3000.0,
        "description": "Stabil - Salınım yok, hedefi tutar, yavaş yanıt"
    },
    "balanced": {
        "KP_X": 1.8, "KI_X": 0.0008, "KD_X": 1.0,
        "KP_Y": 1.3, "KI_Y": 0.0005, "KD_Y": 0.9,
        "OUTPUT_MIN": -12000.0, "OUTPUT_MAX": 12000.0,
        "MIN_MOVE_SPEED": 80.0, "INTEGRAL_MAX": 5000.0,
        "description": "Dengeli - Hız ve stabilite dengesi"
    },
    "aggressive": {
        "KP_X": 2.2, "KI_X": 0.001, "KD_X": 1.2,
        "KP_Y": 1.8, "KI_Y": 0.0008, "KD_Y": 1.1,
        "OUTPUT_MIN": -15000.0, "OUTPUT_MAX": 15000.0,
        "MIN_MOVE_SPEED": 60.0, "INTEGRAL_MAX": 8000.0,
        "description": "Agresif - Hızlı yanıt, daha fazla salınım riski"
    },
    "default": {
        "KP_X": 2.5, "KI_X": 0.001, "KD_X": 0.35,
        "KP_Y": 1.3, "KI_Y": 0.001, "KD_Y": 0.35,
        "OUTPUT_MIN": -30000.0, "OUTPUT_MAX": 30000.0,
        "MIN_MOVE_SPEED": 35.0, "INTEGRAL_MAX": 25000.0,
        "description": "Varsayılan (Orijinal) - En hızlı, en fazla salınım"
    },
}

def generate_config_patch(values: dict) -> str:
    """Config.py için patch kodu üret"""
    code = """# === PID AYARLARI GÜNCELLEME KODU (config.py'ye yapıştır) ===

@dataclass
class PIDConfig:
    # PID kazançları
    KP_X: float = {KP_X}
    KI_X: float = {KI_X}
    KD_X: float = {KD_X}
    
    KP_Y: float = {KP_Y}
    KI_Y: float = {KI_Y}
    KD_Y: float = {KD_Y}

    # Output limitleri
    OUTPUT_MIN: float = {OUTPUT_MIN}
    OUTPUT_MAX: float = {OUTPUT_MAX}
    
    # Minimum hareket eşiği
    MIN_MOVE_SPEED: float = {MIN_MOVE_SPEED}

    INTEGRAL_MAX: float = {INTEGRAL_MAX}
""".format(**values)
    return code

def print_pid_params(name: str, params: dict):
    """PID parametrelerini formatlı yazdır"""
    print(f"\n{'='*70}")
    print(f"📊 {name}")
    print(f"{'='*70}")
    print(f"Açıklama: {params.get('description', 'N/A')}")
    print(f"\n🎮 X Ekseni:")
    print(f"   KP_X:         {params['KP_X']:.4f}")
    print(f"   KI_X:         {params['KI_X']:.6f}")
    print(f"   KD_X:         {params['KD_X']:.4f}")
    print(f"\n🎮 Y Ekseni:")
    print(f"   KP_Y:         {params['KP_Y']:.4f}")
    print(f"   KI_Y:         {params['KI_Y']:.6f}")
    print(f"   KD_Y:         {params['KD_Y']:.4f}")
    print(f"\n⚙️  Output Limitleri:")
    print(f"   OUTPUT_MIN:   {params['OUTPUT_MIN']:.0f}")
    print(f"   OUTPUT_MAX:   {params['OUTPUT_MAX']:.0f}")
    print(f"   MIN_MOVE_SPEED: {params['MIN_MOVE_SPEED']:.0f}")
    print(f"   INTEGRAL_MAX: {params['INTEGRAL_MAX']:.0f}")
    print(f"{'='*70}")

def main():
    parser = argparse.ArgumentParser(description="PID Tuner - Salınım ve Takip Problemleri İçin")
    
    # Preset argümanları
    parser.add_argument("--preset", choices=list(PRESETS.keys()), 
                       help="Önceden tanımlanmış preset kullan")
    
    # Manuel argümanlar
    parser.add_argument("--kp-x", type=float, help="KP_X (Proportional X)")
    parser.add_argument("--ki-x", type=float, help="KI_X (Integral X)")
    parser.add_argument("--kd-x", type=float, help="KD_X (Derivative X)")
    parser.add_argument("--kp-y", type=float, help="KP_Y (Proportional Y)")
    parser.add_argument("--ki-y", type=float, help="KI_Y (Integral Y)")
    parser.add_argument("--kd-y", type=float, help="KD_Y (Derivative Y)")
    parser.add_argument("--output-min", type=float, help="OUTPUT_MIN")
    parser.add_argument("--output-max", type=float, help="OUTPUT_MAX")
    parser.add_argument("--min-speed", type=float, help="MIN_MOVE_SPEED")
    parser.add_argument("--integral-max", type=float, help="INTEGRAL_MAX")
    
    parser.add_argument("--compare", action="store_true", help="Tüm presetleri karşılaştır")
    parser.add_argument("--current", action="store_true", help="Şu anki config'i göster")
    
    args = parser.parse_args()
    
    # Karşılaştırma modu
    if args.compare:
        print("\n🔍 TÜM PRESETLER KARŞILAŞTIRMASI:\n")
        for preset_name, preset_values in PRESETS.items():
            print_pid_params(preset_name.upper(), preset_values)
        return
    
    # Şu anki config'i göster
    if args.current:
        current = {
            'KP_X': 1.2, 'KI_X': 0.0005, 'KD_X': 0.8,
            'KP_Y': 0.9, 'KI_Y': 0.0003, 'KD_Y': 0.7,
            'OUTPUT_MIN': -8000.0, 'OUTPUT_MAX': 8000.0,
            'MIN_MOVE_SPEED': 120.0, 'INTEGRAL_MAX': 3000.0,
            'description': 'Şu Anki Yapılandırma'
        }
        print_pid_params("ŞU ANKI KONFİG", current)
        return
    
    # Preset kullan
    if args.preset:
        values = PRESETS[args.preset].copy()
    else:
        # Manuel override'lar
        values = PRESETS["stable"].copy()  # Default olarak stable başla
        if args.kp_x is not None: values['KP_X'] = args.kp_x
        if args.ki_x is not None: values['KI_X'] = args.ki_x
        if args.kd_x is not None: values['KD_X'] = args.kd_x
        if args.kp_y is not None: values['KP_Y'] = args.kp_y
        if args.ki_y is not None: values['KI_Y'] = args.ki_y
        if args.kd_y is not None: values['KD_Y'] = args.kd_y
        if args.output_min is not None: values['OUTPUT_MIN'] = args.output_min
        if args.output_max is not None: values['OUTPUT_MAX'] = args.output_max
        if args.min_speed is not None: values['MIN_MOVE_SPEED'] = args.min_speed
        if args.integral_max is not None: values['INTEGRAL_MAX'] = args.integral_max
    
    print_pid_params("YENİ AYARLAR", values)
    print(f"\n💾 Yapılandırma Kodu:\n{generate_config_patch(values)}")
    print("\n⚡ İpuçları:")
    print("  1. Salınım çok fazla? → KD (Derivative) artır veya KP (Proportional) düşür")
    print("  2. Hedefi tutmuyor? → KP artır (ama salınıma dikkat et)")
    print("  3. Yavaş takip? → KP artır, OUTPUT_MAX artır")
    print("  4. Jitter/titreşim? → MIN_MOVE_SPEED artır")
    print("  5. Çok hassas? → Smoothing factor'u (main.py:550) düşür (0.3 -> 0.2)")

if __name__ == "__main__":
    main()
