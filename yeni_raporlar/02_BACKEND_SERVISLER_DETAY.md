# 02 — Backend Servis Katmanı Detaylı Analizi

> Her servisin ne yaptığı, hangi dosyada olduğu, hangi metotları açtığı ve diğer servislerle ilişkisi.

---

## 1. Servis Mimarisi

Tüm servisler `RuntimeState` içinde oluşturulur (`backend/app/services/runtime_state.py`). Dependency injection yok — servisler constructor'da birbirine bağlanır.

```python
# runtime_state.py — servis oluşturma zinciri (sadeleştirilmiş)
self.pico = PicoService(config, logger)
self.serial = SerialService(config, logger)
self.camera = CameraService(config)
self.camera_runtime = CameraRuntimeService(config, devices=self.device_manager, logger=logger)
self.vision = VisionService(config)
self.vision_pipeline = VisionPipeline(camera=self.camera, vision=self.vision)
self.decision_engine = DecisionEngine(config, logger)
self.motion = MotionService(config, logger)
self.safety = SafetyService(config, logger)
# ... 30+ servis daha
```

---

## 2. Temel Servisler (Çekirdek Pipeline)

### 2.1 ConfigService — `services/config_service.py` (35 satır)

**Ne yapar:** YAML config dosyasını okur → Pydantic `AppConfig`'e dönüştürür.

```python
class ConfigService:
    def load(self) -> AppConfig:
        raw = self._read_yaml()          # yaml.safe_load
        return AppConfig.model_validate(raw)  # Pydantic validation
```

**Önemli:** `default_config_path()` fonksiyonu `backend/` dizininden 3 seviye yukarı çıkarak `config/config.yaml`'ı bulur.

---

### 2.2 CameraService — `services/camera_service.py` (71 satır)

**Ne yapar:** Kamera yönetimi. Şu an sadece mock kamera destekler.

