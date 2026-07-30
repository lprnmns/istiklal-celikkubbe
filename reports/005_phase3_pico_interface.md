# Task Raporu: Faz 3 - Pico 2 Arayuzu ve Pin Validasyonu

## Yapilanlar

- Housekeeping olarak Faz 2 raporu ayri commit'e alindi.
- Backend Pico API endpointleri eklendi:
  - `GET /api/pico/status`
  - `GET /api/pico/ports`
  - `POST /api/pico/connect`
  - `POST /api/pico/disconnect`
  - `GET /api/pico/pins`
  - `PUT /api/pico/pins`
  - `POST /api/pico/pins/validate`
- Pico telemetry modeli genisletildi.
- Pin assignment, pin profile ve validation modelleri eklendi.
- Mock Pico default davranisi korundu.
- Port listesi gercek `/dev/ttyACM*`, `/dev/ttyUSB*`, `/dev/serial/by-id/*`, `/dev/cu.*` cihazlarini listeleyebilir; her zaman `MOCK_PICO` secenegi ekler.
- Pin validation backend servis katmaninda uygulandi.
- Sistem `DISARMED` degilse veya armed ise pin update reddediliyor.
- Pin profili bu fazda config dosyasina yazilmiyor; backend memory state uzerinde tutuluyor.
- WebSocket eventleri genisletildi:
  - `pico.telemetry`
  - `pico.connection`
  - `pico.pin_validation`
- Frontend Pico sayfasi gelistirildi:
  - connection status card
  - port listesi
  - connect/disconnect butonlari
  - mock mode gostergesi
  - telemetry detay kartlari
  - pin validation paneli
  - pin assignment table
  - tiklanabilir Pico 2 pinout preview
  - pin detail paneli ve function dropdown
- Faz 3 dokumantasyonu eklendi.
- Gercek hardware komutu, motor komutu, servo tetigi veya fire komutu eklenmedi.
- Serial binary protocol eklenmedi.

## Olusturulan / Degistirilen Dosyalar

| Dosya | Degisiklik |
|---|---|
| `backend/app/api/routes_pico.py` | Pico REST endpointleri eklendi. |
| `backend/app/api/routes_ws.py` | Pico connection ve pin validation WebSocket eventleri eklendi. |
| `backend/app/main.py` | Pico router uygulamaya baglandi. |
| `backend/app/schemas/pico.py` | Pico telemetry, pin assignment, profile ve validation modelleri eklendi. |
| `backend/app/services/pico_service.py` | Mock Pico status, port listesi, connect/disconnect, pin validation ve memory update servisi eklendi. |
| `backend/app/services/runtime_state.py` | Runtime Pico service entegrasyonu eklendi. |
| `backend/app/mocks/mock_pico.py` | Eski dar mock servis kaldirildi; yerine `PicoService` kullaniliyor. |
| `backend/tests/test_pico.py` | Pico endpoint ve validation testleri eklendi. |
| `backend/tests/test_websocket.py` | Yeni Pico WebSocket eventleri icin smoke test guncellendi. |
| `frontend/src/types/pico.ts` | Pico frontend tipleri eklendi. |
| `frontend/src/api/pico.ts` | Pico REST API client eklendi. |
| `frontend/src/stores/systemStore.ts` | Pico telemetry, connection ve validation event state'i genisletildi. |
| `frontend/src/components/pico/PicoBoard.vue` | Tiklanabilir Pico pinout preview eklendi. |
| `frontend/src/components/pico/PinValidationPanel.vue` | Validation issue paneli eklendi. |
| `frontend/src/views/PicoView.vue` | Pico arayuzu detaylandirildi. |
| `frontend/src/views/DashboardView.vue` | Yeni Pico telemetry alanlariyla uyumlu hale getirildi. |
| `docs/pico_phase3.md` | Endpoint, model, validation ve UI akis dokumani eklendi. |
| `reports/005_phase3_pico_interface.md` | Bu rapor eklendi. |

## Calistirilan Komutlar

