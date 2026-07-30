# 8. Serial Protokol

## Amaç

Laptop backend ile Pico 2 arasında düşük gecikmeli, güvenilir ve doğrulanabilir haberleşme kurmak.

## Protokol Aşamaları

### Geliştirme

JSON-line:

```json
{"type":"set_motor_target","pan":1200,"tilt":-300,"seq":42}
```

### Final

Binary paket:

```text
START | TYPE | SEQ | LEN | PAYLOAD | CRC16 | END
0xAA  | 1B   | 1B  | 1B  | N byte  | 2B    | 0x55
```

## Komut Tipleri

| Type | Hex | Yön | Açıklama |
|---|---:|---|---|
| HEARTBEAT | 0x01 | PC↔Pico | Bağlantı kontrolü |
| SET_MODE | 0x02 | PC→Pico | Çalışma modu |
| SET_MOTOR_TARGET | 0x03 | PC→Pico | Pan/tilt hedef |
| JOG_MOTOR | 0x04 | PC→Pico | Küçük hareket |
| STOP_MOTION | 0x05 | PC→Pico | Hareket durdur |
| SET_SERVO_POSITION | 0x06 | PC→Pico | Servo pozisyon |
| FIRE_REQUEST | 0x07 | PC→Pico | Ateşleme isteği |
| DISARM | 0x08 | PC→Pico | Güvenli moda geç |
| CONFIG_UPDATE | 0x09 | PC→Pico | Ayar güncelle |
| SELF_TEST | 0x0A | PC→Pico | Test komutu |
| TELEMETRY | 0x81 | Pico→PC | Canlı durum |
| ACK | 0x82 | Pico→PC | Onay |
| NACK | 0x83 | Pico→PC | Red |
| ERROR | 0x84 | Pico→PC | Hata |

## Motor Payload

```c
struct MotorTargetPayload {
  int32_t pan_steps;
  int32_t tilt_steps;
  uint16_t max_speed;
  uint16_t accel;
  uint8_t flags;
};
```

## Telemetry Payload

```c
struct TelemetryPayload {
  uint8_t pico_state;
  int32_t pan_steps;
  int32_t tilt_steps;
  uint8_t estop;
  uint8_t limits;
  uint8_t driver_enabled;
  uint8_t trigger_ready;
  uint16_t error_code;
  uint16_t loop_time_us;
};
```

## ACK/NACK

```json
{
  "type": "ACK",
  "seq": 42,
  "command_type": "SET_MOTOR_TARGET"
}
```

```json
{
  "type": "NACK",
  "seq": 42,
  "reason": "ESTOP_ACTIVE"
}
```

## Watchdog

- PC, Pico heartbeat alamazsa `PICO_TIMEOUT`.
- Backend komut göndermeyi durdurur.
- Pico, PC komutlarını alamazsa safe-state'e geçer.
- Safe-state:
  - Driver disable
  - Servo neutral
  - Motion stop

## Hata Kodları

```text
0x0000 OK
0x0001 CRC_ERROR
0x0002 BAD_PACKET
0x0003 ESTOP_ACTIVE
0x0004 LIMIT_REACHED
0x0005 DRIVER_FAULT
0x0006 INVALID_MODE
0x0007 FIRE_LOCKED
0x0008 WATCHDOG_TIMEOUT
0x0009 PIN_CONFIG_INVALID
```
