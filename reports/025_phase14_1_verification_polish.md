# Ara Task 14.1 - Verification Semantics, Build Label ve KTR Polish Hotfix

## Yapılanlar
- Topbar build etiketi `ISTIKLAL C2 CONSOLE · PHASE 14 · BUILD <hash|DEV-LOCAL>` formatına alındı.
- First Run, Self-Test ve seçili readiness profile topbar badge'leri birbirinden ayrıldı.
- Device Profile doğrulama semantiği `verified` yerine mock/demo/hardware pending/competition not verified seviyelerine ayrıldı.
- Vision Active Model paneli production YOLO modeli yokken açık blocked/warning gösterecek şekilde güçlendirildi.
- Logs tablosu sabit kolonlu ve responsive truncate davranışlı hale getirildi.
- KTR 4.3 preview başlıkları resmi Türkçe yapıya çekildi ve OpenCV circle detector'ın sadece test adaptörü olduğu netleştirildi.
- Phase 14.1 screenshot kanıtları üretildi.

## Düzeltilen terminology/statü problemleri
- `READINESS NOT RUN` tekil/belirsiz badge'i kaldırıldı.
- Topbar artık `FIRST RUN`, `SELF TEST` ve `PROFILE` durumlarını ayrı gösterir.
- Mock/demo cihaz profilinde genel `verified` ifadesi kullanılmıyor.
- Competition hazırlığı gerçek Pico telemetry ve production YOLO modeli yoksa `competition_not_verified` olarak kalır.

## Build label sonucu
- UI global topbar: `ISTIKLAL C2 CONSOLE · PHASE 14 · BUILD <short_git_hash veya DEV-LOCAL>`.
- Aynı topbar Dashboard, First Run, Devices, Vision, Logs, Self-Test, Interfaces ve Reports rotalarında görünür.

## Verification semantics sonucu
- Device Profile alanları ayrıldı:
  - Active profile
  - Verification level
  - Camera binding
  - Pico binding
  - Model binding
  - Competition status
- Mock camera için camera binding `Mock/demo only` görünür.
- Pico candidate count 0 iken profile artık competition/hardware verified görünmez.

## Vision model panel sonucu
- Production YOLO modeli yoksa büyük uyarı gösterilir:
  `Production YOLO model is not loaded. OpenCV circle detector is test-only and cannot be used as competition detector.`
- Panelde `active_model_id`, `model_file`, `model_type`, `expected_classes`, `detected_classes`, `class_mapping_status`, `loaded`, `last_test_status`, `adapter_mode` ve model test safety kanıtı görünür.

## Logs layout sonucu
- Logs tablo kolonları sabitlendi: type, severity, summary, seq/id, timestamp.
- Uzun type/summary değerleri truncate edilir.
- Raw JSON sadece Event Detail panelinde, collapsible blokta gösterilir.
- 1366x768 ve 1920x1080 screenshot smoke alındı.

## KTR polish sonucu
- KTR 4.3 preview başlıkları:
  - Kullanıcı Arayüzü
  - Yazılımsal Arayüzler
  - Görüntü ve Model Arayüzleri
  - Cihaz Keşif ve Kamera Arayüzleri
  - Pico Seri Telemetri Arayüzü
  - Güvenlik Arayüzleri
  - Veri, Log ve Rapor Arayüzleri
  - Dağıtım/Çalıştırma Arayüzü
  - Elektronik Güç/Sinyal Arayüz Tanımı
- Elektronik güç/sinyal metni fiziksel çıkış üretilmediğini açıkça belirtir.

## Test/build sonuçları
- `uv run pytest -q` -> 186 passed
- `pnpm typecheck` -> passed
- `pnpm build` -> passed
- `scripts/check_release.py` -> passed
- Manual smoke -> `/`, `/first-run`, `/devices`, `/vision`, `/logs`, `/interfaces`, `/reports`, `/api/release/status`, `/api/device-profiles/active`, `/api/vision/runtime/status` HTTP 200

## Screenshot yolları
- `reports/screenshots/phase14_1_verification_polish/01_topbar_phase14_labels.png`
- `reports/screenshots/phase14_1_verification_polish/02_first_run_badges_no_conflict.png`
- `reports/screenshots/phase14_1_verification_polish/03_devices_verification_semantics.png`
- `reports/screenshots/phase14_1_verification_polish/04_vision_active_model_warning.png`
- `reports/screenshots/phase14_1_verification_polish/05_logs_responsive_fixed_1366.png`
- `reports/screenshots/phase14_1_verification_polish/06_logs_responsive_fixed_1920.png`
- `reports/screenshots/phase14_1_verification_polish/07_ktr_turkish_polished.png`

## Commit hashleri
- Başlangıç commit'i: `f2ed59e`
- Ara Task 14.1 commit'i: final commit sonrası doğrulandı ve kullanıcıya final yanıtta bildirilecek.

## Bilinen eksikler
- Gerçek Pico bağlı olmadığı için hardware telemetry readiness gerçek cihazla hâlâ doğrulanmadı.
- Production YOLO modeli yok; OpenCV circle detector sadece test adaptörü olarak kalıyor.
- Windows launcher gerçek Windows makinede ayrıca denenmeli.

## Sonraki önerilen task
- Gerçek Pico ve production YOLO modeli geldiğinde `hardware_telemetry_ready` ve `competition_rehearsal_ready` profilleri için saha kabul testi yapılmalı.
