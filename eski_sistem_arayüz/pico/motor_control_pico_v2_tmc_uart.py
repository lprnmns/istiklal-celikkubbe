"""
Raspberry Pi Pico 2 Motor Kontrol Kodu V2.0
Hava Savunma Sistemi - TMC2209 UART Optimizasyonlu

ÖZELLİKLER:
- TMC2209 UART ile gelişmiş motor kontrolü
- Mikroadım interpolasyonu (256 adım hassasiyet)
- StealthChop ↔ SpreadCycle otomatik geçiş
- CoolStep (yük adaptif akım kontrolü)
- Optimize chopper parametreleri

UART BAĞLANTILARI:
- UART0: Python ile iletişim (GPIO0/GPIO1)
- UART1: TMC2209 kontrolü (GPIO4/GPIO5)

NOT: MS1/MS2 pinleri artık UART tarafından kontrol ediliyor!
"""

from machine import Pin, UART
import time
import _thread

# TMC2209 Advanced kütüphanesini import et
try:
    from tmc2209_advanced import TMC2209Advanced
    TMC_AVAILABLE = True
    print("✅ TMC2209 Advanced modülü yüklendi")
except ImportError:
    print("⚠️ TMC2209 Advanced modülü bulunamadı - temel mod kullanılacak")
    TMC_AVAILABLE = False

# ============================================================================
# PIN TANIMLARI - Raspberry Pi Pico 2
# ============================================================================

# X Motoru (Yatay - Pan)
STEP_X_PIN = 2      # GPIO2 - Step pulse
DIR_X_PIN = 3       # GPIO3 - Direction

# Y Motoru (Dikey - Tilt)
STEP_Y_PIN = 6      # GPIO6 - Step pulse
DIR_Y_PIN = 7       # GPIO7 - Direction

# Ortak Kontroller
ENABLE_PIN = 10     # GPIO10 - Her iki motor için ortak ENABLE (LOW = aktif)
LASER_PIN = 11      # GPIO11 - Lazer kontrol
EMERGENCY_STOP_PIN = 12  # GPIO12 - Acil durdur butonu (Pull-up ile)

# UART (Python ile iletişim için)
UART_ID = 0         # UART0
UART_TX = 0         # GPIO0 (TX)
UART_RX = 1         # GPIO1 (RX)
UART_BAUDRATE = 115200

# TMC2209 UART
TMC_UART_ID = 1     # UART1
TMC_TX = 4          # GPIO4 (Pico TX → TMC RX)
TMC_RX = 5          # GPIO5 (Pico RX → TMC TX)
TMC_BAUDRATE = 115200

# TMC2209 Slave Adresleri
# MS1_AD0 ve MS2_AD1 pinleri ile ayarlanır
TMC_ADDR_X = 0x00   # X motoru (MS1=LOW, MS2=LOW)
TMC_ADDR_Y = 0x00   # Y motoru (aynı adres - aynı sürücü ise)
# Eğer iki ayrı sürücü varsa: TMC_ADDR_Y = 0x01

# ============================================================================
# HIZ VE ZAMANLAMA AYARLARI
# ============================================================================

MIN_STEP_DELAY_US = 50      # Minimum adım gecikmesi (maksimum hız)
MAX_STEP_DELAY_US = 2000    # Maksimum adım gecikmesi (başlangıç hızı)
ACCEL_RATE = 0.05           # Hızlanma/yavaşlama oranı

# ============================================================================
# TMC2209 KONFİGÜRASYON SEÇENEKLERİ
# ============================================================================

# Hangi konfigürasyon kullanılacak?
# 'speed'      - X ekseni için maksimum hız
# 'precision'  - Y ekseni için hassasiyet
# 'balanced'   - Her ikisi için dengeli
# 'manual'     - Manuel ayarlar (eski MS1/MS2 modu)

TMC_MODE_X = 'speed'       # X ekseni: HIZ modu
TMC_MODE_Y = 'precision'   # Y ekseni: HASSASİYET modu

# ============================================================================
# PIN KURULUMU
# ============================================================================

