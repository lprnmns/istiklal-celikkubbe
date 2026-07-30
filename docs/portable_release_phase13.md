# Portable Release Phase 13

## Amaç

İSTİKLAL C2 Console, Phase 13 ile geliştirici ortamına bağlı kalmadan Windows ve Linux bilgisayarlarda taşınabilir şekilde başlatılabilecek hale getirildi.

## Windows Çalıştırma

1. Proje klasörünü aç.
2. `start_windows.bat` dosyasını çalıştır.
3. Launcher Python 3.12+, `uv`, port 8000 ve frontend build durumunu kontrol eder.
4. Backend `http://127.0.0.1:8000` üzerinde başlar.
5. Tarayıcı otomatik açılır.

## Linux Çalıştırma

1. Proje klasörünü aç.
2. `./start_linux.sh` çalıştır.
3. Launcher Python 3.12+, `uv`, port 8000 ve frontend build durumunu kontrol eder.
4. Backend `http://127.0.0.1:8000` üzerinde başlar.

## İlk Kurulum

- `uv` yoksa launcher açık hata verir.
- `frontend/dist` yoksa ve `pnpm` varsa frontend build alınır.
- `frontend/dist` varsa Node/pnpm runtime için zorunlu değildir.
- Launcher logları `logs/launcher/launcher_YYYYMMDD_HHMMSS.log` altına yazılır.

## Offline Kullanım

Offline demo öncesi:

1. `backend/` içinde `uv sync` çalıştır.
2. `frontend/` içinde `pnpm install` ve `pnpm build` çalıştır.
3. `frontend/dist/index.html` oluştuğunu doğrula.
4. Proje klasörünü ZIP olarak taşı.

## Frontend Static Serving

Backend production/portable kullanımda `frontend/dist` klasörünü serve eder.

- API route’ları `/api/*` altında kalır.
- WebSocket `/ws` olarak kalır.
- SPA fallback `/devices`, `/vision`, `/self-test`, `/reports`, `/interfaces` gibi route’ları doğrudan açar.

## Cihaz Seçimi

`/devices` ekranı kamera, seri port ve Pico adaylarını listeler. Düşük aday skorlu `/dev/ttyS*` portları varsayılan olarak gizlenir. Pico candidate, Pico verified anlamına gelmez; doğrulama sadece telemetry-only firmware’den `device=pico2` geldiğinde yapılır.

## Model Yükleme

Vision team üretim YOLO/ONNX modelini sağlar. Arayüz tarafı model registry, aktif model seçimi, inference adapter ayarları ve runtime parametrelerini yönetir. OpenCV circle detector yalnızca test adapter’dır.

## Log ve Export Klasörleri

- Launcher logları: `logs/launcher/`
- Runtime JSONL logları: `logs/`
- Report export: `exports/reports/`
- Interface export: `exports/interfaces/`
- Client log export: `exports/logs/`

## Troubleshooting

- Python bulunamadı: Python 3.12+ kur.
- uv bulunamadı: uv resmi kurulumunu yap.
- Port 8000 dolu: portu kullanan servisi kapat.
- Frontend açılmıyor: `frontend/dist/index.html` var mı kontrol et.
- Kamera görünmüyor: `/devices` ekranında permission/busy uyarılarını incele.
- Pico candidate yok: USB kablo, port permission ve telemetry firmware durumunu kontrol et.

## Safety

Portable launcher yazılımı başlatır; hardware enable açmaz. Safety invariant korunur:

- DISARMED
- NO_FIRE
- dry_run=true
- hardware_enabled=false
- physical_command_enabled=false
