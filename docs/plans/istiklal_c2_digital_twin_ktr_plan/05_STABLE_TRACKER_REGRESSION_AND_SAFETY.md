# 05 — Stable Tracker Regression ve Safety Planı

## Amaç

Mevcut sistem gerçek cihazla balonları tespit edip takip edebiliyor. Bu kabiliyet projenin en değerli çalışan kısmıdır. Digital twin dönüşümü bu sistemi bozarsa kazanacağımız arayüz değeri, kaybettiğimiz operasyonel kabiliyeti telafi etmez.

Bu yüzden ana hedef:

> Digital twin ekle, mevcut tracker’ı bozma.

## Bozulmaması gereken davranışlar

- USB kamera seçimi
- Kamera frame capture
- YOLO/detection pipeline
- Balon/target bbox üretimi
- Tracker state
- PID/direction calibration semantics
- Pico discovery
- Serial/Pico command path
- Fire block/fire allowed logic
- E-stop
- Manual/auto mode ayrımı
- Queue/ACK monitoring
- Reports/KTR export

## Regression yaklaşımı

### 1. Contract snapshot

Mevcut endpoint response’ları snapshotlanmalı:

- `/api/status`
- `/api/vision/...`
- `/api/demo/...`
- `/api/calibration/...`
- `/api/pico/...`
- live cockpit state endpointleri

Agent endpoint isimlerini repo içinden doğrulamalı. Bu listedeki endpointler tahminidir.

### 2. Fixture replay

Gerçek cihaz yokken kullanılacak fixture:

```text
fixtures/digital_twin/
  balloon_tracking_run_001.jsonl
  target_lost_after_engagement_candidate.jsonl
  camera_only_no_pico.jsonl
  pico_connected_no_target.jsonl
  safety_blocked_fire.jsonl
```

### 3. Golden UI states

Digital twin gelmeden önceki UI davranışları korunmalı:

- Kokpit açılıyor.
- Kamera paneli render ediyor.
- Debug sayfası çalışıyor.
- Setup sayfası çalışıyor.
- Kanıt/rapor sayfası çalışıyor.

### 4. Feature flag

Digital twin default olarak kontrollü açılmalı.

Örnek:

```env
DIGITAL_TWIN_ENABLED=false
DIGITAL_TWIN_REPLAY_ENABLED=true
DIGITAL_TWIN_COMMAND_AUTHORITY=false
```

Kesin kural:

- `DIGITAL_TWIN_COMMAND_AUTHORITY` her zaman false kalmalı.
- Bu flag true yapılabilir bir özellik gibi tasarlanmamalı.

## Safety negative tests

### Yasak string / yasak çağrı taraması

Digital twin componentleri şunları içermemeli:

- `fire`
- `trigger`
- `servo command`
- `serial.write`
- `GPIO`
- `PWM`
- `STEP`
- `DIR`
- `hardware_enable`

Not: Görsel metin olarak `fire_blocked_reason` olabilir. Test çağrı/komut üretimini yakalamalı; her string yasaklanırsa false positive çıkar.

### Endpoint call guard

3D viewer şunları çağırmamalı:

- manual fire endpointleri
- motor jog endpointleri
- servo/tetik endpointleri
- hardware enable endpointleri
- raw serial TX endpointleri

### Read-only adapter

Digital twin sadece şu tür endpointleri çağırmalı:

- state
- assets
- replay
- evidence
- health read

## Cihaz yokken yapılacak acceptance

- Fixture state viewer render
- Replay timeline render
- Asset fallback render
- KTR export
- Build/test
- Endpoint smoke
- Snapshot diff

## Cihaz varken yapılacak acceptance

Bu ayrı fazdır; simülasyon fazlarıyla karıştırılmamalı.

- USB kamera gerçek görüntü
- Pico connected
- Telemetry read
- Pan/tilt state digital twin uyumu
- Direction calibration physical confirmation
- Tracker live target confirmation
- Emergency stop confirmation
- Fire/tetik testi yalnızca güvenli yarışma prosedürüyle

## KTR güvenlik dili

KTR’de şu ifade kullanılmalı:

> Dijital ikiz katmanı, fiziksel komut üretmeyen salt-okunur bir gözlem ve kanıt üretim katmanı olarak tasarlanmıştır. Motor, servo ve angajman komutları mevcut güvenlik kapıları ve kontrol mantığı üzerinden yürütülür. Böylece arayüz zenginleşirken komut yetkisi dağılmaz ve güvenlik sınırı korunur.

## Agent check-list

Her commit öncesi:

- [ ] Mevcut tracker dosyalarında gereksiz refactor yok.
- [ ] Feature flag kapalıyken eski UI çalışıyor.
- [ ] Digital twin command endpoint çağırmıyor.
- [ ] Testler geçiyor.
- [ ] Build geçiyor.
- [ ] KTR export oluşuyor.
- [ ] Safety boundary raporu var.
- [ ] Git status clean.
