# 06 — Donanım Entegrasyonu, Firmware ve Test Altyapısı

> Pico2 firmware, seri protokol detayları, test yazma rehberi.

---

## 1. Firmware — Pico 2 Telemetry Only

**Dosya:** `firmware/pico2_telemetry_only/main.py` (61 satır)

**Güvenlik sınırı:** Bu firmware **hiçbir GPIO çıkışı üretmez.** Sadece USB serial üzerinden JSON telemetri yayınlar.

### Çalışma mantığı
```python
TELEMETRY_HZ = 2  # Saniyede 2 telemetri paketi

def main():
    seq = 1
    while True:
        print(json.dumps(telemetry(seq)))  # USB serial'e JSON yaz
        seq = (seq + 1) % 256
        time.sleep(0.5)
```

### Telemetri paketi
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
    "pan_left": false, "pan_right": false,
    "tilt_up": false, "tilt_down": false
  },
  "safe_state": true,
  "physical_outputs_enabled": false,
  "timestamp_ms": 123456789
}
```

### Üretim firmware'ı (firmware/pico2/)
**BOŞ — henüz yazılmadı.** Üretim firmware'ı şunları yapacak:
- STEP/DIR sinyal üretimi (TMC2209 sürücüye)
- Servo PWM (tetik mekanizması)
- E-stop input okuma
- Limit switch input okuma
- Driver enable/disable
- Watchdog timer
- JSON-line serial komut parse
- Kendi local safe-state mantığı

---

## 2. Eski Sistem Firmware Referansı

**Dosya:** `eski_sistem_arayüz/pico/motor_control_pico.py` (12.6KB)

Bu dosya **referans olarak** tutuluyor. İçeriği:
- TMC2209 step motor kontrolü
- Servo PWM ile tetik mekanizması
- Limit switch okuma
- E-stop desteği
- JSON-line seri komut alımı

**TMC UART versiyonu:** `motor_control_pico_v2_tmc_uart.py` (15.7KB) — TMC2209 UART modu ile gelişmiş motor kontrolü.

---

## 3. Seri Protokol Detayları

### 3.1 JSON-Line Protokolü

**Format:** Her mesaj tek satır JSON + `\n`

**PC → Pico (TX) mesajları:**

| Tip | Alanlar | Güvenlik |
|-----|---------|----------|
| `heartbeat` | seq, timestamp_ms | ✅ Güvenli |
| `disarm` | seq, reason | ✅ Güvenli |
| `self_test` | seq, test | ✅ Güvenli |
| `set_mode` | seq, mode | ✅ Güvenli |
| `fire_request` | seq, reason | ❌ Riskli (ENGELLİ) |
| `jog_motor` | seq, reason | ❌ Riskli (ENGELLİ) |
| `set_servo_position` | seq, reason | ❌ Riskli (ENGELLİ) |

**Pico → PC (RX) mesajları:**

| Tip | Alanlar | Açıklama |
|-----|---------|----------|
| `ack` | seq, accepted | Komut kabul edildi |
| `nack` | seq, reason | Komut reddedildi |
| `telemetry` | seq, estop_state, driver_enabled, pan/tilt_steps | Durum |
| `error` | seq, code, message | Hata |
| `heartbeat` | seq, timestamp_ms | Yaşam işareti |

### 3.2 Binary Protokolü

```
[0xAA] [TYPE:1byte] [SEQ:1byte] [LEN:1byte] [PAYLOAD:LEN] [CRC16:2byte] [0x55]
```

**Binary mesaj tipleri:**
| Hex | Tip | Yön |
|-----|-----|-----|
| 0x01 | HEARTBEAT | TX |
| 0x02 | SET_MODE | TX |
| 0x03 | SET_MOTOR_TARGET | TX |
| 0x04 | JOG_MOTOR | TX |
| 0x05 | STOP_MOTION | TX |
| 0x06 | SET_SERVO_POSITION | TX |
| 0x07 | FIRE_REQUEST | TX |
| 0x08 | DISARM | TX |
| 0x09 | CONFIG_UPDATE | TX |
| 0x0A | SELF_TEST | TX |
| 0x81 | TELEMETRY | RX |
| 0x82 | ACK | RX |
| 0x83 | NACK | RX |
| 0x84 | ERROR | RX |

**CRC16/XMODEM:** `crc16_xmodem(data) → int`, poly=0x1021, init=0x0000.

### 3.3 Transport Katmanı

3 transport implementasyonu:

| Transport | Kullanım | Açıklama |
|-----------|----------|----------|
| `MockSerialTransport` | Geliştirme | Bellekte buffer, gerçek port yok |
| `PySerialTransport` | Read-only | Gerçek serial.Serial, RX only |
| `AbstractSerialTransport` | Base class | Protocol tanımı |

---

## 4. GPIO Pin Haritası (Pico 2)

```
GP0  (Pin 1)  ─ UART TX capable
GP1  (Pin 2)  ─ UART RX capable
GP2  (Pin 4)  ─ PAN_STEP (varsayılan)
GP3  (Pin 5)  ─ PAN_DIR (varsayılan)
GP4  (Pin 6)  ─ TILT_STEP (varsayılan)
GP5  (Pin 7)  ─ TILT_DIR (varsayılan)
GP6  (Pin 9)  ─ TRIGGER_SERVO_PWM (varsayılan)
GP7  (Pin 10) ─ ESTOP_IN (varsayılan)
GP8  (Pin 11) ─ LIMIT_LEFT (varsayılan)
GP9  (Pin 12) ─ LIMIT_RIGHT (varsayılan)
GP10 (Pin 14) ─ LIMIT_UP (varsayılan)
GP11 (Pin 15) ─ LIMIT_DOWN (varsayılan)
GP12 (Pin 16) ─ DRIVER_ENABLE (varsayılan)
GP13-GP22    ─ Kullanılabilir
GP26-GP28    ─ ADC capable
```

---

## 5. Test Altyapısı

### 5.1 Yapılandırma
```ini
# pytest.ini
testpaths = backend/tests
pythonpath = backend
```

### 5.2 conftest.py (44 satır)

**`client` fixture:** Geçici dizinlerde izole test ortamı oluşturur.
```python
@pytest.fixture
def client(tmp_path):
    config = yaml.safe_load(DEFAULT_CONFIG)
    config["models"]["root_dir"] = str(tmp_path / "models")
    config["dataset"]["root_dir"] = str(tmp_path / "data")
    config["reports"]["root_dir"] = str(tmp_path / "exports/reports")
    config_path = tmp_path / "config.yaml"
    yaml.safe_dump(config, config_path)
    app = create_app(config_path=config_path, log_dir=tmp_path / "logs")
    return TestClient(app)