# Motor pinleri
step_x = Pin(STEP_X_PIN, Pin.OUT)
dir_x = Pin(DIR_X_PIN, Pin.OUT)

step_y = Pin(STEP_Y_PIN, Pin.OUT)
dir_y = Pin(DIR_Y_PIN, Pin.OUT)

enable = Pin(ENABLE_PIN, Pin.OUT)
laser = Pin(LASER_PIN, Pin.OUT)
emergency_stop = Pin(EMERGENCY_STOP_PIN, Pin.IN, Pin.PULL_UP)

# UART kurulumu (Python ile iletişim)
uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX), rx=Pin(UART_RX))

# TMC2209 sürücüleri
tmc_x = None
tmc_y = None

# ============================================================================
# TMC2209 BAŞLATMA
# ============================================================================

def init_tmc2209():
    """TMC2209 sürücülerini başlat"""
    global tmc_x, tmc_y
    
    if not TMC_AVAILABLE:
        print("⚠️ TMC2209 modu devre dışı - temel mod kullanılıyor")
        return False
    
    try:
        print("\n" + "=" * 60)
        print(" TMC2209 UART BAŞLATILIYOR")
        print("=" * 60)
        
        # X Motor
        print("\n🔧 X Motoru yapılandırılıyor...")
        tmc_x = TMC2209Advanced(TMC_UART_ID, TMC_TX, TMC_RX, slave_address=TMC_ADDR_X)
        
        if TMC_MODE_X == 'speed':
            tmc_x.init_for_speed(axis='x')
        elif TMC_MODE_X == 'precision':
            tmc_x.init_for_precision(axis='x')
        elif TMC_MODE_X == 'balanced':
            tmc_x.init_balanced()
        else:
            print(f"⚠️ Bilinmeyen mod: {TMC_MODE_X} - balanced kullanılıyor")
            tmc_x.init_balanced()
        
        time.sleep(0.5)
        
        # Y Motor (sadece farklı adres varsa)
        if TMC_ADDR_Y != TMC_ADDR_X:
            print("\n🔧 Y Motoru yapılandırılıyor...")
            tmc_y = TMC2209Advanced(TMC_UART_ID, TMC_TX, TMC_RX, slave_address=TMC_ADDR_Y)
            
            if TMC_MODE_Y == 'speed':
                tmc_y.init_for_speed(axis='y')
            elif TMC_MODE_Y == 'precision':
                tmc_y.init_for_precision(axis='y')
            elif TMC_MODE_Y == 'balanced':
                tmc_y.init_balanced()
            else:
                tmc_y.init_balanced()
            
            time.sleep(0.5)
        else:
            print("\n⚠️ Y motoru X ile aynı sürücüyü kullanıyor")
            tmc_y = tmc_x  # Aynı sürücü
        
        # Durum kontrolü
        print("\n" + "=" * 60)
        print(" DURUM KONTROLÜ")
        print("=" * 60)
        
        print("\n📊 X Motoru:")
        tmc_x.print_status()
        
        if tmc_y and tmc_y != tmc_x:
            print("\n📊 Y Motoru:")
            tmc_y.print_status()
        
        print("\n" + "=" * 60)
        print("✅ TMC2209 başlatma tamamlandı!")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TMC2209 başlatma hatası: {e}")
        print("⚠️ Temel mod kullanılacak\n")
        return False

# ============================================================================
# GLOBAL DEĞİŞKENLER
# ============================================================================

# Hedef gecikme değerleri (0 = dur)
target_delay_x = 0
target_delay_y = 0

# Anlık gecikme değerleri
current_delay_x = 0.0
current_delay_y = 0.0

# Son adım zamanları (mikrosaniye)
last_step_time_x = 0
last_step_time_y = 0

# Komut buffer
cmd_buffer = ""

# Durum raporu
last_status_time = 0

# Thread kilit
lock = _thread.allocate_lock()

# TMC2209 durumu
tmc_enabled = False

# ============================================================================
# MOTOR SÜRME FONKSİYONLARI
# ============================================================================

