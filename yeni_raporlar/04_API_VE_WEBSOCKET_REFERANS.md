# 04 — API Referansı ve WebSocket Mesaj Kataloğu

> Tüm backend API endpoint'leri ve WebSocket mesaj tipleri referansı.

---

## 1. REST API Endpoint Listesi

### 1.1 Safety — `/api/safety/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/safety/state` | Tüm karar durumunu döner (DecisionState) |
| GET | `/api/safety/gates` | Güvenlik kapılarını döner (SafetyState) |
| POST | `/api/safety/arm` | Sistemi arm eder (dry-run, test amaçlı) |
| POST | `/api/safety/disarm` | Sistemi disarm eder (her zaman kabul edilir) |
| POST | `/api/safety/fire-request` | Ateş talebi değerlendirir (dry_run → hiçbir zaman fiziksel) |

### 1.2 Vision — `/api/vision/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/vision/status` | Vision pipeline durumu |
| GET | `/api/vision/latest` | Son detection event |
| POST | `/api/vision/start` | Vision pipeline başlat |
| POST | `/api/vision/stop` | Vision pipeline durdur |
| POST | `/api/vision/snapshot` | Tek frame snapshot |
| PUT | `/api/vision/config` | Vision ayarları güncelle |
| GET | `/api/camera/status` | Kamera durumu |
| GET | `/api/camera/stream.mjpg` | MJPEG canlı akış |
| GET | `/api/camera/sources` | Mevcut kamera kaynakları |
| POST | `/api/camera/select` | Kamera modu seç |
| GET | `/api/vision/legacy-presets` | Eski sistem preset'leri |
| GET | `/api/vision/real-camera/status` | Gerçek kamera evidence durumu |
| POST | `/api/vision/real-camera/select` | Gerçek kamera cihaz seç |
| POST | `/api/vision/real-camera/capture-evidence` | Gerçek kamera kanıt yakala |
| GET | `/api/vision/real-camera/acceptance` | Gerçek kamera kabul durumu |
| POST | `/api/vision/camera-host/diagnose` | Kamera host tanılama |

### 1.3 Pico — `/api/pico/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/pico/status` | Pico bağlantı durumu |
| GET | `/api/pico/ports` | Mevcut seri portlar |
| POST | `/api/pico/connect` | Mock Pico bağlan |
| POST | `/api/pico/disconnect` | Pico kopma |
| GET | `/api/pico/pins` | Mevcut pin profili |
| POST | `/api/pico/pins/validate` | Pin profili doğrula |
| PUT | `/api/pico/pins` | Pin profili kaydet |
| GET | `/api/pico/discovery/ports` | Detaylı port keşfi (VID/PID/Serial) |
| POST | `/api/pico/read-only/connect` | Read-only seri bağlantı |
| POST | `/api/pico/read-only/disconnect` | Read-only kopma |
| GET | `/api/pico/read-only/status` | Read-only bağlantı durumu |
| GET | `/api/pico/read-only/permission-status` | Linux izin teşhisi |
| GET | `/api/pico/read-only/latest-telemetry` | Son read-only telemetri |
| POST | `/api/pico/read-only/capture-evidence` | Read-only kanıt kaydet |

### 1.4 Serial — `/api/serial/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/serial/status` | Seri bağlantı durumu |
| GET | `/api/serial/logs` | Son seri log'ları |
| POST | `/api/serial/send` | Manuel mesaj gönder (güvenli tiplerde) |

### 1.5 Motion — `/api/motion/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/motion/status` | Motor pozisyonu ve durumu |
| POST | `/api/motion/jog` | Tek adım hareket |
| POST | `/api/motion/go-to` | Açısal hedefe git |
| POST | `/api/motion/home` | Home pozisyonuna dön |
| POST | `/api/motion/stop` | Hareketi durdur |
| POST | `/api/motion/scan/start` | Tarama başlat |
| POST | `/api/motion/scan/stop` | Taramayı durdur |
| POST | `/api/motion/track` | Tracking dry-run |
| GET | `/api/motion/settings` | Hareket ayarları |
| PUT | `/api/motion/settings` | Hareket ayarlarını güncelle |

### 1.6 Calibration — `/api/calibration/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/calibration/status` | Kalibrasyon durumu |
| PUT | `/api/calibration/update` | Kalibrasyon değerlerini güncelle |
| POST | `/api/calibration/direction/simulate` | Yön semantiği simüle et |
| POST | `/api/calibration/direction/observe` | Gözlem kaydet |

### 1.7 Color — `/api/color/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/color/config` | Renk sınıflandırma ayarları |
| PUT | `/api/color/config` | Ayarları güncelle |
| POST | `/api/color/classify` | Renk sınıflandırma testi |
| POST | `/api/color/mask-preview` | Balon maskesi önizleme |
| POST | `/api/color/reset` | Sıfırla |

### 1.8 Models — `/api/models/`

| Metot | Path | Açıklama |
|-------|------|----------|
| GET | `/api/models/registry` | Model listesi |
| POST | `/api/models/packages/upload` | Model paket yükle |
| POST | `/api/models/packages/{id}/activate` | Model aktive et |
| POST | `/api/models/packages/{id}/deactivate` | Model deaktive et |
| POST | `/api/models/packages/{id}/test` | Model dry-run testi |

