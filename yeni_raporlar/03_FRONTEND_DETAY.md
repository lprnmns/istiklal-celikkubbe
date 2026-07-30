# 03 — Frontend Detaylı Analizi

> Vue 3 + Pinia + TypeScript + TailwindCSS v4 ile yazılmış web arayüzünün detaylı analizi.

---

## 1. Giriş Noktası ve Yapı

### main.ts (8 satır)
```typescript
createApp(App)
  .use(createPinia())   // State yönetimi
  .use(router)          // Sayfa yönlendirme
  .mount('#app')
```

### App.vue (4 satır)
Sadece `<RouterView />` render eder — tüm layout AppShell'de.

---

## 2. Router Yapısı — `router/index.ts`

Tek seviye layout: `AppShell` → children routes.

| Route | View | Görev |
|-------|------|-------|
| `/` | DashboardView | Ana gösterge paneli |
| `/system` | SystemView | Sistem durum özeti |
| `/safety` | SafetyView | Güvenlik kapıları detayı |
| `/self-test` | SelfTestView | Otomatik test çalıştırma |
| `/first-run` | FirstRunView | İlk çalıştırma sihirbazı |
| `/demo` | DemoView | Jüri demo senaryosu |
| `/pico` | PicoView | Pico bağlantı, pin profili |
| `/devices` | DevicesView | USB cihaz yönetimi |
| `/serial` | SerialView | Seri port monitör |
| `/vision` | VisionView | Canlı görüntü + algılama |
| `/models` | ModelsView | YOLO model yönetimi |
| `/motion` | MotionView | Pan/tilt kontrol |
| `/calibration` | CalibrationView | Kalibrasyon ayarları |
| `/color` | ColorView | HSV renk sınıflandırma |
| `/data-lab` | DataLabView | Veri toplama/replay |
| `/reports` | ReportsView | KTR raporları |
| `/interfaces` | InterfacesView | Arayüz envanteri |
| `/logs` | LogsView | JSONL log görüntüleyici |

---

## 3. AppShell Layout — `components/layout/AppShell.vue` (217 satır)

Ana layout bileşeni. Sol sidebar + üst header + ana içerik.

### Sidebar
3 navigasyon grubu:
- **Operations:** Dashboard, System, Safety, Self-Test, First Run, Demo
- **Engineering:** Pico, Devices, Serial, Vision, Models, Motion, Calibration, Color
- **Data & Reports:** Data Lab, Reports, Interfaces, Logs

Alt kısımda "Safety Lock" paneli — her zaman `DISARMED / NO_FIRE` gösterir.

### Header
Status badge'leri:
- Backend bağlantı durumu
- Pico durumu (Mock/Read-Only/Physical)
- Kamera durumu
- Serial modu
- Hardware modu
- Motion dry-run durumu
- Environment, profile, self-test badge'leri

### onMounted
Sayfa açıldığında otomatik olarak:
```typescript
store.connect()           // WebSocket bağlantısı
selfTest.refresh()        // Son self-test sonucu
firstRun.refresh()        // İlk çalıştırma durumu
interfaces.refresh()      // Arayüz envanteri
hardware.refresh()        // Donanım durumu
deviceRuntime.refresh()   // Cihaz runtime ayarları
```

---

## 4. State Yönetimi — Pinia Stores

### 4.1 systemStore.ts (556 satır) — EN KRİTİK STORE

**Sorumlulukları:**
1. WebSocket bağlantı yönetimi
2. Gelen mesajları ilgili store'lara yönlendirme
3. Event summary üretimi
4. Son 200 event'i saklama

**WebSocket bağlantı:**
```typescript
// URL belirleme:
// 1. VITE_BACKEND_WS_URL env var
// 2. Aynı host, farklı port (5173 ise 8000'e yönlendir)
// 3. Aynı host:port + /ws

socket = new TelemetrySocket({
  url: websocketUrl(),
  onMessage: handleEnvelope,   // Ana mesaj router
})
```

**handleEnvelope — Mesaj Router (≈100 satır):**
```typescript
if (event.type === 'system.state')     → systemState güncelle
if (event.type === 'decision.gates')   → safetyState güncelle
if (event.type === 'pico.telemetry')   → picoTelemetry güncelle
if (event.type === 'vision.frame')     → visionStore.applyVisionEvent()
if (event.type === 'serial.status')    → serialStore.applyStatus()
if (event.type === 'motion.status')    → motionStore.applyStatus()
// ... 20+ event tipi daha
```

**eventSummary — Okunabilir Özet (≈200 satır):**
Her event tipi için kullanıcıya gösterilecek kısa açıklama üretir. Örnek:
- `system.state` → "DISARMED / NO_FIRE"
- `motion.status` → "IDLE, pan=0deg, tilt=0deg"
- `vision.frame` → detection sayısı

---

### 4.2 visionStore.ts (8.2KB)
- Vision ve kamera durumu
- Son detection event'i
- Vision uyarıları

### 4.3 decisionStore.ts (2.4KB)
- Son karar durumu
- Güvenlik olayları listesi

### 4.4 motionStore.ts (3.8KB)
- Pan/tilt pozisyonu
- Hareket ayarları
- Komut geçmişi

### 4.5 serialStore.ts (2.5KB)
- Seri port durumu
- Son TX/RX log'ları

### 4.6 hardwareStore.ts (4KB)
- Donanım keşif durumu
- Telemetri bilgileri

### 4.7 deviceRuntimeStore.ts (8.7KB)
- Kamera runtime profili
- Vision runtime profili
- Device profil yönetimi

### 4.8 dataLabStore.ts (9.4KB)
- Session listesi
- Annotation durumu
- Dataset sağlık kontrolü

