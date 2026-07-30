# Faz 15 - Cross-Platform Portable Release Candidate and First-Install Acceptance

## Amaç

ISTIKLAL C2 Console'un Windows/Linux ZIP release candidate olarak çalıştırılabilmesi, ilk kurulum eksiklerini güvenli şekilde raporlaması ve frontend static build ile backend üzerinden çalışması hedeflendi. Fiziksel komut yolu eklenmedi.

## Yapılanlar

- Windows ve Linux launcher dosyaları güçlendirildi.
- Release common payload klasör yapısı eklendi.
- Backend `/api/release/status`, `/api/release/preflight`, `/api/release/check` kapsamı genişletildi.
- Release manifest üretimi eklendi: `exports/release/release_manifest_<timestamp>.json`.
- First Run profillerine `release_candidate_ready` eklendi.
- Frontend static serving alternatif portlarda çalışacak şekilde API/WebSocket same-origin fallback düzeltildi.
- Devices, Vision, Dashboard ve First Run ekranlarına release candidate / model / device binding görünürlüğü eklendi.
- KTR export ve Interface Inventory içine "Taşınabilir Çalıştırma ve Kurulum Arayüzü" bölümü eklendi.
- `scripts/check_release.py` release QA scripti JSON/Markdown rapor üretecek şekilde genişletildi.
- Faz 15 screenshot kanıtları üretildi.

## Release Paket Yapısı

- `release/linux/start_istiklal_c2.sh`
- `release/linux/README_FIRST_RUN.md`
- `release/windows/start_istiklal_c2.bat`
- `release/windows/README_FIRST_RUN.md`
- `release/common/config/`
- `release/common/models/`
- `release/common/firmware/`
- `release/common/docs/`
- `release/common/reports/`
- `release/common/scripts/`
- root launcherlar: `start_linux.sh`, `start_windows.bat`

Runtime büyük çıktıları Git dışında tutuldu:

- `exports/release/**`
- `reports/release/**`
- log/export/model binary/runtime klasörleri

## Windows Launcher Davranışı

- Python varlığını ve Python 3.12+ gereksinimini kontrol eder.
- `uv` yoksa kullanıcı dostu hata verir.
- `frontend/dist/index.html` yoksa runtime'da pnpm/npm build çalıştırmaz; release paketinin eksik olduğunu bildirir.
- `.venv`/backend dependency kurulumunu `uv sync` ile yapar.
- `logs/` ve `exports/` yazılabilirliğini kontrol eder.
- Port doluysa anlaşılır hata verir.
- Tarayıcıyı `http://127.0.0.1:<port>` adresinde açar.
- Fiziksel komut endpointi çağırmaz.

Gerçek Windows host üzerinde çalışma ayrıca denenmelidir; bu ortamda Windows launcher static inspection kanıtı üretildi.

## Linux Launcher Davranışı

- `python3`, Python 3.12+, `uv`, config/model/frontend static ve yazılabilir runtime klasörlerini kontrol eder.
- `/dev/ttyACM*`, `/dev/ttyUSB*` ve `/dev/video*` durumunu sadece bilgilendirir.
- Serial permission için `dialout` notu verir; otomatik `sudo/usermod` çalıştırmaz.
- `frontend/dist` yoksa runtime build yapmadan güvenli hata verir.
- Port 8000 doluysa `ISTIKLAL_PORT` ile alternatif port önerir.
- Fiziksel komut veya hardware enable çağrısı yapmaz.

## Dependency/Preflight Checker Sonucu

Endpointler:

- `GET /api/release/status`
- `GET /api/release/preflight`
- `POST /api/release/check`
- `GET /api/release/check` smoke kolaylığı için read-only preflight alias

Preflight raporlanan ana alanlar:

- platform ve python sürümü
- app root
- writable logs/exports
- frontend static build
- config loaded
- model dir
- active model state
- camera/serial/Pico candidate sayıları
- dry_run / NO_FIRE / hardware command disabled
- safety invariant

Release check çıktısı:

- JSON: `exports/release/release_check_20260510_012511.json`
- Markdown: `reports/release/release_check_20260510_012511.md`
- Status: `passed`

## First Run Release Profile Sonucu

`release_candidate_ready` profili eklendi.

Minimum kabul:

- backend reachable
- frontend static available
- config loaded
- logs/exports writable
- launcher files present
- release manifest available
- device manager reachable
- camera mock or selected
- model registry reachable
- no physical command invariant passed