def step_motor(step_pin, delay_us=2):
    """Tek adım at"""
    step_pin.on()
    time.sleep_us(delay_us)
    step_pin.off()

def motor_task():
    """Motor sürme görevi (ayrı thread'de çalışır)"""
    global current_delay_x, current_delay_y
    global last_step_time_x, last_step_time_y
    global target_delay_x, target_delay_y
    
    while True:
        # Acil durdur kontrolü
        if emergency_stop.value() == 0:  # Butona basıldı
            with lock:
                target_delay_x = 0
                target_delay_y = 0
                current_delay_x = 0.0
                current_delay_y = 0.0
            time.sleep_ms(10)
            continue
        
        current_time = time.ticks_us()
        
        # X Motoru
        with lock:
            tgt_x = target_delay_x
            cur_x = current_delay_x
        
        if tgt_x > 0:
            # Hızlanma/yavaşlama
            if cur_x == 0:
                cur_x = MAX_STEP_DELAY_US
            
            if cur_x > tgt_x:
                cur_x -= ACCEL_RATE
            elif cur_x < tgt_x:
                cur_x += ACCEL_RATE
            
            # Adım atma
            if time.ticks_diff(current_time, last_step_time_x) >= int(cur_x):
                last_step_time_x = current_time
                step_motor(step_x)
            
            with lock:
                current_delay_x = cur_x
        else:
            with lock:
                current_delay_x = 0.0
        
        # Y Motoru
        with lock:
            tgt_y = target_delay_y
            cur_y = current_delay_y
        
        if tgt_y > 0:
            if cur_y == 0:
                cur_y = MAX_STEP_DELAY_US
            
            if cur_y > tgt_y:
                cur_y -= ACCEL_RATE
            elif cur_y < tgt_y:
                cur_y += ACCEL_RATE
            
            if time.ticks_diff(current_time, last_step_time_y) >= int(cur_y):
                last_step_time_y = current_time
                step_motor(step_y)
            
            with lock:
                current_delay_y = cur_y
        else:
            with lock:
                current_delay_y = 0.0
        
        time.sleep_us(10)  # CPU'ya nefes aldır

# ============================================================================
# KOMUT İŞLEME
# ============================================================================

def map_value(x, in_min, in_max, out_min, out_max):
    """Arduino map() fonksiyonu"""
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def process_command(cmd):
    """Serial komutları işle"""
    global target_delay_x, target_delay_y
    
    cmd = cmd.strip()
    parts = cmd.split(',')
    
    if cmd.startswith("SPD") and len(parts) == 3:
        # FORMAT: SPD,HIZ_X,HIZ_Y
        # -1000 ile 1000 arası değer
        
        try:
            val_x = int(parts[1])
            val_y = int(parts[2])
            
            # X Motoru
            if val_x == 0:
                with lock:
                    target_delay_x = 0
            else:
                dir_x.value(1 if val_x > 0 else 0)
                speed = min(abs(val_x), 1000)
                delay = map_value(speed, 1, 1000, MAX_STEP_DELAY_US, MIN_STEP_DELAY_US)
                
                with lock:
                    target_delay_x = delay
            
            # Y Motoru
            if val_y == 0:
                with lock:
                    target_delay_y = 0
            else:
                dir_y.value(1 if val_y > 0 else 0)
                speed = min(abs(val_y), 1000)
                delay = map_value(speed, 1, 1000, MAX_STEP_DELAY_US, MIN_STEP_DELAY_US)
                
                with lock:
                    target_delay_y = delay
        
        except ValueError:
            uart.write("ERR,INVALID_SPD\n")
    
    elif cmd.startswith("LZR") and len(parts) == 2:
        # FORMAT: LZR,0 veya LZR,1
        try:
            state = int(parts[1])
            laser.value(state)
            uart.write(f"OK,LASER_{state}\n")
        except ValueError:
            uart.write("ERR,INVALID_LZR\n")
    
    elif cmd == "PING":
        uart.write("OK,PONG\n")
    
    elif cmd == "TMC_STATUS":
        # TMC2209 durum raporu
        if tmc_enabled and tmc_x:
            status_x = tmc_x.get_status()
            if status_x:
                mode = 'StealthChop' if status_x['stealth'] else 'SpreadCycle'
                uart.write(f"TMC_X,{mode},{status_x['cs_actual']}\n")
            else:
                uart.write("TMC_X,NO_COMM\n")
        else:
            uart.write("TMC,DISABLED\n")
    
    elif cmd.startswith("TMC_CURRENT") and len(parts) == 2:
        # FORMAT: TMC_CURRENT,1200
        # Çalışma akımını değiştir
        try:
            current = int(parts[1])
            if tmc_enabled and tmc_x:
                tmc_x.set_current_advanced(run_current=current, hold_current=int(current*0.3))
                uart.write(f"OK,TMC_CURRENT_{current}\n")
            else:
                uart.write("ERR,TMC_DISABLED\n")
        except ValueError:
            uart.write("ERR,INVALID_CURRENT\n")
    
    else:
        uart.write("ERR,UNKNOWN_CMD\n")

