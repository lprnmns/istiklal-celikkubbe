# Field Release QA Phase 14

## Amaç

Phase 14, portable release’in yarışma günü güvenilir kullanılabilmesi için readiness profile, device binding profile, camera probe, vision runtime preset, release QA ve operator UI hardening katmanlarını ekler.

Bu faz fiziksel kontrol fazı değildir. Motor, servo, tetik, atış, STEP/DIR/PWM, GPIO output ve fiziksel komut yolu eklenmemiştir.

## Windows Çift Tık Çalıştırma

1. Proje klasörünü aç.
2. `start_windows.bat` dosyasını çalıştır.
3. Launcher Python 3.12+, `uv`, port 8000 ve frontend build durumunu kontrol eder.
4. Tarayıcı `http://127.0.0.1:8000` adresine açılır.

## Linux Çalıştırma

1. Terminalde proje klasörüne gir.
2. `./start_linux.sh` çalıştır.
3. Launcher logları `logs/launcher/` altına yazılır.

## Python veya uv Yoksa

Launcher kontrollü hata verir ve sistemi değiştirmez. `uv` kurulmadan backend dependency sync yapılmaz.

## Offline Kullanım

Offline demo öncesi:

- `backend/` içinde `uv sync`
- `frontend/` içinde `pnpm install && pnpm build`
- `frontend/dist/index.html` var mı kontrol et
- `/api/release/status` ile release readiness kontrol et

## Port Çakışması

Port 8000 doluysa launcher kullanıcı dostu hata verir. Portu kullanan servis kapatılmadan backend başlatılmaz.

## Kamera İzinleri

`/devices` ekranında kamera permission, busy, stable path ve recommendation score görünür. Kamera yoksa mock camera güvenli fallback olarak kalır.

## Pico Telemetry-only Firmware Doğrulama

Pico candidate, Pico verified anlamına gelmez. Verified state yalnızca telemetry-only firmware `device=pico2` ve beklenen safe flags yayınladığında geçerli olur.

## Model Yükleme

Production YOLO modeli görüntü işleme ekibi tarafından sağlanır. Model yoksa sistem demo/test adapter ile çalışabilir ancak `competition_rehearsal_ready` profili warning/blocked kalır.

## Yarışma Günü Hızlı Kontrol Listesi

- [ ] Portable launcher açılıyor
- [ ] `/first-run` profile check çalıştı
- [ ] `/devices` kamera ve Pico adayları doğrulandı
- [ ] Active field profile kaydedildi ve verify edildi
- [ ] `/vision` runtime preset seçildi
- [ ] Production YOLO model yüklendi veya eksikliği raporlandı
- [ ] `/self-test` critical failure yok
- [ ] `/reports` KTR/demo pack export alındı
- [ ] Safety invariant kontrol edildi:
  - DISARMED
  - NO_FIRE
  - dry_run=true
  - hardware_enabled=false
  - physical_command_enabled=false
