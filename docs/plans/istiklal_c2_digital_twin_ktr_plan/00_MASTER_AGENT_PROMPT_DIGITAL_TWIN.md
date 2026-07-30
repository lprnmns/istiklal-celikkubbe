# 00 — MASTER AGENT PROMPT: İSTİKLAL C2 Digital Twin + KTR Odaklı Arayüz Dönüşümü

## Rolün

Sen bu repoda çalışan kıdemli full-stack + robotics UI + safety-critical systems agentısın. Görevin mevcut çalışan İSTİKLAL C2 yarışma kokpitini bozmadan, KTR puanını artıracak şekilde **telemetry-driven digital twin / operasyonel dijital ikiz** altyapısını eklemektir.

Bu iş bir “görsel süsleme” işi değildir. Amaç:

1. Mevcut balon tespit + takip + indirme kabiliyetini korumak.
2. Mevcut çalışan akışı kırmadan sistem durumunu daha profesyonel, anlaşılır ve kanıtlanabilir hale getirmek.
3. KTR raporunda mekanik, elektronik, yazılım, arayüz, senaryo, test, güvenlik ve özgünlük bölümlerine doğrudan kanıt üretecek bir yapı kurmak.
4. Sonradan balon YOLO modeli yerine yarışmanın istediği 4 hedef sınıfı için eğitilen YOLO modelinin takılabileceği sınıf-bağımsız bir hedef temsil katmanı hazırlamak.
5. 3D model/sanal sahne ile gerçek sistemin telemetry state’ini eşleştirerek operatöre “cihazın yanında duruyormuş gibi” anlık izleme imkânı vermek.

## En kritik kural: çalışan tracker bozulmayacak

Mevcut sistemin gerçek cihazla balonları tespit edip takip ettiği ve hedefleri aşağı indirebildiği varsayılmalıdır. Bu yüzden:

- Mevcut vision/tracker/Pico command path davranışını refactor etme.
- Var olan endpoint isimlerini ve response contract’larını kırma.
- Digital twin için ihtiyaç duyulan datayı mevcut pipeline’dan **read-only tap / adapter** ile al.
- 3D UI crash olursa tracker devam etmeli.
- Digital twin kapalıyken sistem eski kokpit davranışını aynen sürdürmeli.
- Eski kokpit için fallback bırakılmalı.
- Her değişiklik feature flag altında olmalı: örnek `DIGITAL_TWIN_ENABLED=false/true`.

## Güvenlik ve fiziksel komut sınırı

Bu fazlarda cihaz yanımızda olmayabilir. Bu yüzden implementasyon aşamasında:

- Gerçek fiziksel komut gönderen yeni bir yol ekleme.
- Digital twin’den motor/servo/fire komutu üretme.
- 3D sahne yalnızca telemetry/render/replay katmanı olsun.
- Var olan command path’e müdahale etme.
- Hardware test gerektiren her acceptance “deferred_hardware_acceptance” olarak işaretlenmeli.
- Her rapor/event şunu açıkça taşımalı:
  - `physical_command_path: existing_system_only`
  - `digital_twin_command_authority: false`
  - `digital_twin_read_only: true`
  - `hardware_acceptance_required: true`

## KTR hedefi

KTR’de toplam puanın büyük kısmı tasarım, arayüz, test, güvenlik ve özgünlükten geliyor. Bu işin çıktıları şu bölümlere doğrudan bağlanmalı:

- 4.1 Mekanik Tasarım:
  - CAD model parçalanması
  - pan/tilt eksenlerinin dijital ikizde tanımlanması
  - servis edilebilirlik, kablo yönlendirme, limit stop, kamera yerleşimi, montaj doğrulama
- 4.2 Elektronik + Algoritma + Yazılım:
  - kamera, Pico, step motor sürücüleri, servo, E-stop, serial telemetry
  - YOLO hedef sınıfı abstraction
  - tracker state machine
  - event sourcing/replay
