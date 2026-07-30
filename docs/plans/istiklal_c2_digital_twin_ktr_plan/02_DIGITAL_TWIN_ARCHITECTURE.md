# 02 — Digital Twin Architecture: Read-only Telemetry Mirror

## Amaç

Bu mimari, mevcut çalışan İSTİKLAL C2 tracker sistemini değiştirmeden, onun ürettiği durum bilgisini 3B dijital ikiz kokpitinde görünür kılar.

Ana prensip:

> Digital twin, komut üreten bir kontrol katmanı değildir. Sistemin görüntü, takip, yönelim, hedef, güvenlik ve olay durumunu gerçek zamanlı görselleştiren read-only gözlem katmanıdır.

## Sistem bileşenleri

```text
USB Camera
   ↓
Vision / YOLO / Detection Layer
   ↓
Tracker / Target Selection / PID
   ↓
Existing Command Path → Pico / Motor / Servo
   ↓
Telemetry + ACK + State
   ↓
Digital Twin State Adapter
   ↓
Frontend Cockpit 3D Viewer + Timeline + Evidence Export
```

## Veri kaynakları

### Kamera

- device: `/dev/video2` gibi runtime seçilen cihaz
- frame size
- FPS
- capture latency
- real/surrogate flag
- latest frame evidence path

### Vision/YOLO

- class id
- class label
- confidence
- bbox
- target center
- image center error
- detection timestamp
- model version

### Tracker

- tracking state
- selected target id
- PID error
- commanded desired motion
- current target lock quality
- lost-frame count

### Pico/Serial telemetry

- connected/disconnected
- firmware/version if available
- current pan/tilt if telemetry reports it
- last ACK
- queue length
- error state

### Safety

- E-stop
- fire policy
- hardware enable
- physical command enabled
- fire blocked reason
- command queue clean/dirty

## Digital twin state contract

State tek bir normalize response üzerinden frontend’e sunulmalı. Böylece 3D viewer, mevcut backend iç detaylarını bilmez.

```json
{
  "schema_version": "digital_twin_state.v1",
  "timestamp_ms": 0,
  "mode": "live",
  "source": "tracker_telemetry_adapter",
  "device_pose": {
    "pan_deg": 0.0,
    "tilt_deg": 0.0,
    "servo_angle_deg": 0.0,
    "pose_quality": "telemetry|estimated|fixture|unknown"
  },
  "target": {
    "detected": false,
    "track_id": null,
    "class_id": null,
    "class_label": null,
    "confidence": 0.0,
    "bbox_xyxy": null,
    "estimated_scene_position": null
  },
  "tracker": {
    "state": "idle",
    "tracking_enabled": false,
    "error_px": [0, 0],
    "latency_ms": 0.0
  },
  "engagement": {
    "fire_allowed": false,
    "fire_blocked_reason": "not_armed",
    "last_event": null,
    "target_loss_after_engagement": false
  },
  "safety": {
    "e_stop": false,
    "fire_policy": "NO_FIRE",
    "hardware_enabled": false,
    "physical_command_enabled": false,
    "digital_twin_read_only": true
  }
}
```

## Frontend component önerisi

```text
components/digital-twin/
  DigitalTwinPanel.tsx
  DigitalTwinScene.tsx
  IstiklalC2Model.tsx
  TargetProjection.tsx
  SafetyOverlay.tsx
  EngagementRay.tsx
  ReplayTimeline.tsx
  useDigitalTwinState.ts
  digitalTwinTypes.ts
  modelRegistry.ts
```

## Backend önerisi

```text
app/api/digital-twin/
  state/route.ts veya backend eşleniği
  assets/route.ts
  replay/latest/route.ts
  replay/[run_id]/route.ts

lib/digital-twin/
  state_contract.py / ts
  state_adapter.py
  replay_builder.py
  target_projection.py
  asset_registry.py
```

## 3D scene davranışı

### Device model

- `base_node`: sabit taban.
- `yaw_node`: X/pan motoruna göre döner.
- `pitch_node`: Y/tilt motoruna göre döner.
- `camera_node`: kamera pozisyonunu gösterir.
- `launcher_node`: yönelim çizgisi için referans.
- `trigger_node`: servo görsel animasyonu için opsiyonel.

### Target model

- `target_class_01`...`target_class_04`
- `balloon_fallback`
- `unknown_target`

Target placement:

- İlk aşamada bbox center error üzerinden approximate sahne pozisyonu.
- Derinlik bilinmediği için `quality: approximate_from_bbox` yazılmalı.
- UI’da “approximate” badge görünmeli.

### Engagement visualization

- Fire event gelirse modelden hedef yönüne kısa pulse/ray animasyonu.
- Eğer hedef kısa süre sonra kaybolursa:
  - “target_lost_after_engagement_candidate”
- Kesin imha iddiası için ekstra kanıt yoksa “confirmed hit” yazılmamalı.

## Replay mode

Replay, live sistem yokken geliştirme ve KTR kanıtı için kritik.

Event formatı:

```json
{
  "t_ms": 1234,
  "type": "target_detected",
  "payload": {
    "track_id": "t1",
    "class_id": "balloon",
    "bbox_xyxy": [100, 100, 200, 200],
    "confidence": 0.91
  }
}
```

Replay state builder:

- event stream’i deterministic state’e çevirir.
- timeline scrubber ile oynatılır.
- testler fixture dosyası ile yapılır.

## Performance sınırı

3D panel, tracker performansını etkilememeli:

- Render 30 FPS ile sınırlandırılabilir.
- Telemetry update 10-20 Hz yeterli.
- Heavy asset lazy-load edilmeli.
- GLB düşük polygon/optimize olmalı.
- Kamera stream renderı ve 3D render farklı component boundaries içinde tutulmalı.
- 3D hata verirse error boundary fallback göstermeli.

## Safety boundary

Digital twin tarafında yasaklar:

- Motor komutu üretmek
- Servo/tetik komutu üretmek
- Serial TX yapmak
- Fire endpoint çağırmak
- Hardware enable değiştirmek
- E-stop state değiştirmek

İzin verilenler:

- State okumak
- Event okumak
- Replay üretmek
- Rapor/evidence üretmek
- Görsel animasyon göstermek
