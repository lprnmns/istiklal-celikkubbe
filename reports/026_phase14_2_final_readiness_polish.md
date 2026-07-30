# Ara Task 14.2 - Final Readiness Label Consistency and KTR Table Polish

## Yapılanlar
- First Run durum etiketi tekil frontend store computed değerinden beslenir hale getirildi.
- Topbar, First Run ve Dashboard üzerinde environment/profile ayrımı netleştirildi.
- Dashboard Mission Readiness kartı tek ana blocker yerine en fazla 4 maddelik Top Blockers listesine geçirildi.
- Interface Inventory API ve UI tablosuna Türkçe display adı ve kategori etiketi eklendi.
- KTR export envanter tablosunda Türkçe ad korunurken teknik interface adı parantez içinde bırakıldı.
- OpenCV circle detector ifadeleri “test adaptörü” vurgusuyla tutarlı hale getirildi.
- Phase 14.2 screenshot kanıtları üretildi.

## First Run badge consistency sonucu
- Topbar ve First Run sayfası aynı store kaynağını kullanır:
  - `FIRST RUN: OPEN`
  - `FIRST RUN: PASSED`
  - `FIRST RUN: FAILED`
- Mark complete sonrası iki yerde de `FIRST RUN: PASSED` görünür.
- Reset sonrası iki yerde de `FIRST RUN: OPEN` görünür.

## Environment/profile label sonucu
- Environment build/runtime mode ayrı badge olarak gösterilir: `ENV: DEVELOPMENT`.
- Readiness profile ayrı badge olarak gösterilir: `PROFILE: DEMO`.
- Demo readiness seçili iken `DEVELOPMENT` artık profile gibi görünmez.

## Dashboard blocker sonucu
- Mission Readiness kartı şu tür blocker/limitation maddelerini listeler:
  - System is disarmed
  - Self-test not run
  - Production YOLO model not loaded
  - Pico telemetry not verified
  - Hardware command path disabled
- Demo profile için production model/Pico eksikleri `DEMO LIMITATION` olarak görünür.
- Competition profile seçildiğinde aynı eksikler blocking mantığıyla değerlendirilir.

## KTR table polish sonucu
- Interface Inventory tablosunda kullanıcıya görünen ana başlıklar Türkçeleştirildi.
- Interface display adları eklendi:
  - Taşınabilir Başlatıcı Arayüzü
  - Elektronik Güç/Sinyal Arayüz Tanımı
  - Dağıtım/Çalıştırma Arayüzü
  - Rapor Dışa Aktarım Arayüzü
  - Veri Seti ve Replay Arayüzü
  - Kullanıcı Arayüzü
  - Güvenlik Arayüzü
  - Görüntü İşleme Model Arayüzü
- KTR export markdown tablosunda Türkçe ad yanında teknik ad parantez içinde korunur.

## Test/build sonuçları
- `uv run pytest -q` -> 186 passed
- `pnpm typecheck` -> passed
- `pnpm build` -> passed
- `scripts/check_release.py` -> passed
- Manual smoke -> `/`, `/first-run`, `/interfaces`, `/reports`, `/logs`, `/api/release/status`, `/api/first-run/status`, `/api/interfaces/inventory`, `/api/reports/status` HTTP 200

## Screenshot yolları
- `reports/screenshots/phase14_2_final_readiness_polish/01_first_run_passed_consistent.png`
- `reports/screenshots/phase14_2_final_readiness_polish/02_first_run_reset_open_consistent.png`
- `reports/screenshots/phase14_2_final_readiness_polish/03_dashboard_top_blockers.png`
- `reports/screenshots/phase14_2_final_readiness_polish/04_environment_profile_labels.png`
- `reports/screenshots/phase14_2_final_readiness_polish/05_ktr_table_turkish_polished.png`
- `reports/screenshots/phase14_2_final_readiness_polish/06_interfaces_export_after_polish.png`

## Commit hashleri
- Başlangıç commit'i: `b71a90c`
- Ara Task 14.2 commit'i: final commit sonrası doğrulanacak.

## Bilinen eksikler
- Gerçek Pico bağlı olmadığı için hardware telemetry readiness gerçek cihazla doğrulanmadı.
- Production YOLO modeli hâlâ yüklenmedi; competition rehearsal readiness bu nedenle eksik kalır.
- Windows launcher gerçek Windows sistemde ayrıca smoke test gerektirir.

## Sonraki önerilen task
- Gerçek Pico ve production YOLO modeli hazır olduğunda competition rehearsal acceptance için ayrı bir saha doğrulama taskı çalıştırılmalı.