**Anahtar metotlar:**
- `start()` / `stop()` → MockCamera'yı başlatır/durdurur
- `snapshot()` → Tek JPEG frame döner (siyah 1x1 piksel)
- `mjpeg_stream()` → Async MJPEG stream generator (frontend'e canlı görüntü)
- `select(request)` → Kamera modu seçimi (mock/image/webcam)
- `sources()` → Mevcut kamera kaynaklarını listeler

**MockCamera** (`mocks/mock_camera.py`, 34 satır): Base64-encoded minimal siyah JPEG döner. Gerçek kamera frame'i yok.

---

### 2.3 CameraRuntimeService — `services/camera_runtime_service.py` (17KB)

**Ne yapar:** Gerçek kamera cihaz yönetimi. OpenCV `VideoCapture` ile çalışır.

- Cihaz profili yönetimi (source_type, device_path, resolution, fps, fourcc)
- `read_frame()` → OpenCV ile gerçek frame okuma
- `apply_profile()` → Kamera ayarlarını uygulama
- DeviceManagerService ile entegre çalışır

---

### 2.4 VisionService — `services/vision_service.py` (70 satır)

**Ne yapar:** Vision pipeline'ın durumunu ve mock detection üretimini yönetir.

**Anahtar metotlar:**
- `next_event(source, width, height)` → MockVisionGenerator'dan sahte detection alır
- `configure(update)` → Vision ayarlarını günceller (mode, model path, threshold)
- `status()` → VisionStatus döner (fps, latency, model durumu, uyarılar)

**MockVisionGenerator** (`mocks/mock_vision.py`, 60 satır):
- Her frame'de 1 `BodyDetection` (helicopter, conf=0.86, range=8.7m, team=enemy) üretir
- 1 `BalloonDetection` (conf=0.91) üretir
- Body sinüzoidal hareket eder (x ekseni)
- Her 17 frame'de bir "mock_low_contrast_frame" uyarısı üretir

---

### 2.5 VisionPipeline — `services/vision_pipeline.py` (183 satır)

**Ne yapar:** Kamera + Vision + Runtime'ı birleştirir. 3 modda çalışır:

**Mod 1 — Mock (varsayılan):**
```python
def latest(self):
    return self.vision.next_event(source=..., width=..., height=...)
```

**Mod 2 — OpenCV Live Circle Surrogate:**
```python
if self.vision_runtime.profile.inference_adapter == "opencv_live_circle_surrogate":
    event = self.surrogate.run(self.camera_runtime, self.vision_runtime.profile)
```

**Mod 3 — Ultralytics YOLO:**
```python
if self.vision_runtime.profile.inference_adapter == "ultralytics_yolo":
    event = self._latest_ultralytics_event()
```
Bu modda: frame okunur → `YOLO(model_path)` ile inference → BBox → BalloonDetection listesi

**Lazy model loading:** YOLO modeli ilk kullanımda yüklenir ve cache'lenir:
```python
def _load_yolo_model(self, model_path):
    if self._yolo_model is not None and self._yolo_model_path == model_path:
        return self._yolo_model  # cache hit
    self._yolo_model = YOLO(model_path)
```

---

### 2.6 DecisionEngine — `services/decision_engine.py` (231 satır)

**Ne yapar:** Tüm güvenlik kapılarını değerlendirerek ateş kararı verir.

**`evaluate(runtime, operator_confirmed)` akışı:**
1. En yüksek confidence'lı body ve balloon detection seçilir
2. Renk sınıflandırmasıyla takım belirlenir (enemy/friend/unknown)
3. 17 kapı değerlendirilir → pass/fail/warning/not_applicable
4. Fail kapılardan blocking_reasons listesi oluşturulur
5. Karar durumu belirlenir: `NO_TARGET → WAIT → LOCKED → NO_FIRE → FIRE_READY`

**`fire_request(runtime, operator_confirmed)` akışı:**
1. `evaluate()` çağrılır
2. FIRE_READY olsa bile `dry_run=true` ise fiziksel komut üretilmez
3. `hardware_enabled=false` ise ek engel eklenir
4. Sonuç loglanır

**Takım belirleme önceliği:**
1. ColorClassifierService son sonucu (detection_id eşleşmesi)
2. Body detection'daki `target_team` alanı
3. Body detection'daki `color_hint` alanı
4. Varsayılan: "unknown"

---

### 2.7 SafetyService — `services/safety_service.py` (58 satır)

**Ne yapar:** DecisionEngine sonucunu SafetyState formatına dönüştürür. Ek güvenlik kontrolü yaparak komutları reddeder.

- `state(decision)` → Kapı durumlarını SafetyGateState'e çevirir
- `reject_command(command)` → Her komutu varsayılan olarak reddeder

---

### 2.8 MotionService — `services/motion_service.py` (190 satır)

**Ne yapar:** Pan/tilt taret hareketlerini simüle eder.

**Komutlar:**
| Metot | İşlev |
|-------|-------|
| `jog(request)` | Tek adım hareket (pan/tilt, positive/negative) |
| `go_to(request)` | Belirtilen açıya git |
| `home()` | 0,0 pozisyonuna dön |
| `stop()` | Hareketi durdur |
| `scan_start()` | Tarama modunu başlat |
| `track_dry_run(request)` | Piksel hatasından açısal delta hesapla |

**Tracking hesaplama:**
```python
error_x = target_center_x - frame_center_x
error_y = target_center_y - frame_center_y
delta_pan = error_x * tracking_gain_x   # varsayılan 0.05
delta_tilt = error_y * tracking_gain_y
```

**Güvenlik kontrolleri (`_blocking()`):**
- FAULT durumunda hareket yok
- Sistem armed ise hareket yok
- E-stop aktif ise hareket yok
- Soft limit aşımı kontrolü
- Hardware enabled veya dry_run kapalı ise hareket yok

---

### 2.9 SerialService — `services/serial_service.py` (275 satır)

**Ne yapar:** Pico ile seri iletişimi yönetir (şu an mock transport).

**TX güvenlik sınıflandırması:**
- ✅ Güvenli: `heartbeat`, `disarm`, `self_test`, `set_mode`
- ❌ Riskli (engelli): `fire_request`, `jog_motor`, `set_servo`, `enable_driver`, `set_pin`, `pwm_write`, `step_pulse`

**ACK/timeout mekanizması:**
- Gönderilen mesajlar `pending` dict'te tutulur (seq → mesaj)
- `check_timeouts()` ile timeout kontrol edilir
- Heartbeat timeout'u → FAULT durumu

**Read-only modu:** `mark_real_readonly_connected()` çağrıldığında tüm TX engellenir, sadece RX telemetri alınır.

---

### 2.10 PicoService — `services/pico_service.py` (813 satır)

**En büyük servis. Sorumlulukları:**

1. **Mock Pico yönetimi:** Bağlan/kopma simülasyonu
2. **Port keşfi:** `/dev/ttyACM*`, `/dev/ttyUSB*`, `pyserial list_ports`
3. **Pin profili:** 26 GPIO pin tanımı, fonksiyon ataması, doğrulama
4. **Read-only bağlantı:** Gerçek seri port açma (sadece RX, TX yok)
5. **Telemetri parsing:** JSON satırlarını parse etme
6. **İzin teşhisi:** Linux kullanıcı grupları, device permission kontrolü
7. **Kanıt kaydetme:** Bağlantı durumu ve telemetri snapshot'ları

**Pin doğrulama kuralları:**
- Kritik fonksiyonlar tek pine atanmalı (çakışma yok)
- Pan/tilt step/dir zorunlu
- ESTOP_IN zorunlu
- Giriş fonksiyonları IN, çıkış fonksiyonları OUT yönünde olmalı
- TRIGGER_SERVO_PWM PWM-capable pin'de olmalı

---

### 2.11 ColorClassifierService — `services/color_classifier_service.py` (129 satır)

**Ne yapar:** HSV renk analizi ile dost/düşman sınıflandırması yapar.

**Mock modda sabit oranlar döner:**
- Enemy mock: `enemy=0.72, friend=0.06, unknown=0.22`
- Friend mock: `enemy=0.08, friend=0.74, unknown=0.18`
- Unknown mock: `enemy=0.20, friend=0.20, unknown=0.60`

**Karar mantığı:** `decision_threshold` (varsayılan 0.55) üzerindeki en yüksek oran kazanır.

**Balon maskesi:** Balon BBox içindeki pikseller renk analizinden çıkarılır (gerçek gövde rengi elde edilir).

---

### 2.12 CalibrationService — `services/calibration_service.py` (19KB)

**Ne yapar:** Kamera kalibrasyonu, mesafe hesaplama, yön semantiği.

- Fiziksel ölçümler: kamera yüksekliği, hedef yüksekliği, masa yüksekliği
- Lens profili ve FOV hesaplama
- Yön kalibrasyonu: Pan/tilt yönü ↔ piksel hareketi eşleştirmesi
- Homography ve distortion desteği (henüz aktif değil)

---

## 3. Veri / Rapor Servisleri

### 3.1 SessionService (8.9KB) → Veri toplama oturumları
### 3.2 AnnotationService (3.3KB) → Detection annotation yönetimi
### 3.3 DatasetService (12.6KB) → YOLO eğitim dataset'i oluşturma
### 3.4 DataLabService (35KB) → Veri lab oturumu, replay, annotation review
### 3.5 ReplayService (2.8KB) → Kayıtlı video/frame tekrar oynatma
### 3.6 ModelRegistryService (12KB) → Model kayıt, listeleme, versiyon yönetimi
### 3.7 ModelPackageService (27.8KB) → Model paketleme, aktivasyon, test
### 3.8 ReportExportService (65.7KB) → KTR raporu, güvenlik özeti, self-test raporu dışa aktarma
### 3.9 ReleaseService (37.4KB) → Portable release paketi oluşturma
### 3.10 SelfTestService (57KB) → 30+ otomatik self-test senaryosu

---

## 4. Altyapı Servisleri

### 4.1 LogService — `services/log_service.py` (41 satır)

```python
class JsonlLogService:
    def emit(self, level, subsystem, message, details):
        event = LogEvent(ts=time.time(), level=level, ...)
        # logs/backend.jsonl dosyasına append eder
```

**DİKKAT:** Log rotation yok — dosya süresiz büyür (şu an 413MB!).

### 4.2 StoragePaths — `services/storage_paths.py` (18 satır)

`project_root()` fonksiyonu 3 yöntemle proje kökünü bulur:
1. CWD `backend/` ise parent'ı döner
2. CWD'de `backend/` ve `config/` varsa CWD döner
3. Dosya konumundan 3 seviye yukarı çıkar

### 4.3 SafetyGateService — `services/safety_gate_service.py` (24 satır)

4 helper fonksiyon: `pass_gate()`, `fail_gate()`, `warning_gate()`, `na_gate()` — `SafetyGate` nesnesi oluşturur.

---

## 5. Seri Protokol Katmanı

### 5.1 JSON-Line Protokolü — `protocols/serial_json.py` (121 satır)

**PC → Pico (TX) mesaj tipleri:**
- `HeartbeatTx` — yaşam işareti
- `DisarmTx` — sistem devre dışı bırak
- `SelfTestTx` — self-test komutu
- `SetModeTx` — mod değiştir
- `RiskyCommandTx` — ateş, motor jog, servo (ENGELLİ)

**Pico → PC (RX) mesaj tipleri:**
- `AckRx` — komut kabul edildi
- `NackRx` — komut reddedildi
- `TelemetryRx` — durum telemetrisi
- `ErrorRx` — hata bildirimi
- `HeartbeatRx` — yaşam işareti

**Encode/decode:** JSON string + newline → bytes

### 5.2 Binary Protokolü — `protocols/serial_binary.py` (75 satır)

Paket yapısı:
```
[0xAA] [TYPE:1] [SEQ:1] [LEN:1] [PAYLOAD:LEN] [CRC16:2] [0x55]
```

**CRC16/XMODEM** (`protocols/crc16.py`): Standart XMODEM algoritması, poly=0x1021.

### 5.3 Transport — `transports/`

- `serial_transport.py` → Abstract base (Protocol)
- `mock_serial_transport.py` → Bellekte buffer tutar
- `pyserial_transport.py` → Gerçek serial.Serial wrapper
