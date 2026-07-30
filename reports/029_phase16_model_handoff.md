# Faz 16 - Vision Model Handoff & Plug-and-Play Integration Raporu

## Yapılanlar

- Görüntü işleme ekibinin teslim edeceği model paketi için `metadata.json`, `classes.json/classes.yaml`, `thresholds.json`, model dosyası ve checksum temelli paket sözleşmesi eklendi.
- `/api/models/packages/*` endpoint ailesi eklendi: import, validate, activate, deactivate, dry-run test, benchmark ve recommended runtime settings uygulama.
- Model paketi import/validate/activate akışı mevcut model registry, Vision Runtime, First Run, Self-Test, Reports/KTR ve Interface Inventory ile entegre edildi.
- `/models` operatör ekranı eklendi: package inventory, import, active model, class mapping review, runtime compatibility ve safety evidence panelleri.
- Vision ve Devices ekranlarındaki active model/model binding bilgileri yeni paket sisteminden beslenir hale getirildi.
- KTR 4.3 export içine “Görüntü İşleme Model Paketi Arayüzü” bölümü ve model package JSON özetleri eklendi.
- OpenCV test adapter fixture paketi eklendi; üretim modeli olarak işaretlenmedi ve competition readiness blocker davranışı korundu.

## Oluşturulan/değiştirilen dosyalar

- Backend: `backend/app/schemas/model_package.py`, `backend/app/services/model_package_service.py`, `backend/app/api/models.py`
- Entegrasyonlar: `first_run_service.py`, `self_test_service.py`, `vision_runtime_settings_service.py`, `report_export_service.py`, `interface_inventory_service.py`, `release_service.py`
- Frontend: `frontend/src/views/ModelsView.vue`, model package API/store/type dosyaları, `VisionView.vue`, `DevicesView.vue`, `ReportsView.vue`, router/sidebar
- Test fixture: `backend/tests/fixtures/model_packages/opencv_test_adapter_package/`
- Test: `backend/tests/test_phase16_model_handoff.py`
- Dokümantasyon: `docs/model_handoff_phase16.md`
- Screenshot script: `scripts/capture_phase16_screenshots.py`

## Test/build sonuçları

- `uv run pytest -q`: geçti, 198 test.
- `pnpm typecheck`: geçti.
- `pnpm build`: geçti.
- `python3 scripts/check_release.py`: geçti, Phase 16 release check.
- `bash -n release/linux/start_istiklal_c2.sh && bash -n start_linux.sh`: geçti.
- Manual smoke: `/`, `/models`, `/vision`, `/devices`, `/first-run`, `/self-test`, `/interfaces`, `/reports`, `/logs`, `/api/models/packages`, `/api/models/active`, `/api/vision/runtime/status`, `/api/release/status`, `/api/release/preflight` 200 döndü.

## Screenshot klasörü

`reports/screenshots/phase16_model_handoff/`

- `01_models_inventory_empty_or_fixture.png`
- `02_model_package_import_validation.png`
- `03_active_model_panel_validation.png`
- `04_class_mapping_review.png`
- `05_vision_runtime_recommended_settings.png`
- `06_devices_model_binding_status.png`
- `07_first_run_model_profile_checks.png`
- `08_self_test_model_checks.png`
- `09_ktr_model_interface_section.png`
- `10_reports_model_export_detail.png`
- `11_logs_model_events.png`

## Safety invariant sonucu

Korundu:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

Model import, validation, activation, dry-run test, benchmark, recommended settings apply ve report export akışlarında `no_physical_command_generated=true` kanıtı korunuyor.

## Bilinen eksikler

- Production YOLO modeli henüz teslim edilmedi; fixture/test package üretim modeli sayılmıyor.
- Gerçek Ultralytics/ONNX inference load performansı bu fazda çalıştırılmadı; görüntü işleme ekibinin adapter teslimi sonrası acceptance yapılmalı.
- Windows host üzerinde launcher/model handoff akışı ayrıca denenmeli.
- `classes.yaml` dosyası kabul sözleşmesine dahil, ancak doğrulama ana kaynağı şu an `metadata.json` içindeki `class_id_to_name`.

## Commit hashleri

- Başlangıç commit: `051d737`
- Faz 16 commit: final Git commit hash görevin kapanış yanıtında verilmiştir.

## Sonraki önerilen task

Vision ekibinin gerçek model paketi geldiğinde aynı `/models` akışıyla import/validate/test acceptance yapılmalı. Faz 17’ye bu onaydan önce geçilmemeli.
