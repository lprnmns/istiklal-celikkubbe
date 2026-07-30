# Faz 14 - Field Release QA, Device Binding Profiles ve Operator Mode Hardening

## Yapılanlar

- Readiness profile sistemi First Run raporlarına eklendi.
- Device Binding Profile servisi, API endpointleri ve `/devices` UI entegrasyonu eklendi.
- Camera runtime status requested/actual/probe alanlarıyla genişletildi.
- Vision runtime preset sistemi ve active model paneli eklendi.
- Release QA servisi, endpointleri ve `scripts/check_release.py` eklendi.
- Logs ekranında kolon düzeni, truncate, timestamp ve detail action metinleri iyileştirildi.
- Dashboard release readiness ve field profile göstergeleriyle güçlendirildi.
- Interface Inventory alanları KTR için genişletildi ve OpenCV test adapter ifadesi daha net ayrıldı.
- Operator quickstart ve field release QA dokümantasyonu eklendi.

## Readiness Profile Özeti

Eklenen profiller:

- `development_ready`
- `demo_ready`
- `field_dry_run_ready`
- `hardware_telemetry_ready`
- `competition_rehearsal_ready`

Her profil ayrı checklist ve durum üretir:

- `passed`
- `warning`
- `failed`
- `blocked`

Pico yoksa `development_ready` ve `demo_ready` geçebilir; `hardware_telemetry_ready` blocked olur. Production YOLO modeli yoksa demo akışı test adapter ile ilerleyebilir, ancak competition rehearsal profili warning/blocked kalır.

## Device Profile Özeti

Endpointler:

- `GET /api/device-profiles`
- `GET /api/device-profiles/active`
- `POST /api/device-profiles/save`
- `POST /api/device-profiles/apply`
- `POST /api/device-profiles/verify`
- `POST /api/device-profiles/reset`

Kalıcı runtime profil dosyaları `data/device_profiles/*.json` altında tutulur ve git dışında bırakılır. Örnek template `config/device_profiles/default.yaml` olarak eklendi.

UI’da:

- Save as active field profile
- Verify active profile
- Profile mismatch warnings

alanları eklendi.

## Camera Probe Özeti

Camera runtime status artık şu ayrımı verir:

- requested width/height/fps/pixel format
- actual width/height/fps measured/pixel format
- backend API
- warmup ms
- dropped frames
- last probe result
- recommendation score

Kamera yoksa mock state açıkça korunur; fiziksel komut üretimi yoktur.

## Vision Preset/Model Özeti

Runtime presetleri:

- `low_latency`
- `balanced`
- `high_accuracy`
- `debug`
- `competition_candidate`

Endpointler:

- `GET /api/vision/runtime/presets`
- `POST /api/vision/runtime/apply-preset`
- `POST /api/vision/runtime/save-preset`
- `POST /api/vision/runtime/verify-active`
- `POST /api/vision/runtime/test-active-model`

Vision ekranına preset selector, active model paneli ve model test butonu eklendi. Production model yoksa şu uyarı açıkça gösterilir:

`Production YOLO model is not loaded. OpenCV circle detector is test-only.`

## Release QA Özeti

Eklendi:

- `scripts/check_release.py`
- `GET /api/release/status`
- `POST /api/release/check`

Kontroller:

- Python version
- uv availability
- backend import
- frontend/dist exists
- config exists
- writable logs/exports
- start scripts
- required dirs
- model dir
- firmware dir

## UI Düzeltmeleri

- First Run ekranına profile selector ve profile-specific checklist eklendi.
- Devices ekranına field profile actions ve mismatch warnings eklendi.
- Vision ekranına preset selector, active model paneli ve requested/actual camera bilgileri eklendi.
- Logs ekranı kolonlu layout ile düzenlendi: type, severity, summary, seq/id, timestamp.
- Dashboard’a release readiness ve field profile bilgileri eklendi.

## KTR/Interface Düzeltmeleri

Interface Inventory alanları genişletildi:

- verification_status
- readiness_profile_dependency
- operator_visible
- export_evidence_path

KTR preview metni OpenCV circle detector’ın yalnızca test adapter olduğunu açıkça belirtir. Electronic power/signal bölümü “sistem arayüz tanımı kapsamında planlanan fiziksel arayüzler” olarak daha profesyonel ifade edildi.

## Test/Build Sonuçları

- `uv run pytest tests/test_phase14_field_release_qa.py -q`: 7 passed
- `uv run pytest -q`: 186 passed
- `pnpm typecheck`: passed
- `pnpm build`: passed
- `scripts/check_release.py`: passed
- Manual smoke:
  - `/`: 200
  - `/first-run`: 200
  - `/devices`: 200
  - `/vision`: 200
  - `/self-test`: 200
  - `/interfaces`: 200
  - `/reports`: 200
  - `/logs`: 200
  - `/api/release/status`: 200
  - `/api/device-profiles/active`: 200
  - `/api/vision/runtime/presets`: 200

## Screenshot Yolları

- `reports/screenshots/phase14_field_release_qa/01_first_run_profiles.png`
- `reports/screenshots/phase14_field_release_qa/02_device_profile_active.png`
- `reports/screenshots/phase14_field_release_qa/03_camera_probe_requested_vs_actual.png`
- `reports/screenshots/phase14_field_release_qa/04_vision_runtime_presets.png`
- `reports/screenshots/phase14_field_release_qa/05_active_model_panel.png`
- `reports/screenshots/phase14_field_release_qa/06_logs_fixed_layout.png`
- `reports/screenshots/phase14_field_release_qa/07_release_readiness_dashboard.png`
- `reports/screenshots/phase14_field_release_qa/08_self_test_profile_filtered.png`
- `reports/screenshots/phase14_field_release_qa/09_ktr_interface_polished.png`

## Commit Hashleri

Önceki son commitler:

- `f09f8b1` - `docs: add phase 13 portable interface hardening report`
- `1b2c037` - `feat: add portable release and interface inventory hardening`
- `807c288` - `feat: add device manager and live vision runtime settings`
- `5263ba5` - `feat: add telemetry-only pico firmware and verified read-only flow`
- `6e7039a` - `test: verify real pico read-only acceptance`

Faz 14 commit’i task sonunda eklenecek.

## Bilinen Eksikler

- Gerçek Pico bağlı olmadığı için hardware telemetry readiness profili gerçek cihazla geçmedi.
- Production YOLO modeli olmadığı için competition rehearsal profili test adapter senaryosunda warning/blocked kalır.
- Windows launcher gerçek Windows ortamında çalıştırılmadı.
- Camera probe fiziksel kamera yoksa mock/metadata sonucuyla sınırlı kalır.

## Sonraki Önerilen Task

- Faz 15’e geçmeden önce temiz bir ZIP klasöründe portable release acceptance yapılmalı:
  - Windows veya Linux temiz makine
  - First Run profile check
  - Device profile save/verify
  - Production YOLO model dosyası ile runtime verify
  - Reports/KTR export

Safety invariant korunmuştur:

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`