Bu profilde gerçek Pico veya production YOLO yokluğu failed yapılmaz; release/demo için uyarı seviyesinde kalır. `competition_rehearsal_ready` için production model ve verified Pico telemetry eksikliği blocking/warning olarak ayrıştırılır.

## Device/Camera/Model Binding Sonucu

- Devices ekranında release binding kartı eklendi.
- Kamera seçimi, stable path, probe sonucu, Pico candidate count, Pico pending/verified ve model binding ayrı gösteriliyor.
- Vision ekranında production YOLO yoksa uyarı korunuyor:
  `Production YOLO model is not loaded. OpenCV circle detector is a test adapter only.`
- Beklenen yarışma sınıfları UI'da açık:
  `f16, helicopter, ballistic_missile, mini_micro_uav, balloon`

## KTR Katkısı

KTR/Interface metnine şu bölüm eklendi:

- Taşınabilir Çalıştırma ve Kurulum Arayüzü

İçerik:

- Windows `.bat` launcher
- Linux `.sh` launcher
- FastAPI backend static serving
- frontend static UI
- first-run acceptance
- dependency/preflight checks
- device discovery
- camera source binding
- model runtime binding
- logs/export evidence

Güvenlik vurgusu:

`Başlatıcı arayüzleri yalnızca yazılımı çalıştırır; fiziksel komut yetkisi vermez.`

## Test/Build Sonuçları

- Backend: `uv run pytest -q` -> geçti
- Frontend: `pnpm typecheck` -> geçti
- Frontend: `pnpm build` -> geçti
- Release: `python3 scripts/check_release.py` -> geçti
- Launcher syntax: `bash -n release/linux/start_istiklal_c2.sh` -> geçti
- Root launcher syntax: `bash -n start_linux.sh` -> geçti

Manual smoke 8015 portunda yapıldı çünkü bu makinede 8000 portu başka bir servis tarafından tutuluyordu:

- `/`
- `/first-run`
- `/devices`
- `/vision`
- `/self-test`
- `/interfaces`
- `/reports`
- `/logs`
- `/api/health`
- `/api/release/status`
- `/api/release/preflight`
- `/api/release/check`
- `/api/devices`
- `/api/camera/runtime/status`
- `/api/vision/runtime/status`
- `/api/interfaces`
- `/api/reports`

Tümü HTTP 200 döndü.

## Release Check Çıktıları

- Release manifest: `exports/release/release_manifest_1778365511.json`
- Release check JSON: `exports/release/release_check_20260510_012511.json`
- Release check Markdown: `reports/release/release_check_20260510_012511.md`

Bu dosyalar runtime/export çıktısı olarak Git dışında tutulur.

## Screenshot Yolları

- `reports/screenshots/phase15_release_candidate/01_release_first_run_profile.png`
- `reports/screenshots/phase15_release_candidate/02_release_preflight_status.png`
- `reports/screenshots/phase15_release_candidate/03_windows_launcher_preview_or_log.png`
- `reports/screenshots/phase15_release_candidate/04_linux_launcher_preview_or_log.png`
- `reports/screenshots/phase15_release_candidate/05_devices_release_binding_status.png`
- `reports/screenshots/phase15_release_candidate/06_vision_model_import_readiness.png`
- `reports/screenshots/phase15_release_candidate/07_release_dashboard_status.png`
- `reports/screenshots/phase15_release_candidate/08_ktr_release_interface_section.png`
- `reports/screenshots/phase15_release_candidate/09_logs_release_check_events.png`
- `reports/screenshots/phase15_release_candidate/10_reports_release_export.png`

## Commit Hashleri

- Başlangıç commit: `2bd7f92`
- Faz 15 commit hash'i final yanıtta ayrıca bildirilecektir.

## Bilinen Eksikler

- Windows launcher gerçek Windows host üzerinde ayrıca denenmelidir.
- Bu faz ZIP paketini fiziksel olarak arşivlemedi; release candidate dosya yapısı ve preflight/manifest altyapısı hazırlandı.
- Production YOLO modeli hâlâ görüntü işleme ekibi teslimine bağlıdır.
- Gerçek Pico yoksa `hardware_telemetry_ready` ve `competition_rehearsal_ready` tamamlanmış sayılmaz.

## Sonraki Önerilen Task

Faz 16'ya geçmeden önce gerçek Windows makinede launcher acceptance, gerçek ZIP paket oluşturma ve offline wheelhouse stratejisinin netleştirilmesi önerilir.

## Safety Invariant

Korundu:

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- `no_physical_command_generated=true`

Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya fiziksel komut yolu eklenmedi.
