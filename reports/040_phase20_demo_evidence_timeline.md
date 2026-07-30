# Phase 20 - End-to-End Demo Evidence Timeline

## Yapılanlar

- Demo Evidence Timeline backend servisi eklendi.
- `/api/demo/timeline`, `/api/demo/run`, `/api/demo/latest` ve `/api/demo/readiness` endpointleri eklendi.
- Demo run akışı safety snapshot, First Run/profile state, vision metadata, Data Lab session, replay, annotation review, dataset health ve report export kanıtlarını tek timeline içinde topluyor.
- `/demo` ekranı eklendi ve sidebar Operations grubuna bağlandı.
- Dashboard’a Demo Evidence özeti eklendi.
- Data Lab içine Demo Timeline tabı eklendi.
- Reports export detail içine `demo_timeline.json`, `demo_timeline.md`, `demo_readiness_summary.md` ve `demo_runbook.md` görünürlüğü eklendi.
- KTR 4.3 interface metnine “Demo Evidence Timeline Arayüzü” bölümü eklendi.
- Logs summary metinleri `demo.timeline_generated`, `demo.run_completed` ve `demo.readiness_checked` için operatör-dostu hale getirildi.

## Demo Timeline Özeti

Timeline event alanları:

- `event_id`
- `step`
- `title`
- `status`
- `source`
- `timestamp`
- `summary`
- `evidence_ref`
- `advisory_only=true`
- `no_physical_command_generated=true`

Demo run adımları:

- System safety lock
- First Run / profile evaluation
- Vision evidence
- Data Lab session
- Replay
- Annotation review
- Dataset health
- Report export
- Final demo verdict

## Final Demo Verdict

Beklenen ayrım korunuyor:

- `release_demo_ready=true` olabilir.
- `competition_ready=false` kalır.
- `dataset_ready_for_training=false` kalır.

Competition readiness için production YOLO modeli, gerçek kamera kanıtı, Pico telemetry verification ve self-test gerekir. Mock/surrogate evidence yalnızca demo/release evidence olarak değerlendirilir.

## Reports/KTR Export

KTR/report export içine eklenen dosyalar:

- `demo_timeline.json`
- `demo_timeline.md`
- `demo_readiness_summary.md`
- `demo_runbook.md`

Data Lab replay/annotation dosyalarıyla birlikte rapor paketinde görünür durumdadır.

## Logs

Yeni event summary örnekleri:

- `demo.timeline_generated`: Demo evidence timeline generated; steps=...; no physical command generated.
- `demo.run_completed`: End-to-end demo run completed; release_demo_ready=...; competition_ready=false.
- `demo.readiness_checked`: Demo readiness checked; blockers=...; no physical command generated.

Generic `telemetry update` kullanılmadı.

## Test/Build Sonuçları

- `uv run pytest -q`: geçti, 227 passed.
- `pnpm typecheck`: geçti.
- `pnpm build`: geçti.
- `python3 scripts/check_release.py`: geçti.
- `bash -n release/linux/start_istiklal_c2.sh`: geçti.
- `bash -n start_linux.sh`: geçti.

## Manual Smoke

Port `8001` üzerinde kontrol edildi:

- `/demo`: 200
- `/dashboard`: 200
- `/data-lab`: 200
- `/reports`: 200
- `/interfaces`: 200
- `/logs`: 200
- `/api/demo/timeline`: 200
- `/api/demo/run`: 200
- `/api/demo/latest`: 200
- `/api/demo/readiness`: 200
- `/api/data-lab/dataset-health`: 200
- `/api/release/status`: 200

## Screenshot Yolları

- `reports/screenshots/phase20_demo_evidence_timeline/01_demo_timeline_overview.png`
- `reports/screenshots/phase20_demo_evidence_timeline/02_dashboard_demo_evidence_summary.png`
- `reports/screenshots/phase20_demo_evidence_timeline/03_data_lab_demo_timeline_tab.png`
- `reports/screenshots/phase20_demo_evidence_timeline/04_reports_demo_timeline_files.png`
- `reports/screenshots/phase20_demo_evidence_timeline/05_interfaces_demo_timeline_section.png`
- `reports/screenshots/phase20_demo_evidence_timeline/06_logs_demo_events.png`
- `reports/screenshots/phase20_demo_evidence_timeline/07_demo_readiness_endpoint.png`
- `reports/screenshots/phase20_demo_evidence_timeline/08_safety_invariant_demo_flow.png`

## Safety Invariant Kanıtı

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Demo timeline, Data Lab, report export ve log akışları yalnızca demo/evidence/replay/report/advisory amaçlıdır. Motor, servo, fire, GPIO, STEP/DIR/PWM veya hardware enable yolu eklenmedi.

## Bilinen Eksikler

- Timeline görseli şu an evidence kartları ve API verileriyle sınırlı; gelişmiş timeline animasyonu yok.
- Competition readiness bilinçli olarak false: production YOLO, gerçek kamera evidence, Pico telemetry ve saha self-test eksik.
- Dataset training readiness false: gerçek veri ve annotation kalitesi yeterli değil.

## Sonraki Önerilen Task

Faz 21 öncesi istenirse demo timeline için operator-facing print/export polish veya timeline filtreleri eklenebilir. Faz 21’e geçilmedi.