# ============================================================================
# SERIAL OKUMA
# ============================================================================

def serial_task():
    """Serial komut okuma görevi"""
    global cmd_buffer
    
    while True:
        if uart.any():
            data = uart.read()
            if data:
                try:
                    text = data.decode('utf-8')
                    for char in text:
                        if char == '\n':
                            if cmd_buffer:
                                process_command(cmd_buffer)
                                cmd_buffer = ""
                        else:
                            cmd_buffer += char
                except:
                    pass
        
        time.sleep_ms(5)

# ============================================================================
# DURUM RAPORU
# ============================================================================

def status_task():
    """Periyodik durum raporu"""
    global last_status_time
    
    while True:
        current_time = time.ticks_ms()
        
        if time.ticks_diff(current_time, last_status_time) >= 500:
            with lock:
                tx = target_delay_x
                ty = target_delay_y
            
            if tx > 0 or ty > 0:
                uart.write("STS,MOVING\n")
            else:
                uart.write("STS,READY\n")
            
            last_status_time = current_time
        
        time.sleep_ms(100)

# ============================================================================
# ANA PROGRAM
# ============================================================================

def main():
    """Ana başlatma fonksiyonu"""
    global tmc_enabled
    
    print("\n" + "=" * 60)
    print(" HAVA SAVUNMA SİSTEMİ - PICO 2 MOTOR KONTROL V2.0")
    print("=" * 60)
    
    # Motorları devre dışı bırak
    enable.value(1)  # HIGH = disable
    time.sleep_ms(100)
    
    # Lazeri kapat
    laser.value(0)
    
    # TMC2209 başlat
    tmc_enabled = init_tmc2209()
    
    # Motorları etkinleştir
    enable.value(0)  # LOW = enable
    time.sleep_ms(100)
    
    print("\n📌 PIN KONFIGÜRASYONU:")
    print(f"  X Motor: STEP={STEP_X_PIN}, DIR={DIR_X_PIN}")
    print(f"  Y Motor: STEP={STEP_Y_PIN}, DIR={DIR_Y_PIN}")
    print(f"  Kontrol: ENABLE={ENABLE_PIN}, LASER={LASER_PIN}, E-STOP={EMERGENCY_STOP_PIN}")
    print(f"  UART0: TX={UART_TX}, RX={UART_RX}, Baudrate={UART_BAUDRATE}")
    
    if tmc_enabled:
        print(f"  UART1 (TMC): TX={TMC_TX}, RX={TMC_RX}, Baudrate={TMC_BAUDRATE}")
        print(f"  TMC Mode: X={TMC_MODE_X}, Y={TMC_MODE_Y}")
    else:
        print("  TMC2209: ⚠️ Devre dışı")
    
    print("\n✅ Sistem hazır!")
    uart.write("OK,PICO_READY_V2\n")
    
    # Thread'leri başlat
    _thread.start_new_thread(motor_task, ())
    _thread.start_new_thread(status_task, ())
    
    # Ana thread'de serial okuma
    serial_task()

# ============================================================================
# BAŞLAT
# ============================================================================

if __name__ == "__main__":
    main()