### 4.9 demoStore.ts (2.6KB)
- Demo timeline event'leri
- Readiness durumu

### 4.10 selfTestStore.ts (3KB)
- Son test sonuçları
- Test çalıştırma durumu

### 4.11 Diğer store'lar
- `calibrationStore.ts` (5.1KB) — Kalibrasyon durumu
- `colorStore.ts` (3KB) — Renk sınıflandırma ayarları
- `firstRunStore.ts` (3.5KB) — İlk çalıştırma durumu
- `interfacesStore.ts` (2KB) — Arayüz envanteri
- `modelPackageStore.ts` (3KB) — Model paketleri
- `reportsStore.ts` (2.6KB) — Rapor durumu
- `releaseStore.ts` (3KB) — Release paketi durumu
- `deviceProfileStore.ts` (1.1KB) — Cihaz profilleri

---

## 5. API İstemci Katmanı — `api/`

Her modül aynı pattern'i kullanır:

```typescript
// 1. Base URL belirleme
function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_BACKEND_API_URL
  if (configured) return configured
  if (window.location.port !== '5173') return window.location.origin
  return `${window.location.protocol}//${window.location.hostname}:8000`
}

// 2. Generic request helper
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  return body as T
}

// 3. Endpoint fonksiyonları
export function fetchVisionStatus(): Promise<VisionStatus> {
  return request<VisionStatus>('/api/vision/status')
}
```

**API modülleri:** vision, pico, serial, motion, calibration, color, decision, demo, dataLab, deviceRuntime, deviceProfiles, firstRun, hardware, interfaces, logs, modelPackages, release, reports, selfTest, websocket

---

## 6. Tip Sistemi — `types/`

Backend Pydantic şemalarının TypeScript karşılıkları. Önemli tipler:

### system.ts
```typescript
interface SystemState {
  mode: string; armed: boolean; fire_policy: string;
  dry_run: boolean; hardware_enabled: boolean;
  ready: boolean; uptime_s: number;
}

interface SafetyGateState {
  armed: boolean; estop_released: boolean;
  pico_heartbeat: boolean; track_stable: boolean;
  target_enemy: boolean; balloon_detected: boolean;
  // ... 17 kapı
}

interface WebSocketEnvelope<TPayload = unknown> {
  type: string; ts: number; seq: number; payload: TPayload;
}
```

---

## 7. WebSocket İstemcisi — `api/websocket.ts` (75 satır)

```typescript
class TelemetrySocket {
  connect()      // WebSocket bağlantısı aç
  disconnect()   // Manuel kapatma
  // Otomatik reconnect: 2 saniye sonra tekrar dene
  scheduleReconnect() → window.setTimeout(() => this.connect(), 2000)
}
```

**Önemli:** Bağlantı koptuğunda otomatik reconnect devreye girer. `manuallyClosed` flag'i ile manuel kapatma ayrımı yapılır.

---

## 8. Bileşen Yapısı — `components/`

```
components/
├── layout/
│   └── AppShell.vue          ← Ana layout (sidebar + header + content)
├── dashboard/
│   ├── DashboardCard.vue     ← Genel kart bileşeni
│   └── MetricRow.vue         ← Metrik satırı
├── safety/
│   └── SafetyGatesPanel.vue  ← 17 güvenlik kapısı görsel paneli
├── shared/
│   └── StatusBadge.vue       ← Durum rozeti (good/warn/bad/neutral)
└── pico/
    ├── PicoBoard.vue         ← Pico 2 pin diyagramı (SVG)
    └── PinValidationPanel.vue ← Pin doğrulama sonuçları
```

---

## 9. Stil Sistemi

TailwindCSS v4 kullanılır. Vite plugin olarak entegre:
```typescript
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'
plugins: [vue(), tailwindcss()]
```

**Renk paleti:**
- Arka plan: `#0b0d10` (koyu lacivert-siyah)
- Sidebar: `#111418`
- Vurgu: `cyan-300/400` (ISTIKLAL markası)
- Uyarı: `amber-400`, Hata: `red-400`
- Metin: `slate-100/300/400/500`

---

## 10. Yeni Sayfa/Özellik Ekleme Rehberi

### Adım 1: Backend API router oluştur
```python
# backend/app/api/yeni_modul.py
router = APIRouter(prefix="/api/yeni-modul", tags=["yeni-modul"])

@router.get("/status")
def get_status(runtime: RuntimeState = Depends(get_runtime)):
    return runtime.yeni_servis.status()
```

### Adım 2: Router'ı main.py'ye kaydet
```python
from app.api.yeni_modul import router as yeni_modul_router
app.include_router(yeni_modul_router)
```

### Adım 3: Frontend types tanımla
```typescript
// frontend/src/types/yeniModul.ts
export interface YeniModulStatus { ... }
```

### Adım 4: API client oluştur
```typescript
// frontend/src/api/yeniModul.ts
export function fetchYeniModulStatus(): Promise<YeniModulStatus> {
  return request<YeniModulStatus>('/api/yeni-modul/status')
}
```

### Adım 5: Pinia store oluştur
```typescript
// frontend/src/stores/yeniModulStore.ts
export const useYeniModulStore = defineStore('yeniModul', () => { ... })
```

### Adım 6: View oluştur ve router'a ekle
```vue
<!-- frontend/src/views/YeniModulView.vue -->
```
```typescript
// router/index.ts
{ path: 'yeni-modul', name: 'yeni-modul', component: YeniModulView }
```

### Adım 7: AppShell navigasyonuna ekle
```typescript
// components/layout/AppShell.vue → navGroups
{ label: 'Yeni Modul', to: '/yeni-modul' }
```
