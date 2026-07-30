# Ara Task 16.1 - Model Semantics & Competition Readiness Polish

## Yapılanlar
- Model paket doğrulama, runtime doğrulama, aktif model durumu, production readiness ve competition readiness kavramları backend response'larında ayrıştırıldı.
- Fixture/test package doğrulaması `PACKAGE VALID` kalırken `production_ready=false` ve `competition_ready=false` olacak şekilde netleştirildi.
- OpenCV/fixture test adapter aktifken Vision runtime `ultralytics_yolo` göstermeyecek şekilde düzeltildi.
- Models, Vision, Dashboard, Devices ve Reports ekranlarında test adapter / production model ayrımı görünür hale getirildi.
- First Run ve Self-Test model kontrolleri release candidate ile competition rehearsal ayrımını açık anlatacak şekilde güncellendi.
- KTR 4.3 model paketi arayüz metni test adaptörü, production model paketi, runtime ayarları ve safety sınırı ayrımıyla güçlendirildi.
- Eski kayıtlar için `body`/`balloon` class mapping rollerini `body_target`/`balloon_target` formatına normalleyen geriye dönük schema uyumluluğu eklendi.

## Düzeltilen terminology/statü problemleri
- `VALIDATION PASSED` yerine UI'da `PACKAGE VALID` kullanıldı.
- Fixture/test adapter için `TEST ADAPTER ACTIVE` ve `FIXTURE / TEST ONLY` badge'leri eklendi.
- Production model için ayrı `PRODUCTION ACTIVE` / `PRODUCTION MODEL` gösterimi korundu.
- `package_schema_validation`, `runtime_validation`, `production_readiness` ve `competition_readiness` ayrı alanlar olarak gösterildi.
- Reports export detail içinde `Active model: fixture/test adapter`, `Production model: not loaded`, `Competition readiness: blocked/limited_demo_only`, `No physical command: true` görünür hale getirildi.

## Build label sonucu
- Bu hotfix build label kapsamını değiştirmedi; mevcut Phase 16 release/build davranışı korunuyor.

## Verification semantics sonucu
- Fixture/test package schema validation geçebilir, ancak production readiness geçemez.
- Competition readiness production model, valid class mapping, model dry-run test, real camera/probe ve Pico telemetry olmadan geçmez.
- `GET /api/models/active` artık `package_kind`, `adapter_mode`, `package_schema_valid`, `runtime_valid`, `class_mapping_valid`, `production_model`, `production_ready`, `competition_ready`, `warnings` ve `blockers` alanlarını net döndürüyor.
- `GET /api/vision/runtime/status` artık `selected_adapter`, `effective_adapter`, `production_yolo_loaded`, `test_adapter_active`, `model_package_id`, `runtime_source` ve `advisory_only` alanlarını net döndürüyor.

## Vision model panel sonucu
- Production YOLO modeli yokken büyük uyarı gösteriliyor:
  “Production YOLO modeli yüklü değil. OpenCV daire algılayıcı yalnızca test adaptörüdür; yarışma modeli değildir.”
- Active Model Panel dar kolonlarda class listelerini ayrı, kırılabilir satırlarda gösteriyor.
- Runtime Compatibility alanı önerilen model parametreleri ile mevcut runtime adapter/parametrelerini ayrıştırıyor.

## Logs layout sonucu
- Model event summary metinleri daha açıklayıcı hale getirildi:
  - `model.package_validation_passed`: Model package schema validation passed.
  - `model.activated`: Test adapter activated; production readiness remains blocked.
  - `model.test_completed`: Model dry-run test completed; no physical command generated.
  - `model.runtime_recommended_applied`: Recommended vision runtime settings applied; safety state unchanged.
- Logs ekranında model filtre screenshot'ı üretildi.

## KTR polish sonucu
- “Görüntü İşleme Model Paketi Arayüzü” bölümü test adaptörü ve production model paketini ayıracak şekilde güncellendi.
- Korunan kritik KTR cümlesi:
  “Görüntü işleme modeli, komuta kontrol yazılımına yalnızca sınıf, güven skoru, konum ve zaman bilgisi içeren algılama metadatası sağlar; bu metadata tek başına fiziksel atış veya hareket komutu üretmez.”

## Test/build sonuçları
- `uv run pytest -q`: 201 passed.
- `pnpm typecheck`: geçti.
- `pnpm build`: geçti.
- `python3 scripts/check_release.py`: geçti.
- `bash -n release/linux/start_istiklal_c2.sh`: geçti.
- `bash -n start_linux.sh`: geçti.
- Manual smoke geçti:
  - `/`
  - `/models`
  - `/vision`
  - `/devices`
  - `/first-run`
  - `/self-test`
  - `/reports`
  - `/interfaces`
  - `/logs`
  - `/api/models/active`
  - `/api/models/packages`
  - `/api/vision/runtime/status`
  - `/api/release/status`
  - `/api/release/preflight`

## Screenshot yolları
- `reports/screenshots/phase16_1_model_semantic_polish/01_models_fixture_not_production.png`
- `reports/screenshots/phase16_1_model_semantic_polish/02_active_model_semantic_fields.png`
- `reports/screenshots/phase16_1_model_semantic_polish/03_class_mapping_clean_roles.png`
- `reports/screenshots/phase16_1_model_semantic_polish/04_vision_adapter_consistency.png`
- `reports/screenshots/phase16_1_model_semantic_polish/05_dashboard_release_vs_competition_blockers.png`
- `reports/screenshots/phase16_1_model_semantic_polish/06_first_run_model_semantics.png`
- `reports/screenshots/phase16_1_model_semantic_polish/07_self_test_model_warnings.png`
- `reports/screenshots/phase16_1_model_semantic_polish/08_reports_model_semantic_export.png`
- `reports/screenshots/phase16_1_model_semantic_polish/09_ktr_model_interface_semantic_text.png`
- `reports/screenshots/phase16_1_model_semantic_polish/10_logs_model_semantic_events.png`

## Commit hashleri
- Başlangıç commit'i: `4e4f1a8 feat: add vision model handoff and validation workflow`
- Bu task commit'i final yanıtta bildirildi.

## Bilinen eksikler
- Gerçek production YOLO modeli henüz sağlanmadığı için competition rehearsal readiness bilinçli olarak blocked/limited demo durumunda kalıyor.
- Gerçek Pico telemetry doğrulaması bu taskta yapılmadı.
- Screenshotlar Linux ortamında üretildi; Windows host üzerinde launcher gerçek çalışma kabulü ayrıca yapılmalı.

## Sonraki önerilen task
- Görüntü işleme ekibi production model paketini verdiğinde kod değişmeden import/validate/activate/test akışı gerçek modelle çalıştırılmalı.
- Faz 17'ye geçilmedi.
