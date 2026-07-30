# 03 — Faz 31-35 Uygulama Planı

## Genel strateji

Cihaz şu an her zaman yanımızda olmayabilir. Bu yüzden canlı sistem testine bağımlı olmayan, ama gerçek cihaz geldiğinde doğrudan acceptance’a girecek bir yapı kurulmalı.

En önemli karar:

> Önce digital twin kontratı ve read-only viewer yapılacak. Sonra hedef projection/replay/KTR export eklenecek. Fiziksel hareket veya tracker davranışı bu fazlarda değiştirilmemeli.

## Faz 31 — Digital Twin Contract + Asset Inventory

### Amaç

Digital twin için veri kontratını, hedef model envanterini ve KTR bağlamını netleştirmek.

### Görevler

- `reports/digital_twin_state_contract.json` oluştur.
- `reports/digital_twin_event_contract.md` oluştur.
- `reports/target_model_asset_inventory.md` oluştur.
- `reports/digital_twin_ktr_mapping.md` oluştur.
- 4 adet `.model` dosyasının:
  - format
  - boyut
  - sha256
  - placeholder class mapping
  - conversion ihtiyacı
  envanterini çıkar.
- `modelRegistry.ts` veya backend asset registry taslağı oluştur.

### Kod sınırı

- Mevcut tracker/vision/Pico command path’e dokunma.
- Sadece rapor, contract, registry ve feature flag ekle.

### Acceptance

- Testler geçmeli.
- `digital_twin_read_only=true` kontratta yer almalı.
- KTR mapping dosyası oluşturulmalı.

### Beklenen commit

`feat: add digital twin contract and asset inventory`

---

## Faz 32 — Read-only 3D Viewer MVP

### Amaç

3D cihaz modelini fixture telemetry ile döndürmek. Live tracker’a bağlı olmasa bile UI çalışmalı.

### Görevler

- React Three Fiber bağımlılıklarını ekle.
- `DigitalTwinPanel.tsx` oluştur.
- `DigitalTwinScene.tsx` oluştur.
- Fixture state ile:
  - pan_deg
  - tilt_deg
  - servo_angle
  - target detected/not detected
  göster.
- `/api/digital-twin/state` endpointini ekle.
- Feature flag:
  - `DIGITAL_TWIN_ENABLED`
  - default: false veya safe default
- Error boundary ekle.
- Eski kokpit fallback korunsun.

### Acceptance

- 3D panel command endpoint çağırmıyor.
- Feature flag off iken eski UI değişmiyor.
- Feature flag on iken 3D viewer fixture state ile render ediyor.
- Build/typecheck/test geçiyor.

### Beklenen commit

`feat: add read-only digital twin viewer`

---

## Faz 33 — Target Projection + Competition Class Asset Layer

### Amaç

YOLO/detection çıktısını sınıf-bağımsız hedef model temsilinde göstermek.

### Görevler

- `TargetClassRegistry` oluştur.
- `balloon` ve `class_01..class_04` destekle.
- Yüklenen `.model` dosyaları için GLB conversion TODO ve asset registry ekle.
- Target bbox -> approximate 3D scene mapper ekle.
- UI’da:
  - class label
  - confidence
  - bbox center error
  - estimated position quality
  göster.
- Asset yoksa placeholder model.

### Acceptance

- YOLO modeli balondan yarışma sınıflarına değişse bile UI contract kırılmıyor.
- Unknown class fallback çalışıyor.
- KTR export hedef sınıf arayüzünü açıklıyor.

### Beklenen commit

`feat: add target projection and class asset registry`

---

## Faz 34 — Replay Timeline + Engagement Evidence

### Amaç

Canlı koşu veya fixture koşusunu digital twin üzerinde tekrar oynatmak.

### Görevler

- Event stream formatı:
  - target_detected
  - target_lost
  - tracking_started
  - tracking_stopped
  - pose_updated
  - fire_blocked
  - fire_event
  - e_stop
- Replay builder.
- Timeline scrubber.
- KTR için export:
  - `digital_twin_replay_summary.md`
  - `digital_twin_replay_events.json`
  - `engagement_timeline.md`
- “target_lost_after_engagement_candidate” mantığı.
- Kesin imha yoksa “candidate” ifadesi kullanılmalı.

### Acceptance

- Fixture replay deterministik.
- Timeline ileri/geri sarılabiliyor.
- Digital twin replay live tracker’a bağlı değil.
- KTR test kanıtı üretiliyor.

### Beklenen commit

`feat: add digital twin replay evidence timeline`

---

## Faz 35 — KTR Evidence Export + Cockpit Polish

### Amaç

KTR puan kalemleri için raporlanabilir, görsel ve teknik olarak güçlü çıktı üretmek.

### Görevler

- Reports/KTR export’a ekle:
  - `digital_twin_architecture.md`
  - `digital_twin_interface_contract.json`
  - `digital_twin_safety_boundary.md`
  - `digital_twin_test_matrix.md`
  - `target_model_asset_inventory.md`
  - `digital_twin_replay_summary.md`
- Kokpit polish:
  - daha az badge
  - net safety banner
  - 3D model + camera side-by-side
  - health rail sadeleştirme
  - “why blocked?” açıklama kartı
- KTR 4.2/4.3/4.4/5/6/9 metin taslakları.

### Acceptance

- KTR export dosyaları oluşuyor.
- UI screenshotları net ve profesyonel.
- Eski tracker davranışı bozulmamış.
- Build/test geçiyor.

### Beklenen commit

`feat: add digital twin KTR evidence export`

---

## Faz 36 ve sonrası — Cihazlı acceptance

Bu fazlar cihaz yanımızdayken yapılmalı.

### Hardware acceptance

- USB kamera seçimi gerçek görüntüyle doğrulanır.
- Pico port + telemetry doğrulanır.
- Pan/tilt telemetry digital twin ile karşılaştırılır.
- Direction calibration gerçek hareketle doğrulanır.
- Tracker canlı balon ile tekrar doğrulanır.
- Fire/tetik testleri yalnızca yarışma güvenlik prosedürleri ve mekanik güvenli ortam sağlandıktan sonra yapılır.

### Cihaz yokken yapılmayacaklar

- Motor hareket testi
- Tetik/servo gerçek hareket testi
- Fire-allowed live test
- Competition-ready claim

## Faz sonu rapor formatı

Her faz sonunda agent şunu yazmalı:

```text
Faz XX tamamlandı.

Commit:
...

Eklenenler:
...

KTR katkısı:
...

Doğrulama:
- uv run pytest -q
- pnpm --dir frontend typecheck
- pnpm --dir frontend build
- python3 scripts/check_release.py
- bash -n release/linux/start_istiklal_c2.sh
- bash -n start_linux.sh

Safety boundary:
digital_twin_read_only=true
physical_command_path unchanged
no new command authority added

Known limitations:
...

Git status: clean.
```