### 1.9 Diğer Endpoint'ler

| Prefix | Açıklama |
|--------|----------|
| `/api/data-lab/` | Data Lab session, replay, annotation |
| `/api/dataset/` | Dataset oluşturma, sağlık kontrolü |
| `/api/demo/` | Demo timeline, jüri paketi |
| `/api/devices/` | USB cihaz yönetimi |
| `/api/hardware/` | Donanım keşfi, telemetri |
| `/api/first-run/` | İlk çalıştırma sihirbazı |
| `/api/self-test/` | Self-test çalıştır / sonuç |
| `/api/reports/` | KTR raporu oluştur / indir |
| `/api/interfaces/` | Arayüz envanteri |
| `/api/logs/` | JSONL log oku / temizle |
| `/api/release/` | Portable release paketi |
| `/health` | Sağlık kontrolü |

---

## 2. WebSocket Mesaj Kataloğu

### Bağlantı
- Endpoint: `ws://localhost:8000/ws`
- Protokol: JSON text frame
- Yenileme aralığı: **200ms** (backend `asyncio.sleep(0.2)`)

### Envelope Formatı
```json
{
  "type": "system.state",
  "ts": 1716000000.123,
  "seq": 42,
  "payload": { ... }
}
```

### Sürekli Gönderilen Mesajlar (Her 200ms)

| type | payload | Açıklama |
|------|---------|----------|
| `system.state` | SystemState | Sistem modu, arm durumu, fire_policy |
| `decision.updated` | DecisionState | Karar motoru sonucu |
| `decision.gates` | SafetyState | 17 güvenlik kapısı durumu |
| `safety.gates` | SafetyState | Güvenlik durumu (decision.gates ile aynı) |
| `pico.telemetry` | PicoTelemetry | Pico bağlantı ve telemetri |
| `pico.connection` | PicoConnectionEvent | Pico bağlantı olayı |
| `pico.pin_validation` | PinValidationResult | Pin profil doğrulama |
| `serial.status` | SerialStatus | Seri port durumu |
| `motion.status` | MotionState | Motor pozisyonu |
| `hardware.status` | HardwareStatus | Donanım keşif durumu |
| `hardware.telemetry` | HardwareTelemetry | Donanım telemetrisi |
| `calibration.status` | CalibrationStatus | Kalibrasyon durumu |
| `vision.status` | VisionStatus | Vision pipeline durumu |
| `vision.frame` | VisionEvent | Son detection frame |
| `vision.detections` | VisionEvent | Son detection (frame ile aynı) |
| `camera.status` | CameraStatus | Kamera durumu |
| `camera.runtime_status` | CameraRuntimeStatus | Kamera runtime ayarları |
| `vision.runtime_status` | VisionRuntimeStatus | Vision runtime ayarları |
| `vision.frame_stats` | FrameStats | FPS ve latency metrikleri |

### Koşullu Gönderilen Mesajlar

| type | Koşul | Açıklama |
|------|-------|----------|
| `safety.armed` | Arm çağrıldığında | Arm kabul/red sonucu |
| `safety.disarmed` | Disarm çağrıldığında | Disarm sonucu |
| `safety.fire_request_*` | Fire request'te | Ateş talebi sonucu |
| `safety.fault` | decision=FAULT | Hata durumu |
| `motion.command_*` | Hareket komutu | Komut kabul/red |
| `motion.fault` | motion=FAULT | Motor hata durumu |
| `vision.warning` | Uyarı varsa | Vision uyarısı |
| `serial.timeout` | Timeout oluşursa | ACK timeout |
| `serial.log_*` | Log oluşursa | TX/RX/hata log |
| `color.config_updated` | Config güncelleme | Renk ayarları değişti |
| `color.classification` | Sınıflandırma | Renk sonucu |
| `color.mask_preview` | Maske önizleme | Balon maskesi |
| `calibration.*` | Kalibrasyon olayı | Kalibrasyon güncelleme |
| `model.*` | Model olayı | Model paket/aktivasyon |
| `data_lab.*` | DataLab olayı | Session/replay/annotation |
| `demo.*` | Demo olayı | Timeline/readiness |
| `report.*` | Rapor olayı | KTR/export |
| `release.*` | Release olayı | Paket oluşturma |
| `self_test.*` | Self-test olayı | Test sonuçları |
| `pico.readonly_*` | Read-only Pico | Telemetri/bağlantı |
| `pico.real_*` | Gerçek Pico | RX-only telemetri |

---

## 3. Dependency Injection Pattern

Backend'de tek bir DI mekanizması var:

```python
# backend/app/api/deps.py (9 satır)
def get_runtime(request: Request) -> RuntimeState:
    return request.app.state.runtime

# Kullanım (her router'da):
@router.get("/status")
def get_status(runtime: RuntimeState = Depends(get_runtime)):
    return runtime.vision_pipeline.status()
```

`app.state.runtime` → `create_app()` içinde set edilir → tüm router'lar aynı `RuntimeState` instance'ına erişir.