```

**`config_data` fixture:** Ham YAML dict döner (schema test etmek için).

### 5.3 Test Dosyaları (34 adet)

| Test Dosyası | Ne Test Eder |
|--------------|--------------|
| `test_health.py` | `/health` endpoint çalışıyor mu |
| `test_config.py` | Config yükleme ve validator kontrolü |
| `test_safety.py` | Arm/disarm/fire request |
| `test_decision.py` | 17 güvenlik kapısı |
| `test_vision.py` | Vision start/stop/snapshot |
| `test_pico.py` | Pico connect/disconnect/pins |
| `test_serial.py` | Serial send/status |
| `test_motion.py` | Jog/goto/home/scan |
| `test_calibration.py` | Kalibrasyon güncelleme |
| `test_color.py` | Renk sınıflandırma |
| `test_models.py` | Model registry |
| `test_dataset.py` | Dataset oluşturma |
| `test_data_lab.py` | DataLab session/replay |
| `test_demo_timeline.py` | Demo timeline |
| `test_self_test.py` | Self-test çalıştırma |
| `test_hardware.py` | Donanım keşfi |
| `test_release.py` | Release paket doğrulama |
| `test_jury_package.py` | Jüri paketi |
| `test_model_handoff.py` | Model handoff pipeline |
| `test_live_camera_surrogate.py` | OpenCV daire algılama |
| `test_data_lab_replay_annotation.py` | Replay ve annotation |
| `test_cleanroom_rehearsal.py` | Cleanroom senaryosu |
| `test_legacy_perception.py` | Eski sistem migration |
| `test_direction_semantics.py` | Yön kalibrasyonu |
| `test_pico_readonly.py` | Pico read-only |
| `test_pico_real_rxonly.py` | Gerçek Pico RX-only |
| `test_camera_host.py` | Kamera host tanılama |
| ve diğerleri... | |

### 5.4 Test Yazma Rehberi

```python
# Yeni test dosyası: backend/tests/test_yeni_modul.py
from fastapi.testclient import TestClient