```bash
git status --short
git add reports/004_phase2_frontend_dashboard.md
git commit -m "docs: add phase 2 frontend dashboard report"
PATH="$HOME/.local/bin:$PATH" uv run pytest
pnpm typecheck
pnpm build
git add backend docs/pico_phase3.md frontend/src
git commit -m "feat: add pico interface and pin validation"
setsid -f sh -c 'cd /home/alperen/teknofest/backend && PATH="$HOME/.local/bin:$PATH" uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/istiklal-backend.log 2>&1'
setsid -f sh -c 'cd /home/alperen/teknofest/frontend && pnpm dev --host 127.0.0.1 --port 5173 > /tmp/istiklal-frontend.log 2>&1'
curl -sS http://127.0.0.1:8000/api/pico/status
curl -sS http://127.0.0.1:8000/api/pico/ports
curl -sS -I http://127.0.0.1:5173
```

## Test / Build Sonuclari

```text
Backend pytest: 19 passed in 0.64s
Frontend pnpm typecheck: passed
Frontend pnpm build: passed
Manual backend /api/pico/status: passed
Manual backend /api/pico/ports: passed
Manual frontend HTTP check: HTTP 200
```

Build ciktisi:

```text
dist/index.html                  0.45 kB
dist/assets/index-*.css         20.43 kB
dist/assets/index-*.js         123.66 kB
```

## Git Commit Hashleri

```text
94edad9 docs: add phase 2 frontend dashboard report
9f33f6d feat: add pico interface and pin validation
```

## Pico Ekranlarinin Kisa Aciklamasi

- Pico Connection: mock/live durumu, port, baudrate, firmware ve hardware disabled bilgilerini gosterir.
- Port Control: port secimi, baudrate ve mock connect/disconnect aksiyonlarini icerir.
- Telemetry Detail: E-stop, driver, pan/tilt step ve heartbeat age alanlarini gosterir.
- Pico 2 Pinout Preview: Pico benzeri SVG kart uzerinde pinleri tiklanabilir gosterir.
- Pin Detail: secili pinin gorevini dropdown ile preview olarak degistirir.
- Pin Validation: backend validation sonucunu critical/error/warning/info seviyelerine gore gosterir.
- Pin Assignment Table: profilin tum pinlerini tablo halinde gosterir.

## Pin Validation Kurallari

- Ayni kritik gorev iki pine atanamaz.
- `ESTOP_IN` input olmalidir.
- Limit switch gorevleri input olmalidir.
- STEP/DIR gorevleri output olmalidir.
- `TRIGGER_SERVO_PWM` PWM-capable output pin olmalidir.
- `UART_TX` ve `UART_RX` ayni pin olamaz.
- `PAN_STEP`, `PAN_DIR`, `TILT_STEP`, `TILT_DIR` eksikse validation error uretir.
- `ESTOP_IN` eksikse critical error uretir.
- Sistem `DISARMED` degilse pin update reddedilir.
- Sistem armed ise pin update reddedilir.

## Bilinen Eksikler

- Pin profili config dosyasina yazilmiyor; sadece backend memory state'te tutuluyor. Bu, placeholder profilin yanlislikla kalici hale gelmesini onlemek icin bu fazda bilincli tercih edildi.
- Pico board SVG ilk surumdur; fiziksel kartin tum guc/GND/ADC ayrintilarini modellemiyor.
- Frontend component/unit test altyapisi henuz yok; typecheck/build ve backend pytest ile dogrulandi.
- Gercek serial port acma ve PySerial entegrasyonu yok; Faz 4 veya daha sonraki serial entegrasyon kapsaminda ele alinmali.
- `reports/005_phase3_pico_interface.md` commit sonrasinda olusturuldu; bu rapor henuz commitlenmedi.

## Riskler

- UI pin degisikligini preview olarak gosterse de safety otoritesi backend/Pico tarafinda olmalidir.
- Mock connect/disconnect gercek serial port acmaz; fiziksel entegrasyon sirasinda bunu yanlis sekilde "hardware connected" kabul etmemek gerekir.
- Placeholder pin profili final/onayli kablolama degildir.
- Config'e yazma ileride eklenecekse audit log, DISARMED gate ve kullanici onayi olmadan acilmamalidir.

## Bir Sonraki Onerilen Task

Faz 4 - Serial Protocol:

- JSON-line dev protocol encode/decode.
- Binary packet temel siniflari.
- CRC16.
- ACK/NACK.
- Timeout.
- Serial monitor.

Kullanici `devam` demeden Faz 4'e gecilmeyecek.
