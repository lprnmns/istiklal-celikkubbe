# P0 — CommandGateway fiziksel komut sözleşmesi

Tarih: 2026-07-15. Kapsam: donanım yokken mock Pico uçtan uca sözleşmesi ve iki Pico firmware'inin derleme doğrulaması.

## A. Eski fiziksel tetik envanteri

| Konum | Eski komut | Yeni durum |
|---|---|---|
| `backend/app/services/serial_service.py:send_fire_command` | Doğrudan `LZR,1` | Ateş isteği reddedilir; yalnız Gateway ham komut yolunu kullanır. `LZR,0` güvenli bırakmadır. |
| `backend/app/services/tracking_loop.py:_update_fire_zone` | Hedef merkezde ateş adayı | Seri yazmaz; adayı Gateway'e verir. |
| `eski_sistem_arayüz/pico_arduino/motor_control_v2_optimized/motor_control_v2_optimized.ino` | `LZR,1` / `LZR,0` | Korundu; `STAT`, `ARM,1` ve E-Stop denetimi eklendi. |
| `firmware/pico2/main.py:process_command` | `LZR,1` / `LZR,0` | Korundu; `STAT`, `ARM,1` ve E-Stop denetimi eklendi. |

## B–D. Protokol, zincir ve modlar

| Amaç | Pico komutu | Gateway metodu | ACK |
|---|---|---|---|
| Sağlık | `PING`, `STAT` | `run_preflight` | `OK,PONG`, `OK,STAT,...` / JSON karşılığı |
| Tetik arm | `ARM,1` | `select_profile` / `run_preflight` | `OK,ARM_1` / `TRIGGER_ARMED` |
| Hareket | `DRV,1`, `SPD,x,y` | `send_motion` | driver ACK, SPD yazımı |
| Ateş | `LZR,1` | `fire_from_tracking` | `OK,LASER_1` / `FIRE_SERVO_PULLED` |
| Kesme | `LZR,0`, `STP`, `DRV,0` | `tick` / `gateway_safe_stop` | ilgili ACK |

Çağrı zinciri: `VisionPipeline → TrackingLoop._update_fire_zone → CommandGateway.fire_from_tracking → SerialService.gateway_exchange("LZR,1") → USB serial → Pico firmware → ACK`.

| Profil | Hareket | Ateş |
|---|---|---|
| `DRY_RUN` | Hayır | Hayır |
| `LIVE_TEST` | Preflight hazırsa | Preflight, arm ve taze balon algısı ile |
| `COMPETITION` | Preflight hazırsa | Preflight, arm ve `DecisionEngine.FIRE_READY` ile |

## E–J. Otomatik kanıtlar

`backend/tests/test_phase63_command_gateway_contract.py` aşağıdakileri kapsar:

| Kanıt | Test |
|---|---|
| E ARM → FIRE → ACK | `test_mock_pico_arm_fire_ack_contract` |
| F E-Stop reddi/kesilmesi | `test_estop_rejects_fire_and_safes_outputs` |
| G bağlantı kaybı NO_FIRE | `test_connection_loss_produces_no_fire` |
| H stale kamera ve recovery | `test_stale_camera_blocks_then_repreflight_recovers` |
| I LIVE_TEST hareket | `test_live_test_motion_reaches_gateway_pico_contract` |
| J arayüz/API ile profils seçimi | `test_profile_is_selectable_over_api_without_config_change` |
| Heartbeat kaybında safing | `test_heartbeat_loss_safes_motion_and_requires_new_preflight` |

Son doğrulama:

```text
arduino-cli compile --fqbn rp2040:rp2040:rpipico eski_sistem_arayüz/pico_arduino/motor_control_v2_optimized
Sketch uses 68448 bytes (3%) of program storage space.
Global variables use 10112 bytes (3%) of dynamic memory.

backend/.venv/bin/python -m py_compile firmware/pico2/main.py
passed

backend/.venv/bin/python -m pytest -q backend/tests/test_phase62_fail_closed_tracking.py backend/tests/test_phase63_command_gateway_contract.py backend/tests/test_phase64_gateway_boundary.py
18 passed

npm --prefix frontend run typecheck
passed
```

`SafetyModeBanner.vue` görünür profil seçimi, Pico portu/baud ile `PICO BAĞLA`, arm, preflight ve makinece okunur reason code sunar. Kaynak kodu, environment veya gizli flag düzenlemesi gerekmez.

`HIL_PICO_TARET_KABUL_TESTI.md`, Pico/taret geri geldiğinde uygulanacak HIL-01…05 adımlarını ve her run için zorunlu kanıt alanlarını saklar.

## UI reason code'ları

`PICO_HANDSHAKE_FAILED`, `ESTOP_STATE_UNKNOWN`, `ESTOP_ACTIVE`, `CAMERA_STALE`, `MOTION_FAULT_OR_ESTOP`, `ACTUATOR_NOT_ARMED`, `ACTUATOR_ARM_FAILED`, `PREFLIGHT_NOT_READY`, `PICO_CONNECTION_FAULT`, `PICO_HEARTBEAT_STALE`, `LIVE_PROFILE_NOT_ACTIVE`, `LIVE_TEST_BALLOON_NOT_DETECTED`, `DECISION_NOT_FIRE_READY`, `PICO_DRIVER_ENABLE_FAILED`, `PICO_MOTION_WRITE_FAILED`, `PICO_FIRE_REJECTED`, `MOTION_SPEED_LIMIT`, `PAN_LEFT_LIMIT_ACTIVE`, `PAN_RIGHT_LIMIT_ACTIVE`, `TILT_UP_LIMIT_ACTIVE`, `TILT_DOWN_LIMIT_ACTIVE`, `PAN_SOFT_LIMIT`, `TILT_SOFT_LIMIT`.