def test_yeni_modul_status(client: TestClient):
    """GET /api/yeni-modul/status 200 dönmeli."""
    response = client.get("/api/yeni-modul/status")
    assert response.status_code == 200
    data = response.json()
    assert "durum" in data

def test_yeni_modul_config_validation(config_data):
    """Config validator yanlış değer için hata fırlatmalı."""
    from app.schemas.config import AppConfig
    import pytest
    config_data["yeni_modul"]["tehlikeli_ayar"] = True
    with pytest.raises(ValueError):
        AppConfig.model_validate(config_data)
```

### 5.5 Testleri Çalıştırma
```bash
cd backend
uv run pytest                      # Tüm testler
uv run pytest tests/test_safety.py # Tek dosya
uv run pytest -v                   # Detaylı çıktı
uv run pytest -k "test_arm"        # İsim filtresi
```

---

## 6. Dosya Boyut Analizi (En Büyük Dosyalar)

### Backend Servisleri
| Dosya | Boyut | Not |
|-------|-------|-----|
| report_export_service.py | 65.7KB | KTR rapor oluşturma — bölünebilir |
| self_test_service.py | 57KB | 30+ test senaryosu — bölünebilir |
| interface_inventory_service.py | 53KB | Arayüz envanteri — bölünebilir |
| release_service.py | 37.4KB | Release paketi oluşturma |
| data_lab_service.py | 35KB | Veri lab yönetimi |
| pico_service.py | 33.7KB | Pico yönetimi |
| model_package_service.py | 27.8KB | Model paketleme |
| camera_host_diagnostic_service.py | 27.2KB | Kamera tanılama |
| demo_timeline_service.py | 27KB | Demo senaryosu |

### Frontend View'ları
| Dosya | Boyut | Not |
|-------|-------|-----|
| VisionView.vue | 46KB | Component extraction gerekli |
| DataLabView.vue | 43KB | Component extraction gerekli |
| PicoView.vue | 31KB | Büyük ama bölünmüş yapıda |
| DashboardView.vue | 28KB | — |
| CalibrationView.vue | 23KB | — |
| ReportsView.vue | 21KB | — |

---

## 7. Bilinen Sorunlar ve İyileştirme Alanları

| Sorun | Öncelik | Açıklama |
|-------|---------|----------|
| Log rotation yok | 🔴 Yüksek | `logs/backend.jsonl` 413MB — rotation mekanizması gerekli |
| WebSocket broadcast | 🟡 Orta | Her 200ms'de tüm durum gönderiliyor — delta bazlı olmalı |
| Büyük servis dosyaları | 🟡 Orta | report_export, self_test, interface_inventory bölünmeli |
| Monolitik RuntimeState | 🟡 Orta | 30+ servis tek objede — DI container kullanılabilir |
| Üretim firmware yok | 🔴 Yüksek | firmware/pico2/ boş |
| Model dağıtımı | 🟡 Orta | YOLO modeller .gitignore'da — dağıtım stratejisi lazım |
| Frontend view boyutları | 🟢 Düşük | VisionView 46KB, DataLabView 43KB — component extraction |
