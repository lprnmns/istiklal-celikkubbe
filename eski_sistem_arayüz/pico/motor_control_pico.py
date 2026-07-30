"""
Raspberry Pi Pico 2 Motor Kontrol Kodu
Hava Savunma Sistemi - TMC2209 Sürücü Desteği

TMC2209 MANUEL MICROSTEP AYARI (UART'sız mod):
- MS1 ve MS2 pinlerini kullanarak mikroadımlama ayarı
- MS1=LOW, MS2=LOW  -> 1/8 mikroadım (önerilen başlangıç)
- MS1=HIGH, MS2=LOW -> 1/32 mikroadım
- MS1=LOW, MS2=HIGH -> 1/64 mikroadım
- MS1=HIGH, MS2=HIGH -> 1/16 mikroadım

İlerleyen aşamada UART eklenebilir.
"""

from machine import Pin, UART
import time
import _thread

# ============================================================================
# PIN TANIMLARI - Raspberry Pi Pico 2
# ============================================================================

# X Motoru (Yatay - Pan)
STEP_X_PIN = 2      # GPIO2 - Step pulse
DIR_X_PIN = 3       # GPIO3 - Direction
MS1_X_PIN = 4       # GPIO4 - Mikroadım ayar 1
MS2_X_PIN = 5       # GPIO5 - Mikroadım ayar 2

# Y Motoru (Dikey - Tilt)
STEP_Y_PIN = 6      # GPIO6 - Step pulse
DIR_Y_PIN = 7       # GPIO7 - Direction
MS1_Y_PIN = 8       # GPIO8 - Mikroadım ayar 1
MS2_Y_PIN = 9       # GPIO9 - Mikroadım ayar 2

# Ortak Kontroller
ENABLE_PIN = 10     # GPIO10 - Her iki motor için ortak ENABLE (LOW = aktif)
LASER_PIN = 11      # GPIO11 - Lazer kontrol
EMERGENCY_STOP_PIN = 12  # GPIO12 - Acil durdur butonu (Pull-up ile)

# UART (Python ile iletişim için)
UART_ID = 0         # UART0
UART_TX = 0         # GPIO0 (TX)
UART_RX = 1         # GPIO1 (RX)
UART_BAUDRATE = 115200

# TMC2209 UART (İleride kullanılacak - şimdilik devre dışı)
# TMC_UART_ID = 1    # UART1
# TMC_TX = 4         # GPIO4
# TMC_RX = 5         # GPIO5

# ============================================================================
# HIZ VE ZAMANLAMA AYARLARI
# ============================================================================

MIN_STEP_DELAY_US = 50      # Minimum adım gecikmesi (maksimum hız)
MAX_STEP_DELAY_US = 2000    # Maksimum adım gecikmesi (başlangıç hızı)
ACCEL_RATE = 0.05           # Hızlanma/yavaşlama oranı

# ============================================================================
# PIN KURULUMU
# ============================================================================

# Motor pinleri
step_x = Pin(STEP_X_PIN, Pin.OUT)
dir_x = Pin(DIR_X_PIN, Pin.OUT)
ms1_x = Pin(MS1_X_PIN, Pin.OUT)
ms2_x = Pin(MS2_X_PIN, Pin.OUT)

step_y = Pin(STEP_Y_PIN, Pin.OUT)
dir_y = Pin(DIR_Y_PIN, Pin.OUT)
ms1_y = Pin(MS1_Y_PIN, Pin.OUT)
ms2_y = Pin(MS2_Y_PIN, Pin.OUT)

enable = Pin(ENABLE_PIN, Pin.OUT)
laser = Pin(LASER_PIN, Pin.OUT)
emergency_stop = Pin(EMERGENCY_STOP_PIN, Pin.IN, Pin.PULL_UP)

# UART kurulumu (Python ile iletişim)
uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX), rx=Pin(UART_RX))

# ============================================================================
# TMC2209 MANUEL MICROSTEP AYARI
# ============================================================================

def set_microstepping(motor='both', mode='1/8'):
    """
    Mikroadımlama ayarı (MS1, MS2 pinleri ile)
    
    motor: 'x', 'y', veya 'both'
    mode: '1/8', '1/16', '1/32', '1/64'
    
    MS1  MS2  | Mikroadım
    -----|-----|-----------
    LOW  LOW  | 1/8  (önerilen)
    HIGH HIGH | 1/16
    HIGH LOW  | 1/32
    LOW  HIGH | 1/64
    """
    
    modes = {
        '1/8':  (0, 0),
        '1/16': (1, 1),
        '1/32': (1, 0),
        '1/64': (0, 1)
    }
    
    if mode not in modes:
        print(f"HATA: Geçersiz mod {mode}")
        return
    
    ms1_val, ms2_val = modes[mode]
    
    if motor in ('x', 'both'):
        ms1_x.value(ms1_val)
        ms2_x.value(ms2_val)
        print(f"X Motor mikroadım: {mode}")
    
    if motor in ('y', 'both'):
        ms1_y.value(ms1_val)
        ms2_y.value(ms2_val)
        print(f"Y Motor mikroadım: {mode}")

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
        # 0 = dur, pozitif/negatif = yön ve hız
        
        try:
            val_x = int(parts[1])
            val_y = int(parts[2])
            
            # X Motoru
            if val_x == 0:
                with lock:
                    target_delay_x = 0
            else:
                # Yön belirle
                dir_x.value(1 if val_x > 0 else 0)
                
                # Hızı gecikmeye çevir
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
    
    elif cmd.startswith("MICROSTEP") and len(parts) == 3:
        # FORMAT: MICROSTEP,both,1/8
        # İleride mikroadım değiştirmek için
        motor = parts[1]
        mode = parts[2]
        set_microstepping(motor, mode)
        uart.write(f"OK,MICROSTEP_{motor}_{mode}\n")
    
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
    print("=" * 50)
    print("Hava Savunma Sistemi - Pico 2 Motor Kontrolü")
    print("=" * 50)
    
    # Motorları devre dışı bırak
    enable.value(1)  # HIGH = disable
    time.sleep_ms(100)
    
    # Lazeri kapat
    laser.value(0)
    
    # Mikroadımlama ayarı (başlangıç: 1/8)
    set_microstepping('both', '1/8')
    
    # Motorları etkinleştir
    enable.value(0)  # LOW = enable
    time.sleep_ms(100)
    
    print("\n📌 PIN KONFIGÜRASYONU:")
    print(f"  X Motor: STEP={STEP_X_PIN}, DIR={DIR_X_PIN}, MS1={MS1_X_PIN}, MS2={MS2_X_PIN}")
    print(f"  Y Motor: STEP={STEP_Y_PIN}, DIR={DIR_Y_PIN}, MS1={MS1_Y_PIN}, MS2={MS2_Y_PIN}")
    print(f"  Kontrol: ENABLE={ENABLE_PIN}, LASER={LASER_PIN}, E-STOP={EMERGENCY_STOP_PIN}")
    print(f"  UART: TX={UART_TX}, RX={UART_RX}, Baudrate={UART_BAUDRATE}")
    
    print("\n✅ Sistem hazır!")
    uart.write("OK,PICO_READY\n")
    
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
