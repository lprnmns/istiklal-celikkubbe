# Ara Task 15.1 - Release Candidate Semantic Consistency Hotfix

## Yapılanlar

- `release_candidate_ready`, `competition_rehearsal_ready` ve mission readiness kavramları ayrıştırıldı.
- `release_candidate_ready` donanımsız ve production YOLO olmadan çalışabilir paket profili olarak `passed` kalabiliyor.
- `competition_rehearsal_ready` için şu eksikler blocking yapıldı:
  - production YOLO model yok
  - Pico telemetry verified değil
  - gerçek kamera/probe doğrulanmamış
  - self-test çalışmamış
- Dashboard’da release profile passed ile mission readiness blocked durumları ayrı gösterildi.
- `/api/release/status` artık varsa son manifest yolunu döndürüyor; Dashboard manifest için dosya adını gösteriyor.
- Python minimum sürüm metinleri launcher tarafında `Python 3.12+` standardına çekildi.
- “OpenCV circle detector is a test adaptörü only” benzeri karma metinler Türkçe hale getirildi.
- KTR 4.3 release bölümüne release candidate ile competition rehearsal farkını anlatan paragraf eklendi.
- Kamera mock ise topbar “Camera Mock Running” gösteriyor.

## Düzeltilen Semantik Problemler

- Release candidate readiness artık competition rehearsal readiness gibi yorumlanmıyor.
- Mission Readiness kartı, release profile passed olsa bile self-test/arm/model/Pico eksikliği nedeniyle mission readiness blocked durumunu açık gösteriyor.
- `/api/release/preflight` status ile Dashboard “Release candidate preflight” etiketi aynı anlamda kullanılıyor.
- Competition rehearsal gereksinimleri First Run checklist içinde ayrı ve blocking görünüyor.

## Manifest Tutarlılığı

- `release_manifest_path` API yanıtında korunuyor.
- Dashboard “Release manifest” alanında `release_manifest_<timestamp>.json` dosya adı görünüyor.
- `scripts/check_release.py` release check sırasında manifest üretiyor ve endpoint yanıtı aynı manifest yolunu raporluyor.
- Manifest içinde commit hash, phase, build_id, generated_at ve safety invariant alanları dolu.

## Python Sürüm Standardı

- Proje standardı `Python 3.12+` olarak korundu.
- Linux ve Windows launcher hata metinleri aynılaştırıldı:
  `Python bulunamadı veya sürüm yetersiz. Python 3.12+ kurup tekrar çalıştırın.`
- `pyproject.toml` standardı değiştirilmedi.

## Dil ve Operatör Metinleri

- Operatör metni Türkçeleştirildi:
  `OpenCV daire algılayıcı yalnızca test adaptörüdür; yarışma modeli değildir.`
- Active Model Panel, Vision Runtime, Data Lab ve backend warning metinleri tutarlı hale getirildi.
- Teknik alan adları, örneğin `active_model_id`, `class_mapping_status`, `adapter_mode`, korunmaya devam ediyor.

## UI Badge Sonucu

- Topbar:
  - `PROFILE: RELEASE CANDIDATE`
  - `FIRST RUN: PASSED`
  - `SELF TEST: NOT RUN`
  - `NO_FIRE`
  - `DRY RUN`
  çelişkisiz kaldı.
- Kamera mock durumunda `Camera Mock Running` gösteriliyor.
- Dashboard’da:
  - `RELEASE PROFILE: PASSED`
  - `MISSION READINESS BLOCKED`
  - `COMPETITION: BLOCKED`
  ayrı gösteriliyor.

## KTR Polish Sonucu

- KTR 4.3 içinde “Taşınabilir Çalıştırma ve Kurulum Arayüzü” bölümü güncellendi.
- Şu cümle korunuyor:
  `Başlatıcı arayüzleri yalnızca yazılımı çalıştırır; fiziksel komut yetkisi vermez.`
- Release candidate / competition rehearsal farkı resmi Türkçe paragrafla eklendi.

## Test/Build Sonuçları

- Backend: `uv run pytest -q` -> geçti
- Frontend: `pnpm typecheck` -> geçti
- Frontend: `pnpm build` -> geçti
- Release: `python3 scripts/check_release.py` -> geçti
- Linux launcher syntax: `bash -n release/linux/start_istiklal_c2.sh` -> geçti
- Root Linux launcher syntax: `bash -n start_linux.sh` -> geçti

Manual smoke 8015 portunda yapıldı:

- `/` -> 200
- `/first-run` -> 200
- `/devices` -> 200
- `/vision` -> 200
- `/interfaces` -> 200
- `/reports` -> 200
- `/logs` -> 200
- `/api/release/status` -> 200
- `/api/release/preflight` -> 200
- `/api/release/check` -> 200

## Screenshot Yolları

- `reports/screenshots/phase15_1_release_semantic_hotfix/01_first_run_release_candidate_consistent.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/02_dashboard_release_vs_mission_readiness.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/03_release_preflight_status_consistent.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/04_release_manifest_consistent.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/05_vision_test_adapter_turkish_text.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/06_devices_release_binding_consistent.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/07_ktr_release_text_consistent.png`
- `reports/screenshots/phase15_1_release_semantic_hotfix/08_logs_release_hotfix_events.png`

## Commit Hashleri

- Başlangıç commit: `5493870`
- Bu task commit hash'i final yanıtta bildirilecektir.

## Bilinen Eksikler

- Windows launcher gerçek Windows host üzerinde ayrıca denenmelidir.
- Production YOLO modeli ve gerçek Pico telemetry olmadan `competition_rehearsal_ready` blocked kalır.
- Gerçek kamera/probe doğrulaması yapılmadan competition rehearsal readiness tamamlanmış sayılmaz.

## Sonraki Önerilen Task

Faz 16’ya geçmeden önce gerçek Windows host launcher testi ve gerçek saha bilgisayarında release candidate ZIP smoke testi önerilir.

## Safety Invariant

Korundu:

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `physical_command_enabled=false`
- `no_physical_command_generated=true`

Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya fiziksel komut yolu eklenmedi.
