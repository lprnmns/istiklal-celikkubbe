import time
from config import SerialConfig
from serial_comm import SerialComm

"""
Basit Motor Hız Testi
- Amaç: Pico motor sürücüsünün maksimum hız ve tepki davranışını hızlıca doğrulamak
- Kullanım: python motor_speed_test.py
"""

def ramp_test(serial: SerialComm, max_speed: int = 1000, step: int = 100, dwell: float = 0.3):
    print(f"RAMP TEST: 0 -> {max_speed} -> 0 / step={step}")
    # X eksenini ileri/geri hız rampası
    for s in range(0, max_speed + step, step):
        serial.set_speed(s, 0)
        time.sleep(dwell)
    for s in range(max_speed, -step, -step):
        serial.set_speed(s, 0)
        time.sleep(dwell)
    # Y ekseni
    for s in range(0, max_speed + step, step):
        serial.set_speed(0, s)
        time.sleep(dwell)
    for s in range(max_speed, -step, -step):
        serial.set_speed(0, s)
        time.sleep(dwell)


def step_response(serial: SerialComm, speed: int = 1000, repeats: int = 10, dwell: float = 0.2):
    print(f"STEP RESPONSE: +/-{speed} x{repeats}")
    for _ in range(repeats):
        serial.set_speed(speed, speed)
        time.sleep(dwell)
        serial.set_speed(-speed, -speed)
        time.sleep(dwell)
        serial.set_speed(0, 0)
        time.sleep(dwell)


def main():
    cfg = SerialConfig()
    ser = SerialComm(cfg)
    if not ser.connect():
        print("Serial bağlanamadı; lütfen Pico port ve kabloyu kontrol edin.")
        return
    try:
        # Maksimum ölçeği dene
        step_response(ser, speed=1000, repeats=6, dwell=0.15)
        ramp_test(ser, max_speed=1000, step=200, dwell=0.15)
        # İnce ayar: orta hızda daha kısa dwell
        step_response(ser, speed=700, repeats=6, dwell=0.10)
    finally:
        # Güvenli durdur
        ser.emergency_stop()
        ser.disconnect()
        print("Test bitti, serial kapatıldı.")

if __name__ == "__main__":
    main()
