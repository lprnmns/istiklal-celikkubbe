# Pico Telemetry-Only Firmware

## Amaç

Faz 12.2 firmware'i gerçek Pico 2 ile read-only acceptance testini doğrulamak içindir. Bu firmware gerçek motor firmware'i değildir.

## Güvenlik Sınırı

- Motor hareketi yok.
- Servo/tetik yok.
- Atış yok.
- STEP/DIR/PWM output yok.
- GPIO output yok.
- Driver enable yok.
- PC'den gelen komutlar işlenmez.
- Sadece USB serial üzerinden JSON-line telemetry yayınlanır.

## Yükleme Adımları

1. Pico 2 için MicroPython UF2 dosyasını yükle.
2. Pico 2'yi BOOTSEL ile bağlayıp UF2 dosyasını kopyala.
3. `firmware/pico2_telemetry_only/main.py` dosyasını Thonny veya `mpremote` ile Pico'ya `main.py` olarak kopyala.
4. Linux port kontrolü:

```bash
python -m serial.tools.list_ports
```

5. Backend config'te read-only discovery için `hardware.allow_real_serial_readonly=true` ve `serial.transport_mode=real_readonly` test config'iyle çalıştır.
6. UI'da Pico > Real Hardware Discovery ekranından portu seç ve Connect Read-Only yap.

## Telemetry JSON Formatı

```json
{
  "type": "telemetry",
  "seq": 1,
  "device": "pico2",
  "firmware_version": "telemetry-only-0.1",
  "estop_state": false,
  "driver_enabled": false,
  "pan_position_steps": 0,
  "tilt_position_steps": 0,
  "limits": {
    "pan_left": false,
    "pan_right": false,
    "tilt_up": false,
    "tilt_down": false
  },
  "safe_state": true,
  "physical_outputs_enabled": false,
  "timestamp_ms": 123456
}
```

## Backend Parser Beklentisi

Backend şu alanları okur:

- `firmware_version`
- `safe_state`
- `physical_outputs_enabled`
- `timestamp_ms`
- `limits`
- `estop_state`
- `driver_enabled`
- `pan_position_steps`
- `tilt_position_steps`

Eksik alanlar backend'i çökertmez; state warning olarak görünür. `device=pico2`, `firmware_version=telemetry-only-*` ve `physical_outputs_enabled=false` birlikte gelirse Pico verified sayılır.

## Kabul Testi

1. Pico USB ile bağlanır.
2. `/api/hardware/serial/ports` Pico adayını göstermelidir.
3. Connect Read-Only ile port açılır.
4. `PICO_READONLY_VERIFIED` state'i görülmelidir.
5. `physical_outputs_enabled=false` görülmelidir.
6. Riskli komut blocker testleri reddedilmelidir.
7. Self-test hardware step'lerinde critical failure olmamalıdır.

## Sık Hatalar

- Port permission: kullanıcı `dialout` grubunda olmayabilir.
- Wrong baudrate: MicroPython USB CDC için baudrate genellikle etkisizdir ama UI 115200 kullanır.
- No telemetry: `main.py` Pico'ya kopyalanmamış veya board resetlenmemiş olabilir.
- Device not candidate: Port description Pico yazmayabilir; dikkatli read-only seçime izin verilir.
- Serial busy: Thonny, mpremote veya başka terminal portu açık tutuyor olabilir.
