# Faz 3 Pico 2 Arayuzu ve Pin Validasyonu

## Amac

Faz 3, Pico 2 donanim arayuzunu mock/dry-run guvenlik modeli icinde gorunur ve dogrulanabilir hale getirir.

Bu fazda:

- Gercek serial port acmak zorunlu degildir.
- Mock Pico default kalir.
- Motor, servo veya fire komutu uretilmez.
- Pin profili backend memory state uzerinde guncellenir.
- Placeholder pin profili final/onayli kablolama olarak kabul edilmez.

## Endpoint Listesi

```http
GET  /api/pico/status
GET  /api/pico/ports
POST /api/pico/connect
POST /api/pico/disconnect
GET  /api/pico/pins
PUT  /api/pico/pins
POST /api/pico/pins/validate
```

## WebSocket Eventleri

```text
pico.telemetry
pico.connection
pico.pin_validation
```

`pico.telemetry` backend mock Pico servisinden gelir. UI bu eventleri system store icinde takip eder.

## Pin Assignment Modeli

Her pin:

```json
{
  "pin_name": "GP10",
  "physical_pin": 14,
  "function": "TRIGGER_SERVO_PWM",
  "direction": "OUT",
  "mode": "PWM",
  "pwm_capable": true,
  "uart_capable": false,
  "note": null
}
```

Desteklenen gorevler:

- `PAN_STEP`
- `PAN_DIR`
- `TILT_STEP`
- `TILT_DIR`
- `TRIGGER_SERVO_PWM`
- `ESTOP_IN`
- `LIMIT_LEFT`
- `LIMIT_RIGHT`
- `LIMIT_UP`
- `LIMIT_DOWN`
- `DRIVER_ENABLE`
- `UART_TX`
- `UART_RX`
- `UNUSED`

## Validation Kurallari

- Ayni kritik gorev iki pine atanamaz.
- `ESTOP_IN` input olmalidir.
- Limit switch gorevleri input olmalidir.
- STEP/DIR gorevleri output olmalidir.
- `TRIGGER_SERVO_PWM` PWM-capable output pin olmalidir.
- `UART_TX` ve `UART_RX` ayni pin olamaz.
- `PAN_STEP`, `PAN_DIR`, `TILT_STEP`, `TILT_DIR` eksikse validation error uretir.
- `ESTOP_IN` eksikse critical error uretir.
- Sistem `DISARMED` degilse pin update uygulanmaz.
- Sistem armed ise pin update reddedilir.

## Frontend Kullanim Akisi

1. Pico sayfasi acilir.
2. UI `/api/pico/status`, `/api/pico/ports`, `/api/pico/pins` verilerini ceker.
3. Pico karti uzerindeki pin tiklanir.
4. Pin detail panelinde gorev dropdown ile preview olarak degistirilir.
5. `Validate Preview` backend validation endpointini cagirir.
6. `Apply / Save` backend `PUT /api/pico/pins` endpointini cagirir.
7. Backend validation basariliyse profil memory state'e uygulanir.

## Guvenlik Notlari

- UI safety otoritesi degildir.
- Pin degisikligi sadece backend `DISARMED` durumunda uygulanir.
- Bu fazda config dosyasina otomatik yazma yapilmadi; yanlis pin profilini kalici hale getirme riski azaltildi.
- Gercek donanim hareketi, motor komutu, servo tetigi veya fire komutu yoktur.
- `config/pin_profiles/pico2_placeholder.yaml` final/onayli pinout degildir.
