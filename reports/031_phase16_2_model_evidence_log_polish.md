# Ara Task 16.2 - Model UI Evidence and Log Summary Hardening

## Yapılanlar
- Model event payload ve log summary alanları jüri/demo okunurluğu için netleştirildi.
- `model.package_validation_passed`, `model.activated`, `model.test_completed`, `model.runtime_recommended_applied` ve `model.deactivated` eventleri artık generic `telemetry update` olarak görünmüyor.
- Model event payloadlarına `summary`, `package_kind`, `production_ready`, `competition_ready` ve `no_physical_command_generated` kanıt alanları eklendi.
- Models ekranındaki Active Model ve Safety Evidence kartları stacked/wrap layout’a alındı.
- First Run, Self-Test ve Dashboard üzerinde release candidate ile competition rehearsal ayrımı açıklama metinleriyle güçlendirildi.
- Reports export detail ve KTR metni test adapter/fixture model paketinin yarışma modeli olmadığını daha açık gösteriyor.
- Boş/korrupt active model state dosyası için model registry güvenli fallback eklenerek `/api/models/active` 500 hatası engellendi.

## Model log summary sonucu
- `model.package_validation_passed`: “Model package schema validation passed.”
- `model.activated`: fixture/test adapter için “Test adapter activated; production readiness remains blocked.”
- `model.test_completed`: “Model dry-run test completed; no physical command generated.”
- `model.runtime_recommended_applied`: “Recommended vision runtime settings applied; safety state unchanged.”
- `model.deactivated`: “Active model deactivated; vision falls back to no production model.”

## Models UI sonucu
- Active Model kartında şu alanlar görünür:
  - `active_model_id`
  - `package_id`
  - `package_kind`
  - `adapter_mode`
  - `package_schema_status`
  - `runtime_status`
  - `production_status`
  - `competition_status`
  - `production_ready=false`
  - `competition_ready=false`
- Uzun path/id değerleri artık satır içinde kırılıyor ve kart dışına taşmıyor.

## Safety Evidence sonucu
- Models ekranındaki Safety Evidence kartı stacked row formatında şu değerleri açık gösteriyor:
  - `advisory_only=true`
  - `dry_run=true`
  - `physical_command_enabled=false`
  - `no_physical_command_generated=true`
  - `production_ready=false`
  - `competition_ready=false`

## First Run / Self-Test açıklama sonucu
- First Run’da şu açıklama eklendi:
  “Release candidate profili, yazılımın taşınabilir/demo çalışmasını doğrular; production YOLO ve gerçek Pico telemetry yarışma provası için ayrıca gerekir.”
- Self-Test’te release candidate ve competition rehearsal farkı açık gösteriliyor.
- Dashboard’da “Release profile passed does not mean competition rehearsal ready.” metni eklendi.

## Vision runtime sonucu
- Fixture/test adapter aktifken:
  - `effective_adapter=test_adapter`
  - `production_yolo_loaded=false`
  - `runtime_source=fixture_or_test_adapter`
  - `TEST ADAPTER ACTIVE, NOT PRODUCTION YOLO` badge’i görünüyor.
- `ultralytics_yolo` yalnızca production YOLO gerçekten aktif olduğunda effective adapter olarak gösterilecek.

## Reports/KTR sonucu
- Reports export detail içinde active model summary şu değerleri açık gösteriyor:
  - Active model: fixture/test adapter
  - Package kind: fixture/test_adapter
  - Production model: not loaded / false
  - Production ready: false
  - Competition ready: false
  - Advisory only: true
  - No physical command generated: true
- KTR metnine şu cümle eklendi:
  “Test adaptörü veya fixture model paketi, yalnızca arayüz ve veri akışı doğrulaması için kullanılır; yarışma tespit modeli olarak değerlendirilmez.”
- Mevcut güvenlik cümlesi korundu:
  “Görüntü işleme modeli, komuta kontrol yazılımına yalnızca sınıf, güven skoru, konum ve zaman bilgisi içeren algılama metadatası sağlar; bu metadata tek başına fiziksel atış veya hareket komutu üretmez.”

## Test/build sonuçları
- `uv run pytest -q`: 202 passed.
- `pnpm typecheck`: geçti.
- `pnpm build`: geçti.
- `python3 scripts/check_release.py`: geçti.
- `bash -n release/linux/start_istiklal_c2.sh`: geçti.
- `bash -n start_linux.sh`: geçti.
- Manual smoke geçti:
  - `/`
  - `/models`
  - `/vision`
  - `/dashboard`
  - `/first-run`
  - `/self-test`
  - `/reports`
  - `/interfaces`
  - `/logs`
  - `/api/models/active`
  - `/api/vision/runtime/status`
  - `/api/release/status`

## Screenshot yolları
- `reports/screenshots/phase16_2_model_evidence_log_polish/01_models_active_model_values_visible.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/02_models_safety_evidence_values_visible.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/03_logs_model_human_readable_summaries.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/04_first_run_release_vs_competition_explanation.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/05_self_test_release_competition_warning_explanation.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/06_vision_runtime_fixture_adapter_consistency.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/07_reports_active_model_semantic_export_detail.png`
- `reports/screenshots/phase16_2_model_evidence_log_polish/08_ktr_test_adapter_not_competition_text.png`

## Commit hashleri
- Başlangıç commit'i: `5890b97 fix: clarify model readiness semantics and adapter state`
- Bu task commit'i final yanıtta bildirildi.

## Safety invariant sonucu
- Korundu: `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`.
- Model import/validate/activate/test/benchmark/runtime apply/report export işlemleri fiziksel komut üretmiyor.

## Bilinen eksikler
- Production YOLO modeli hâlâ görüntü işleme ekibinden bekleniyor.
- Gerçek Pico telemetry ve gerçek kamera/probe competition rehearsal için ayrıca doğrulanmalı.

## Sonraki önerilen task
- Production model paketi geldiğinde import/validate/activate/test ve competition readiness kabul testi yapılmalı.
- Faz 17’ye geçilmedi.
