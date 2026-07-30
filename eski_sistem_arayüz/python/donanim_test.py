import serial
import serial.tools.list_ports
import time
import sys

# Yapılandırma (Raspberry Pi Pico 2)
# Mikrodenetleyici: Pico 2 (Arduino IDE)
# Baud Rate: 460800 (motor_control_v2_optimized.ino ile eşleşir)
# Microstepping: CNC Shield jumper'larıyla ayarlanır (1/8 önerilen)
BAUDRATE = 460800

def list_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def connect_pico():
    """Raspberry Pi Pico 2 portuna bağlan"""
    ports = list_ports()
    if not ports:
        print("❌ Hiçbir COM portu bulunamadı! Pico 2 takılı mı?")
        return None
    
    print("Bulunan Portlar:")
    for i, p in enumerate(ports):
        print(f"{i+1}: {p}")
    
    if len(ports) == 1:
        port = ports[0]
        print(f"🔌 Otomatik olarak {port} seçiliyor...")
    else:
        selection = input("Hangi portu kullanmak istersiniz? (Numara girin): ")
        try:
            port = ports[int(selection)-1]
        except:
            print("Geçersiz seçim.")
            return None

    try:
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = BAUDRATE
        ser.timeout = 1
        ser.dtr = True # Bağlantı uyanması için
        ser.rts = True
        ser.open()
        time.sleep(2) # Pico 2 reset için bekle
        print(f"✅ {port} portuna bağlanıldı (Pico 2)")
        
        print("Pico'dan sistem durumu bekleniyor...")
        while ser.in_waiting:
            print("   >", ser.readline().decode('utf-8', errors='ignore').strip())
            
        return ser
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return None

# Geriye uyumluluk
connect_arduino = connect_pico

def send_command(ser, cmd):
    """Pico 2'ye komut gönder"""
    print(f"📤 Gönderiliyor: {cmd}")
    ser.write(f"{cmd}\n".encode('utf-8'))
    time.sleep(0.1)
    # Cevap bekle (Pico 2'den OK gelmesi lazım)
    start = time.time()
    while time.time() - start < 1.0:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"📥 Pico 2: {line}")
                return True
    return False

def ask_user(question):
    while True:
        response = input(f"\n❓ {question} (e/h): ").lower().strip()
        if response == 'e':
            return True
        elif response == 'h':
            return False
        else:
            print("Lütfen 'e' (evet) veya 'h' (hayır) girin.")

def main():
    print("=== Hava Savunma Sistemi Donanım Testi ===")
    print("Mikrodenetleyici: Raspberry Pi Pico 2 (Arduino IDE)")
    print("UYARI: Motorların serbestçe dönebildiğinden emin olun.")
    
    ser = connect_pico()
    if not ser:
        return

    try:
        # --- TEST 1: X Ekseni Hareketi ---
        print("\n--- TEST 1: X Ekseni Step Motor ---")
        print("X motoru + yönde dönecek...")
        send_command(ser, "SPD,500,0")
        time.sleep(2)
        send_command(ser, "SPD,0,0") # Durdur
        
        if ask_user("X motoru hareket etti mi?"):
            print("✅ X Ekseni Step Pinleri (0, 1) Doğru.")
        else:
            print("❌ X Ekseni bağlantılarını kontrol edin: STEP=1, DIR=0, ENABLE=6")
            print("   - Sürücüye güç gidiyor mu (12V/24V)?")
            print("   - Sürücü akım ayarı yapıldı mı?")

        # --- TEST 2: X Ekseni Yön ---
        print("\n--- TEST 2: X Ekseni Yönü ---")
        print("X motoru - (ters) yönde dönecek...")
        send_command(ser, "SPD,-500,0")
        time.sleep(2)
        send_command(ser, "SPD,0,0")
        
        if ask_user("Motor ters yöne döndü mü?"):
            print("✅ X Ekseni Yön Pini Doğru.")
        else:
            print("❌ X Yön pini veya bobin bağlantıları ters olabilir.")

        # --- TEST 3: Y Ekseni Hareketi ---
        print("\n--- TEST 3: Y Ekseni Step Motor ---")
        print("Y motoru + yönde dönecek...")
        send_command(ser, "SPD,0,500")
        time.sleep(2)
        send_command(ser, "SPD,0,0")
        
        if ask_user("Y motoru hareket etti mi?"):
            print("✅ Y Ekseni Step Pinleri (8, 9) Doğru.")
        else:
            print("❌ Y Ekseni bağlantılarını kontrol edin: STEP=9, DIR=8, ENABLE=14")

        # --- TEST 4: Lazer Kontrolü ---
        print("\n--- TEST 4: Lazer ---")
        print("Lazer AÇILIYOR (DİKKAT!)...")
        send_command(ser, "LZR,1")
        time.sleep(2)
        print("Lazer KAPANIYOR...")
        send_command(ser, "LZR,0")
        
        if ask_user("Servo Tetik Çekildi mi?"):
            print("✅ Servo Tetik Pini (15) Doğru.")
        else:
            print("❌ Servo bağlantısını kontrol edin: PIN=15. Güç kaynağını kontrol edin.")

    except KeyboardInterrupt:
        print("\nTest kullanıcı tarafından iptal edildi.")
    finally:
        print("\nTest tamamlandı. Motorlar durduruluyor...")
        send_command(ser, "SPD,0,0")
        send_command(ser, "LZR,0")
        ser.close()
        print("Bağlantı kesildi.")

if __name__ == "__main__":
    main()