- 4.3 Arayüzler:
  - yalnızca UI değil; mesaj arayüzleri, telemetry contract, frontend/backend/Pico arayüzleri
  - 3D operational digital twin cockpit
- 4.4 Sistem senaryoları:
  - tespit, takip, hedefe yönlenme, angajman, hedef kaybı, hata durumları
  - sequence/activity/state diyagramlarına veri sağlayacak event log
- 5 Test:
  - replay test, fixture test, clean-room package, camera acceptance, Pico acceptance, latency
- 6 Güvenlik:
  - E-stop, fire gate, hardware enable, no-command states, command authority boundary
- 9 Özgünlük:
  - telemetry-driven digital twin
  - gerçek zamanlı evidence cockpit
  - sınıf-bağımsız hedef varlıkları
  - replayable engagement evidence

## Teknik yaklaşım

### Önerilen 3D stack

Mevcut frontend React ise ana öneri:

- `three`
- `@react-three/fiber`
- `@react-three/drei`

Gerekçe:

- Web tabanlı gerçek zamanlı 3D sahne için uygundur.
- GLB/glTF asset loading yaygındır.
- React component mimarisiyle mevcut arayüze daha kolay entegre olur.
- 3D sahne read-only telemetry render katmanı olarak izole edilebilir.

Alternatif değerlendirme:

- Babylon.js digital twin/IoT için güçlüdür; fakat mevcut React uygulamaya minimal riskle eklemek için React Three Fiber daha uygun başlangıçtır.
- Foxglove benzeri robotics visualization araçları benchmark olarak incelenebilir, ancak yarışma KTR ve özel arayüz etkisi için native kokpit içinde kendi 3D panelimiz daha değerlidir.

### Asset pipeline

- Mevcut STEP/CAD model doğrudan browser’da kullanılmamalı.
- Blender/FreeCAD pipeline ile parçalı GLB üretilmeli.
- Pan/yaw, tilt/pitch, kamera gövdesi, namlu/launcher, tetik/servo görsel parçası, hedef modelleri ayrı node isimleriyle export edilmeli.
- Dosya hedefi:
  - `frontend/public/models/istiklal_c2/istiklal_c2_rigged.glb`
  - `frontend/public/models/targets/class_01.glb`
  - `frontend/public/models/targets/class_02.glb`
  - `frontend/public/models/targets/class_03.glb`
  - `frontend/public/models/targets/class_04.glb`

### Yüklenen hedef model adayları

Kullanıcı tarafından 4 adet `.model` dosyası verildi. İlk incelemeye göre bunlar 3MF XML model formatında görünüyor. Bunlar doğrudan browser 3D asset’i olarak kullanılmamalı; GLB’ye dönüştürülmeli ve sınıf etiketleri ayrıca kullanıcıdan veya dataset dokümantasyonundan alınmalı.

Şimdilik placeholder mapping:

- `object_18.model` -> `target_class_01_candidate`
- `object_19.model` -> `target_class_02_candidate`
- `object_20.model` -> `target_class_03_candidate`
- `object_21.model` -> `target_class_04_candidate`

Agent bu model dosyalarını repo dışından kopyalayacaksa lisans/etiket/ölçek/eksen bilgilerini `reports/target_model_asset_inventory.md` içinde belgelemeli.

## Mimari kontrat

Yeni backend endpointleri önerisi:

```http
GET /api/digital-twin/state
GET /api/digital-twin/assets
GET /api/digital-twin/replay/latest
GET /api/digital-twin/replay/{run_id}
POST /api/digital-twin/replay/generate
```

Örnek state:

```json
{
  "schema_version": "digital_twin_state.v1",
  "mode": "live_or_replay",
  "source": "tracker_telemetry_adapter",
  "timestamp_ms": 0,
  "device_pose": {
    "pan_deg": 0.0,
    "tilt_deg": 0.0,
    "pan_source": "pico_telemetry|tracker_estimate|fixture",
    "tilt_source": "pico_telemetry|tracker_estimate|fixture"
  },
  "camera": {
    "selected_device": "/dev/video2",
    "frame_width": 1280,
    "frame_height": 720,
    "is_real_camera": true,
    "latency_ms": 0.0
  },
  "target": {
    "detected": true,
    "track_id": "target_001",
    "class_id": "balloon|class_01|class_02|class_03|class_04",
    "class_label": "balloon_or_competition_class",
    "confidence": 0.0,
    "bbox_xyxy": [0, 0, 0, 0],
    "image_center_error_px": [0, 0],
    "estimated_scene_position": {
      "x": 0,
      "y": 0,
      "z": 0,
      "quality": "approximate_from_bbox"
    }
  },
  "tracker": {
    "state": "idle|tracking|lost|engaging|blocked",
    "tracking_enabled": false,
    "pid_error": [0, 0]
  },
  "engagement": {
    "fire_allowed": false,
    "fire_blocked_reason": "no_target|safety|e_stop|not_armed|competition_blocker",
    "last_fire_event": null,
    "target_loss_after_engagement": false
  },
  "safety": {
    "e_stop": false,
    "fire_policy": "NO_FIRE|FIRE_ALLOWED",
    "hardware_enabled": false,
    "physical_command_enabled": false,
    "digital_twin_read_only": true
  }
}
```

## Frontend UI hedefi

Mevcut kokpit “debug ağırlıklı” görünüyor. Yeni düzen şöyle olmalı:

1. Sol ana panel:
   - canlı kamera görüntüsü
   - hedef bbox
   - tracker overlay
   - latency mini bar

2. Sağ ana panel:
   - 3D digital twin
   - pan/tilt görsel yönelim
   - target projection
   - fire/engagement visual event
   - safety lock overlay

3. Alt timeline:
   - detection
   - track acquired
   - pan/tilt updates
   - fire blocked / fire event
   - target lost
   - operator action
   - E-stop

4. Sağ küçük health rail:
   - Kamera
   - Pico
   - YOLO
   - Tracker
   - Serial
   - Safety
   - Queue

3D sahne:

- Sadece gerçek telemetry/replay state’i render eder.
- OrbitControls default olarak kapalı veya sınırlı olmalı; operatör görünümü bozulmamalı.
- Debug modda serbest orbit açılabilir.
- Model üzerinde pan/tilt eksenleri ve center line görünmeli.
- Hedefin tahmini sanal pozisyonu “approximate” badge ile gösterilmeli.
- “Görsel temsil; angajman kararı değildir” boundary metni KTR export’a yazılmalı.

## Fazlar

### Faz 31 — Digital Twin Contract + Asset Inventory

Amaç: Kodlamadan önce veri kontratı ve asset envanterini sabitle.

Yapılacaklar:

- `reports/digital_twin_state_contract.json`
- `reports/digital_twin_event_contract.md`
- `reports/target_model_asset_inventory.md`
- `.model` dosyalarının format/ölçek/etiket envanteri
- frontend model path convention
- backend state adapter taslağı

DoD:

- Mevcut tracker kodu değişmemiş olmalı.
- Testler geçmeli.
- KTR’ye “Digital Twin Interface Contract” bölümü export edilmeli.
- Screenshot gerekmeyebilir; kontrat ve rapor yeterli.

### Faz 32 — Read-only 3D Viewer MVP

Amaç: Digital twin modelini frontend’de telemetry fixture ile döndürmek.

Yapılacaklar:

- React Three Fiber viewer component
- Mock/fixture state ile pan/tilt/servo visual animation
- Digital twin panel feature flag
- 3D render failure fallback
- `/api/digital-twin/state` fixture/live adapter endpoint
- No command authority guard

DoD:

