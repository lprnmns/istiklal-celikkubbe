# 01 — Genel Bakış ve Sistem Mimarisi

> Bu doküman, projeye yeni katılacak mühendislerin tüm sistemi anlaması için hazırlanmıştır.
> Amaç: Her dosyanın ne yaptığını, veri akışını, güvenlik katmanlarını bilerek yeni özellik ekleyebilmek.

---

## 1. Proje Nedir?

**İSTİKLAL Komuta Kontrol Merkezi** — TEKNOFEST Çelikkubbe Hava Savunma Sistemleri yarışması için geliştirilmiş, web tabanlı komuta-kontrol yazılımıdır.

**Ne yapar:**
- USB kameradan görüntü alır → YOLO ile hedef (gövde + balon) tespit eder
- HSV renk analizi ile dost/düşman ayrımı yapar
- Pan/tilt taret motorlarını yönlendirir (step motor + servo)
- 17 güvenlik kapısından geçerek ateş kararı verir
- Tüm bunları tek bir web arayüzünden yönetir

**Mevcut durum:** Sistem `dry_run` (kuru çalışma) modunda çalışır. Fiziksel motor/servo/ateşleme komutu üretilmez.

---

## 2. Teknoloji Stack

| Katman | Teknoloji | Versiyon |
|--------|-----------|----------|
| Backend | Python + FastAPI + Pydantic | Python 3.12+, FastAPI ≥0.111 |
| Frontend | Vue 3 + TypeScript + Pinia | Vue 3.5, TS 6, Vite 8 |
| CSS | TailwindCSS | v4 |
| Görüntü İşleme | OpenCV + Ultralytics YOLO | opencv-headless ≥4.9, ultralytics ≥8.4 |
| Seri İletişim | PySerial | ≥3.5 |
| Firmware | MicroPython (Raspberry Pi Pico 2) | — |
| Konfigürasyon | YAML + Pydantic validation | PyYAML ≥6.0 |
| Test | pytest + httpx | pytest ≥8.2 |
| Paket Yöneticisi | uv (backend), pnpm (frontend) | — |

---

## 3. Dizin Yapısı (Ne Nerededir?)

```
teknofest/
├── backend/                  ← Python FastAPI uygulaması
│   ├── app/
│   │   ├── main.py           ← Uygulama fabrikası, router kayıtları
│   │   ├── api/              ← 28 REST API router dosyası
│   │   ├── services/         ← 42 iş mantığı servisi
│   │   ├── schemas/          ← 32 Pydantic veri modeli
│   │   ├── protocols/        ← Seri protokol codec'leri (JSON-line, binary)
│   │   ├── transports/       ← Seri transport abstraction (mock, pyserial)
│   │   └── mocks/            ← Sahte kamera, vision, serial
│   ├── tests/                ← 34 test dosyası
│   └── pyproject.toml        ← Python bağımlılıkları
├── frontend/                 ← Vue 3 web arayüzü
│   ├── src/
│   │   ├── views/            ← 18 sayfa bileşeni
│   │   ├── stores/           ← 18 Pinia state yönetimi
│   │   ├── api/              ← 20 backend API istemci modülü
│   │   ├── types/            ← 19 TypeScript tip tanımı
│   │   ├── components/       ← Paylaşılan UI bileşenleri
│   │   ├── router/           ← Vue Router yapılandırması
│   │   └── utils/            ← Yardımcı fonksiyonlar
│   └── package.json          ← Frontend bağımlılıkları
├── firmware/                 ← Pico 2 MicroPython firmware'ları
│   ├── pico2/                ← (BOŞ — üretim firmware henüz yok)
│   └── pico2_telemetry_only/ ← Sadece telemetri gönderen firmware
├── config/
│   ├── config.yaml           ← Ana konfigürasyon dosyası (240 satır)
│   ├── device_profiles/      ← Cihaz profil şablonları
│   └── pin_profiles/         ← GPIO pin profil şablonları
├── models/                   ← YOLO model dosyaları dizini
├── data/                     ← Dataset, session, export verileri
├── logs/                     ← JSONL log dosyaları
├── exports/                  ← Dışa aktarılan raporlar
├── release/                  ← Portable launcher paketleri
├── eski_sistem_arayüz/       ← Önceki monolitik Python sistemi (referans)
├── start_linux.sh            ← Linux başlatma scripti
└── start_windows.bat         ← Windows başlatma scripti
```

---

## 4. Sistem Nasıl Başlar?

