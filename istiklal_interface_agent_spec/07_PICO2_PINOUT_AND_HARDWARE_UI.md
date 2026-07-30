# 7. Pico 2 Pinout ve Donanım UI

## Amaç

Pico 2 ekranı sistemin elektronik arayüzlerini görsel ve doğrulanabilir hale getirmelidir. Kullanıcı hangi pinin hangi göreve atandığını, canlı pin durumunu ve hatalı atamaları görebilmelidir.

## Pin Görev Enum'u

```text
UNUSED
PAN_STEP
PAN_DIR
TILT_STEP
TILT_DIR
DRIVER_ENABLE
PAN_LIMIT_LEFT
PAN_LIMIT_RIGHT
TILT_LIMIT_UP
TILT_LIMIT_DOWN
ESTOP_IN
TRIGGER_SERVO_PWM
UART_TX
UART_RX
I2C_SDA
I2C_SCL
SPI_MOSI
SPI_MISO
SPI_SCK
DEBUG_LED
BUZZER
AUX_INPUT
AUX_OUTPUT
```

## Validasyon Kuralları

- Aynı pin iki aktif göreve atanamaz.
- GND/3V3/VSYS pinlerine görev atanamaz.
- UART TX/RX aynı pin olamaz.
- STEP/DIR output olmalıdır.
- Limit switch ve E-stop input olmalıdır.
- Servo görevi PWM destekli pine atanmalıdır.
- Pin değişiklikleri sadece `DISARMED` durumda uygulanır.
- `ESTOP_IN` yoksa sistem `ARMED` olamaz.
- `TRIGGER_SERVO_PWM` yoksa fire request kabul edilmez.

## UI Pin Kartı

```json
{
  "pin_name": "GP10",
  "physical_pin": 14,
  "function": "TRIGGER_SERVO_PWM",
  "mode": "PWM",
  "direction": "OUT",
  "current_value": "1500us",
  "valid": true,
  "last_update": "14:22:11.410"
}
```

## Renk Kodları

- gri: unused
- yeşil: input
- mavi: output
- turuncu: PWM
- mor: communication
- kırmızı: conflict/error
- sarı: warning

## Component Önerileri

```text
PicoPinoutView.vue
PicoBoardSvg.vue
PicoPin.vue
PinDetailDrawer.vue
PinAssignmentForm.vue
PinValidationPanel.vue
```

## Validasyon Mesajları

### Pin çakışması

```json
{
  "level": "error",
  "code": "PIN_CONFLICT",
  "message": "GP2 is assigned to both PAN_STEP and TILT_STEP."
}
```

### Uygun olmayan pin

```json
{
  "level": "error",
  "code": "PIN_CAPABILITY_MISMATCH",
  "message": "TRIGGER_SERVO_PWM requires PWM-capable pin."
}
```

### Kritik pin eksik

```json
{
  "level": "warning",
  "code": "MISSING_ESTOP",
  "message": "ESTOP_IN is not assigned. System cannot be armed."
}
```

## Canlı Telemetry

```json
{
  "pins": {
    "GP2": {"value": 0, "mode": "OUT"},
    "GP3": {"value": 1, "mode": "OUT"},
    "GP14": {"value": 1, "mode": "IN", "function": "ESTOP_IN"}
  }
}
```

## Test Butonları

- Blink debug LED
- Read all inputs
- Toggle driver enable
- Servo dry-run
- Pan step pulse test
- Tilt step pulse test
- E-stop read test
- Limit switch read test

Hareket doğuran tüm testlerde:

```text
System mode = DISARMED
Fire lock = CLOSED
Operator confirmation = TRUE
```

## Config Örneği

```yaml
pins:
  pan_step: GP2
  pan_dir: GP3
  tilt_step: GP4
  tilt_dir: GP5
  driver_enable: GP6
  trigger_servo_pwm: GP10
  estop_in: GP14
  pan_limit_left: GP16
  pan_limit_right: GP17
  tilt_limit_up: GP18
  tilt_limit_down: GP19
```
