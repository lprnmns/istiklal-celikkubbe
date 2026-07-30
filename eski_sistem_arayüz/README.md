# TEKNOFEST Hava Savunma Sistemi

## Kurulum
```
cd C:\Users\manas\Desktop\HavaSavunma-Teknofest-main\final
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## YOLO Model
`models/balon_model.pt` yükleyin (dataset: Hava_Savunma.v1i.yolov8).

## Mikrodenetleyici Seçenekleri

### Arduino Uno (Orijinal)
1. `arduino/motor_control/motor_control.ino` yükleyin (AccelStepper lib gerekli).
2. USB bağlayın (COM3 varsayılan).

### Raspberry Pi Pico 2 (Yeni! ⚡)
**Arduino IDE ile:**
1. Arduino IDE 2.x yükle
2. Board support: `https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json`
3. `pico_arduino/motor_control_pico/motor_control_pico.ino` yükle
4. Board: Raspberry Pi Pico 2, Port: COMx
5. Detaylar: [pico_arduino/README.md](pico_arduino/README.md)

**Avantajlar:** 150 MHz CPU, 520 KB RAM, Multi-threading, TMC2209 UART desteği

## Çalıştırma
```
python python/main.py
```

## Kontroller
- **GUI Modlar**: Manuel/Otomatik/Otonom
- **Klavye**: WASD=Move, SPACE=Ateş, E=Dur, M=Mod, H=Home, Q=Çıkış
- **Acil Durdur**: Kırmızı buton

## Özellikler
- 11 yarışma yeteneği
- PID + Kalman takip
- Yasak bölge koruması
- Non-blocking 30 FPS
- Simülasyon modu (no hardware)

## Test
- SIMULATION_MODE=True config.py'de