### Adım 1: Config yüklenir
```
config/config.yaml → ConfigService.load() → Pydantic AppConfig (20 alt-model)
```
Her alt-model kendi `model_validator` ile güvenlik kısıtlarını zorlar. Örneğin `SystemConfig`, `mode=DISARMED` değilse hata fırlatır.

### Adım 2: RuntimeState oluşturulur
```python
# backend/app/services/runtime_state.py
build_runtime(config, log_dir) → RuntimeState
```
Bu tek obje içinde 30+ servis instance'ı yaratılır ve birbirine bağlanır.

### Adım 3: FastAPI routerları kayıt edilir
```python
# backend/app/main.py → create_app()
app.include_router(health_router)
app.include_router(safety_router)
# ... toplam 28 router
```

### Adım 4: Frontend statik dosyaları serve edilir
Production'da `frontend/dist/` altındaki build çıktısı FastAPI tarafından serve edilir. SPA fallback ile tüm route'lar `index.html`'e yönlendirilir.

---

## 5. Veri Akışı (Canlı Mod)

```
USB Kamera
    ↓ frame (OpenCV / mock)
CameraService / CameraRuntimeService
    ↓ numpy array veya mock JPEG
VisionPipeline.latest()
    ↓ 3 moddan biri çalışır:
    ├─ Mock: sahte detection üretir
    ├─ OpenCV Circle Surrogate: gerçek kameradan daire algılar
    └─ Ultralytics YOLO: gerçek model inference
    ↓ VisionEvent (body_detections + balloon_detections)
DecisionEngine.evaluate()
    ↓ 17 güvenlik kapısını değerlendirir
    ↓ DecisionState (FIRE_READY / NO_FIRE / WAIT / LOCKED / NO_TARGET)
SafetyService.state()
    ↓ SafetyState (karar + kapı durumları)
WebSocket (200ms aralıkla)
    ↓ JSON envelope
Frontend systemStore → ilgili store'lara dağıtım
    ↓ Vue reactive UI güncelleme
```

---

## 6. Güvenlik Mimarisi (4 Katman)

### Katman 1: Config Validator
`config.yaml` yüklenirken Pydantic `model_validator` devreye girer:
- `system.mode` DISARMED olmalı
- `system.dry_run` true olmalı
- `hardware.physical_command_enabled` false olmalı
- Yanlış değer → uygulama başlamaz

### Katman 2: Servis Güvenlik Kontrolleri
Her servis kendi içinde engel kontrolü yapar:
- `MotionService._blocking()`: soft limit, e-stop, fault kontrolü
- `SerialService.send_json()`: risky komutları reddeder
- `PicoService`: read-only modda TX yapmaz

### Katman 3: Decision Engine Gate Sistemi
17 kapı ile değerlendirme:
- system_armed, dry_run, hardware_enabled, estop, pico, serial
- vision_running, body_detected, balloon_detected
- team_classified, enemy_target, friend_rejection
- range_valid, stable_track, forbidden_zone, operator_confirm
- motion gates (soft_limits, estop, fault, driver, dry_run)

### Katman 4: Dry-Run Engeli
Tüm fiziksel komutlar `no_physical_command_generated=true` etiketiyle loglanır. `hardware_enabled=false` olduğu sürece hiçbir motor/servo/ateş komutu üretilmez.

---

## 7. İletişim Protokolleri

### REST API
- 28 router, `/api/` prefix'i altında
- `Depends(get_runtime)` ile `RuntimeState`'e erişim
- JSON request/response

### WebSocket
- Endpoint: `/ws`
- 200ms polling döngüsü
- Envelope formatı: `{ type: string, ts: number, seq: number, payload: object }`
- 20+ mesaj tipi gönderilir (system.state, vision.frame, decision.updated, pico.telemetry...)

### Seri Protokol (Pico ↔ Backend)
- **JSON-line:** `{"type":"heartbeat","seq":1,"timestamp_ms":123456}\n`
- **Binary:** `0xAA | TYPE | SEQ | LEN | PAYLOAD | CRC16 | 0x55`
- TX tipleri: heartbeat, disarm, self_test, set_mode (güvenli), fire_request, jog_motor (riskli → engelli)
- RX tipleri: ack, nack, telemetry, error, heartbeat

---

## 8. Nasıl Çalıştırılır?

### Geliştirme Modu
```bash
# Backend
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload

# Frontend (ayrı terminalde)
cd frontend
pnpm install
pnpm dev
```
Backend: `http://localhost:8000`, Frontend: `http://localhost:5173`

### Testler
```bash
cd backend
uv run pytest       # 34 test dosyası
```

### Production (Portable Release)
```bash
./start_linux.sh    # release/linux/start_istiklal_c2.sh'yi çağırır
```
