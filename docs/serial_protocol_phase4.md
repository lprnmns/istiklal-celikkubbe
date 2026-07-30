# Faz 4 Serial Protocol ve Serial Monitor

## JSON-line Dev Protocol

Gelistirme protokolu newline ile biten JSON mesajlarindan olusur.

PC -> Pico safe mesajlari:

```json
{"type":"heartbeat","seq":1,"timestamp_ms":123456}
{"type":"disarm","seq":2,"reason":"operator_request"}
{"type":"self_test","seq":3,"test":"pico_status"}
{"type":"set_mode","seq":4,"mode":"standby"}
```

Pico -> PC mesajlari:

```json
{"type":"ack","seq":2,"accepted":true}
{"type":"nack","seq":2,"reason":"ESTOP_ACTIVE"}
{"type":"heartbeat","seq":10,"timestamp_ms":123456}
{"type":"error","seq":11,"code":"MOCK_ERROR","message":"example"}
```

Telemetry:

```json
{
  "type": "telemetry",
  "seq": 10,
  "estop_state": false,
  "driver_enabled": false,
  "pan_position_steps": 0,
  "tilt_position_steps": 0,
  "last_error": null
}
```

## Binary Packet Format

Binary protokol bu fazda yalnizca testlenebilir encode/decode katmani olarak eklendi.

```text
START   TYPE   SEQ   LEN   PAYLOAD   CRC16   END
0xAA    1B     1B    1B    N byte    2B      0x55
```

Kurallar:

- START `0xAA` olmalidir.
- END `0x55` olmalidir.
- LEN payload uzunlugudur.
- CRC16, `TYPE + SEQ + LEN + PAYLOAD` uzerinden hesaplanir.
- CRC hatasi controlled decode error uretir.
- LEN uyusmazligi controlled decode error uretir.
- Bilinmeyen TYPE controlled decode error uretir.

## CRC16 Secimi

Secilen algoritma: **CRC16/XMODEM**

- Polynomial: `0x1021`
- Init: `0x0000`
- RefIn/RefOut: false
- XorOut: `0x0000`

Test vektoru:

```text
"123456789" -> 0x31C3
```

## ACK / NACK Akisi

SerialService:

- seq counter tutar.
- ACK bekleyen komutlari pending map icinde saklar.
- `ack` mesajinda pending komutu temizler.
- `nack` mesajinda pending komutu temizler ve `last_error` gunceller.
- `heartbeat` RX mesajinda heartbeat zamanini gunceller.

## Timeout / Fault Mantigi

- ACK timeout: `ack_timeout_ms` asilirsa pending komut fault olarak loglanir.
- Heartbeat timeout: `heartbeat_timeout_ms` asilirsa connection state `FAULT` olur.
- Timeout durumlari JSONL log ve WebSocket event olarak akar.

WebSocket eventleri:

- `serial.tx`
- `serial.rx`
- `serial.ack`
- `serial.nack`
- `serial.timeout`
- `serial.error`
- `serial.status`

## Serial Monitor Kullanim

Frontend Serial sayfasi:

- connection status
- transport mode
- protocol mode
- last tx/rx
- pending ack count
- heartbeat age
- safe message sender
- simulate rx panel
- serial log table

Renkler:

- tx: mavi/gri
- rx/ack: yesil
- nack/error: kirmizi
- timeout: sari

## Guvenlik Notlari

- `hardware_enabled=false` iken real serial transport devre disidir.
- `serial.real_serial_enabled=false` validation ile korunur.
- Bu fazda transport `mock` disinda acilamaz.
- Fire/motor/servo gibi riskli mesajlar schema seviyesinde taninsa bile `/api/serial/send-json` tarafindan reddedilir.
- DISARM safe command olarak kabul edilir fakat sadece mock transport uzerinden yurutulur.
- Gercek Pico seri portu acilmaz, fiziksel donanim komutu uretilmez.

## Bu Fazda Bilincli Disabled Komutlar

- `fire_request`
- `jog_motor`
- `set_motor_target`
- `set_servo_position`
- `set_servo`

Bu komutlar Faz 7 motor/taret ve ileride hardware safety gate tamamlanmadan gercek transport'a gonderilmemelidir.
