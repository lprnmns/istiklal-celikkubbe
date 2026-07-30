"""
Basit Motor Test Programı - Raspberry Pi Pico 2
TMC2209 sürücülerini test etmek için
"""

from machine import Pin
import time

# ============================================================================
# PIN TANIMLARI
# ============================================================================

# X Motoru
STEP_X = 2
DIR_X = 3
MS1_X = 4
MS2_X = 5

# Y Motoru
STEP_Y = 6
DIR_Y = 7
MS1_Y = 8
MS2_Y = 9

# Kontroller
ENABLE = 10
LASER = 11

# ============================================================================
# PIN KURULUMU
# ============================================================================

step_x = Pin(STEP_X, Pin.OUT)
dir_x = Pin(DIR_X, Pin.OUT)
ms1_x = Pin(MS1_X, Pin.OUT)
ms2_x = Pin(MS2_X, Pin.OUT)

step_y = Pin(STEP_Y, Pin.OUT)
dir_y = Pin(DIR_Y, Pin.OUT)
ms1_y = Pin(MS1_Y, Pin.OUT)
ms2_y = Pin(MS2_Y, Pin.OUT)

enable = Pin(ENABLE, Pin.OUT)
laser = Pin(LASER, Pin.OUT)

# ============================================================================
# FONKSİYONLAR
# ============================================================================

def set_microstepping(mode='1/8'):
    """
    Mikroadımlama ayarı
    '1/8', '1/16', '1/32', '1/64'
    """
    modes = {
        '1/8':  (0, 0),
        '1/16': (1, 1),
        '1/32': (1, 0),
        '1/64': (0, 1)
    }
    
    ms1_val, ms2_val = modes.get(mode, (0, 0))
    
    ms1_x.value(ms1_val)
    ms2_x.value(ms2_val)
    ms1_y.value(ms1_val)
    ms2_y.value(ms2_val)
    
    print(f"Mikroadım ayarı: {mode}")

def step_motor(step_pin, steps, delay_us=500):
    """Belirtilen sayıda adım at"""
    for _ in range(steps):
        step_pin.on()
        time.sleep_us(2)
        step_pin.off()
        time.sleep_us(delay_us)

def test_x_motor(steps=200, speed=500):
    """X motorunu test et"""
    print(f"\nX Motoru test: {steps} adım")
    
    # İleri
    print("  → İleri")
    dir_x.value(1)
    time.sleep_ms(10)
    step_motor(step_x, steps, speed)
    time.sleep(1)
    
    # Geri
    print("  ← Geri")
    dir_x.value(0)
    time.sleep_ms(10)
    step_motor(step_x, steps, speed)

def test_y_motor(steps=200, speed=500):
    """Y motorunu test et"""
    print(f"\nY Motoru test: {steps} adım")
    
    # İleri
    print("  ↑ İleri")
    dir_y.value(1)
    time.sleep_ms(10)
    step_motor(step_y, steps, speed)
    time.sleep(1)
    
    # Geri
    print("  ↓ Geri")
    dir_y.value(0)
    time.sleep_ms(10)
    step_motor(step_y, steps, speed)

def test_laser():
    """Lazer testi"""
    print("\nLazer testi:")
    for i in range(3):
        print(f"  {i+1}. Lazer AÇIK")
        laser.on()
        time.sleep(0.5)
        print(f"  {i+1}. Lazer KAPALI")
        laser.off()
        time.sleep(0.5)

# ============================================================================
# ANA TEST
# ============================================================================

def main():
    print("=" * 50)
    print("TMC2209 Motor Test - Raspberry Pi Pico 2")
    print("=" * 50)
    
    # Lazeri kapat
    laser.off()
    
    # Motorları devre dışı bırak
    enable.value(1)
    time.sleep_ms(100)
    
    # Mikroadımlama ayarı
    set_microstepping('1/8')  # Başlangıç için 1/8
    
    # Motorları etkinleştir
    print("\nMotorlar etkinleştiriliyor...")
    enable.value(0)  # LOW = enable
    time.sleep_ms(200)
    
    print("\n✅ Hazır!\n")
    
    # Testleri başlat
    while True:
        print("\n" + "=" * 50)
        print("TEST MENÜSÜ")
        print("=" * 50)
        print("1. X Motorunu Test Et (200 adım)")
        print("2. Y Motorunu Test Et (200 adım)")
        print("3. Her İki Motoru Test Et")
        print("4. Lazer Testi")
        print("5. Mikroadım Değiştir")
        print("6. Hız Testi (Farklı hızlarda)")
        print("0. Çıkış")
        print("=" * 50)
        
        try:
            secim = input("\nSeçim: ")
            
            if secim == '1':
                test_x_motor()
            
            elif secim == '2':
                test_y_motor()
            
            elif secim == '3':
                test_x_motor()
                time.sleep(1)
                test_y_motor()
            
            elif secim == '4':
                test_laser()
            
            elif secim == '5':
                print("\nMikroadım seçenekleri:")
                print("1. 1/8 (önerilen)")
                print("2. 1/16")
                print("3. 1/32")
                print("4. 1/64")
                
                ms_secim = input("Seçim: ")
                modes = {'1': '1/8', '2': '1/16', '3': '1/32', '4': '1/64'}
                mode = modes.get(ms_secim, '1/8')
                set_microstepping(mode)
            
            elif secim == '6':
                print("\nHız testi başlıyor...")
                speeds = [2000, 1000, 500, 250, 100]  # mikrosaniye
                
                for speed in speeds:
                    freq = 1000000 / speed  # Hz
                    print(f"\n  Hız: {speed}µs gecikme ({freq:.0f} Hz)")
                    dir_x.value(1)
                    step_motor(step_x, 100, speed)
                    time.sleep(0.5)
            
            elif secim == '0':
                print("\nMotorlar devre dışı bırakılıyor...")
                enable.value(1)
                laser.off()
                print("Çıkış yapılıyor.")
                break
            
            else:
                print("Geçersiz seçim!")
        
        except KeyboardInterrupt:
            print("\n\nKesme algılandı! Çıkış yapılıyor...")
            enable.value(1)
            laser.off()
            break
        
        except Exception as e:
            print(f"Hata: {e}")

if __name__ == "__main__":
    main()