- Eski kokpit bozulmadan çalışmalı.
- Digital twin kapatılabilir olmalı.
- 3D viewer hiçbir command endpoint çağırmamalı.
- Unit/e2e test: 3D panel state render eder, command üretmez.

### Faz 33 — Target Projection + 4 Class Asset Mapping

Amaç: Kamera bbox/class bilgisini 3D sanal hedef temsilinde göstermek.

Yapılacaklar:

- `class_id -> model_path` mapping
- balloon fallback model
- 4 yarışma sınıfı için placeholder asset support
- bbox center/error -> approximate scene position mapper
- UI’da confidence, class label, estimated position quality
- Model conversion pipeline raporu

DoD:

- YOLO model değişse bile UI class-agnostic çalışmalı.
- Sınıf etiketi bilinmeyen model “unlabeled_asset” olarak görünmeli.
- KTR export: target class interface + model asset pipeline.

### Faz 34 — Engagement Timeline + Replay Mode

Amaç: Gerçek koşu veya fixture koşusunu replay edilebilir hale getirmek.

Yapılacaklar:

- Event log -> replay state stream
- Timeline scrubber
- detection/tracking/fire_blocked/fire_event/target_lost events
- target disappeared after engagement candidate logic
- replay export:
  - `digital_twin_replay_summary.md`
  - `digital_twin_replay_events.json`
  - `engagement_timeline.md`

DoD:

- Replay, live tracker’dan bağımsız çalışmalı.
- Replay dosyası KTR test kanıtı olarak kullanılmalı.
- “Hit confirmed” gibi kesin iddia yoksa “target disappearance after engagement candidate” denmeli.

### Faz 35 — KTR Evidence Export + Report Integration

Amaç: Yapılan işi KTR puan kalemlerine bağlayan export üretmek.

Yapılacaklar:

- Reports/KTR export’a yeni dosyalar:
  - `digital_twin_architecture.md`
  - `digital_twin_interface_contract.json`
  - `digital_twin_replay_summary.md`
  - `target_model_asset_inventory.md`
  - `digital_twin_safety_boundary.md`
  - `digital_twin_test_matrix.md`
- KTR 4.2/4.3/4.4/5/6/9 bölümleri için metin taslakları
- Screenshot klasörü
- Acceptance summary

DoD:

- KTR export digital twin’i “özgünlük + arayüz + test + güvenlik” olarak net bağlamalı.
- Sayfa limitine uygun kısa ve yoğun metin üretmeli.
- Mevcut sistem davranışı bozulmamış olmalı.

## Test stratejisi

Her faz sonunda:

- `uv run pytest -q`
- `pnpm --dir frontend typecheck`
- `pnpm --dir frontend build`
- `python3 scripts/check_release.py`
- `bash -n release/linux/start_istiklal_c2.sh`
- `bash -n start_linux.sh`

Ek testler:

- Digital twin hiçbir `fire`, `motor`, `serial TX`, `STEP/DIR`, `GPIO`, `PWM`, `servo command` endpointini çağırmıyor.
- Feature flag off iken eski UI aynı.
- Fixture telemetry ile viewer deterministic render ediyor.
- Asset yoksa UI crash olmuyor; placeholder model gösteriyor.
- Replay dosyası parse ediliyor.
- KTR export dosyaları oluşturuluyor.

## Git/rapor standardı

Her faz sonunda:

- Commit al.
- Rapor yaz:
  - `reports/058_phase31_digital_twin_contract.md` gibi sırayı mevcut repo standardına göre devam ettir.
- Screenshot varsa:
  - `reports/screenshots/phase31_.../`
- `git status clean` ile bitir.

## Agent çıktısı beklenen format

Agent her faz sonunda şunu yazmalı:

- Yapılanlar
- Değişen dosyalar
- Test/build sonuçları
- KTR’ye katkı
- Safety boundary
- Bilinen eksikler
- Sonraki faz önerisi
- Commit hash
