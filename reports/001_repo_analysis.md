# Repo Analiz Raporu

## Bulunan Teknolojiler

Mevcut calisma alaninda uygulama kodu yok. Bu nedenle fiilen kurulu framework, paket yoneticisi, test altyapisi veya runtime scripti bulunmadi.

Dokuman paketinde hedeflenen teknoloji yığını:

- Backend: Python 3.12+, FastAPI, WebSocket, Pydantic, OpenCV, Ultralytics YOLO, PySerial, SQLite/JSONL, YAML config.
- Frontend: Vue 3, TypeScript, Pinia, TailwindCSS, SVG/Canvas overlay, WebSocket client.
- Firmware/donanim: Raspberry Pi Pico 2, USB serial, TMC2209 STEP/DIR/UART, servo PWM, E-stop ve limit inputlari.
- Test hedefleri: unit, integration, UI, replay, hardware-in-the-loop, safety testleri.

Bulunmayan teknoloji/manifest dosyalari:

- `pyproject.toml`, `requirements.txt` yok.
- `package.json`, `vite.config.*`, `tsconfig*.json` yok.
- `Dockerfile`, `docker-compose*.yml`, `Makefile` yok.
- `.git/` yok; dizin Git repository olarak baslatilmamis.
- `.gitignore` yok.

## Mevcut Dosya Yapısı

Gercek dosya yapisi:

```text
/home/alperen/teknofest/
  istiklal_interface_agent_spec/
    00_README.md
    01_PRODUCT_VISION.md
    02_FEATURE_CATALOG.md
    03_SYSTEM_ARCHITECTURE.md
    04_UI_UX_SPEC.md
    05_INTERFACE_REQUIREMENTS_FOR_KTR.md
    06_BACKEND_API_AND_WEBSOCKET_SPEC.md
    07_PICO2_PINOUT_AND_HARDWARE_UI.md
    08_SERIAL_PROTOCOL.md
    09_VISION_AND_DECISION_UI.md
    10_SAFETY_ARMING_STATE_MACHINE.md
    11_DATASET_REPLAY_LOGGING.md
    12_CONFIGURATION_AND_MODEL_REGISTRY.md
    13_TESTING_ACCEPTANCE_CRITERIA.md
    14_INITIAL_AGENT_PROMPT.md
    15_AGENT_REPORT_TEMPLATE.md
    16_RECOMMENDED_REPO_STRUCTURE.md
    17_BACKLOG_AND_PHASES.md
    18_SOURCE_REFERENCES.md
    AGENT_PROMPT_COPY_PASTE.txt
  reports/
    001_repo_analysis.md
```

Okunan dokumanlar:

- `istiklal_interface_agent_spec/*.md` altindaki 19 Markdown dosyasinin tamami okundu.
- Ek olarak `AGENT_PROMPT_COPY_PASTE.txt` incelendi; 14 numarali prompt ile ayni icerige sahip.

## Eksik Kritik Bilgiler

- Yarışma teknik şartnamesi ve `ParkurÇizim.pdf` dosyalari repo icinde yok.
- Gercek kamera modeli, lens bilgisi, cozumurluk/FPS hedefi ve OS seviyesindeki kamera erisim yontemi net degil.
- YOLO body ve balloon model dosyalari yok; sinif isimleri dokumanda var ama egitim/veri kaynagi yok.
- Pico 2 firmware kaynak kodu yok.
- TMC2209 surucu baglanti detayi, UART adresleme, step/degree kalibrasyonu, limit switch tipi ve E-stop elektriksel mimarisi net degil.
- Gercek pin atama profili onayli degil; dokumandaki pinler ornek kabul edilmeli.
- Atesleme/servo mekanizmasinin fiziksel hareket sinirlari ve guvenli neutral PWM degeri belirtilmemis.
- Backend ile Pico arasinda gelistirme icin JSON-line, final icin binary protokol oneriliyor; hangi fazda binary'ye gecilecegi onaylanmali.
- Frontend tasarim sistemi, marka varliklari, logo ve ekran cozunurlugu hedefleri yok.
- Veri saklama politikasi, log retention, session naming ve export hedefleri net degil.
- GPU/CPU hedef donanim ve performans beklentilerinin hangi makinede olculecegi belirsiz.
- CI, lint, formatter, test komutlari ve paket yoneticisi tercihi yok.

## Riskler

- En buyuk risk guvenliktir. UI uzerinden gelen hicbir arm/fire/motor komutu tek basina guvenilir sayilmamali; backend ve Pico local safety modeli zorunlu olmali.
- Repo su an bos oldugu icin ilk fazlarda scaffold kararlari sonraki tum mimariyi belirleyecek. Acele frontend agirlikli baslamak safety ve protokol cekirdegini zayiflatir.
- Gercek donanim olmadan motor/servo kodu yazilirsa dry-run varsayilmazsa tehlikeli hareket riski dogar. Varsayilan mod kesinlikle mock/dry-run olmali.
- Binary serial protokol, CRC, ACK/NACK ve watchdog test edilmeden fiziksel komuta gecmek kabul edilemez.
- YOLO modeli, kamera kalibrasyonu ve veri seti henuz yoksa goruntu isleme ekranlari ilk etapta mock inference ile kurulmak zorunda kalacak.
- P0/P1/P2 kapsami genis. Her faz sonunda durup dogrulama yapilmazsa sistem demo gorunen ama guvenilir olmayan bir arayuze donusebilir.
- E-stop sadece UI durumu olarak ele alinirsa tasarim hatali olur. E-stop hattinin Pico ve tercihen guc katmaninda bagimsiz etkisi olmasi gerekir.
- Friend/enemy renk dogrulama ortama bagimli olacagi icin HSV/LAB esikleri field test olmadan guvenli karar kapisi olarak kabul edilmemeli.

## Önerilen Mimari

Monorepo yapisi kullanilmali:

```text
backend/   FastAPI, servisler, schemalar, protokoller, mocklar, testler
frontend/  Vue 3 + TypeScript + Pinia + Tailwind arayuzu
firmware/  Pico 2 firmware kodu
config/    YAML config ve pin profilleri
models/    body/balloon modelleri ve model kartlari
data/      raw/session/dataset ciktilari
logs/      JSONL runtime loglari
reports/   her ana task raporu
docs/      API, WebSocket, config ve mimari dokumantasyon
```

Backend icinde ana sinirlar:

- `api/`: REST ve WebSocket giris noktalari.
- `schemas/`: Pydantic modelleri ve hata formatlari.
- `services/`: camera, vision, tracking, decision, serial, config, log, replay servisleri.
- `protocols/`: JSON-line dev protokol, binary paket, CRC16.
- `mocks/`: mock camera, mock Pico, mock vision.
- `tests/`: safety, config, serial, decision ve API testleri.

Oncelikli teknik ilke:

- Sistem `NO_FIRE` ve `DISARMED` baslamali.
- Mock/dry-run default olmali.
- Gercek serial/hardware komutlari explicit config, operator onayi, backend gate ve Pico local gate olmadan aktif olmamali.
- Replay ve calibration modlarinda fiziksel komut uretilmemeli.
- Her komut ve karar gerekcesi JSONL olarak loglanmali.

## Fazlara Bölünmüş Uygulama Planı

### Faz 0 - Repo Analizi

Durum: tamamlandi.

Ciktilar:

- Dokuman paketi okundu.
- Mevcut dosya yapisi incelendi.
- Kritik eksikler ve riskler listelendi.
- Faz plani ve ilk task onerisi hazirlandi.

Testler:

- Dosya kesfi: `rg --files`, `find`, `ls`.
- Markdown sayimi/okuma: `wc -l`, `sed`.
- Git durumu kontrolu: `git status` denendi; dizin Git repo degil.

### Faz 1 - Proje Scaffold ve Backend Safety Cekirdegi

Ana tasklar:

- Monorepo klasor yapisini olustur.
- Backend `pyproject.toml` ve FastAPI app iskeletini kur.
- Health endpoint, tek WebSocket endpoint ve basit event bus ekle.
- Pydantic schema setinin ilk surumunu ekle: system, safety, pico, config, log.
- YAML config loader ve validasyon ekle.
- JSONL logger ekle.
- Mock Pico ve mock camera servislerini ekle.
- Varsayilan state'i `DISARMED` + `NO_FIRE` yap.

Ciktilar:

- Calisan FastAPI backend.
- `/api/health`, `/api/system/state`, `/ws`.
- Validasyonlu config.
- Mock telemetry yayinlayan WebSocket.
- Backend test altyapisi.

Testler:

- `pytest` unit testleri.
- FastAPI TestClient ile health/system endpoint testleri.
- WebSocket mock telemetry testi.
- Config validation negatif/pozitif testleri.
- Safety default `NO_FIRE` testi.

### Faz 2 - Frontend Scaffold ve Dashboard

Ana tasklar:

- Vue 3 + TypeScript + Vite + Pinia + Tailwind kur.
- App layout/sidebar ve route yapisini ekle.
- Dashboard, system state, safety card, Pico status card ve target table mocklarini ekle.
- WebSocket client ve system store ekle.
- Backend mock telemetry ile UI state guncellemesini bagla.

Ciktilar:

- Calisan frontend dev server.
- Dashboard ilk ekrani.
- Canli mock telemetry kartlari.
- Safety gates panelinin ilk surumu.

Testler:

- `npm run build`.
- TypeScript check.
- Basit component/store testleri.
- Manuel browser kontrolu.

### Faz 3 - Pico 2 Arayuzu ve Pin Validasyonu

Ana tasklar:

- Pico port listesi, connect/disconnect endpointleri ve mock serial telemetry.
- Pin assignment Pydantic modeli.
- Pin conflict, capability, missing critical pin validasyonlari.
- Frontend interaktif Pico pinout SVG ekraninin ilk surumu.
- Pin detail drawer ve validation panel.

Ciktilar:

- UI'da Pico pinleri, görevleri, telemetry ve validation mesajlari.
- Backend pin config validation API'si.

Testler:

- Pin conflict unit testleri.
- Critical pin missing testleri.
- DISARMED disinda pin degisikligi reddi testi.
- Frontend build ve manuel pin assignment testi.

### Faz 4 - Serial Protokol ve Serial Monitor

Ana tasklar:

- JSON-line dev protokol encode/decode.
- Binary packet modeli, CRC16, ACK/NACK, timeout siniflari.
- Serial monitor log akisinin backend ve UI karsiligi.
- Mock Pico ile ACK/NACK ve CRC hata senaryolari.

Ciktilar:

- Test edilebilir serial protocol katmani.
- UI serial monitor.
- Pico timeout fault uretimi.

Testler:

- CRC16 test vektorleri.
- Packet encode/decode roundtrip.
- ACK/NACK testleri.
- Timeout ve `DISARM` testi.

### Faz 5 - Kamera, Vision Mock ve Overlay

Ana tasklar:

- CameraService mock/gercek kaynak soyutlamasi.
- VisionService mock detection ve opsiyonel Ultralytics model yukleme.
- TrackingService ilk track/stable frame modeli.
- Frontend camera panel ve Canvas/SVG overlay.
- Body, balloon, aim point, track ID ve latency gostergeleri.

Ciktilar:

- Mock kamera veya placeholder frame uzerinde overlay.
- Model dosyasi varsa gercek inference icin hazir servis arayuzu.

Testler:

- Mock frame pipeline unit testleri.
- Model path yoksa kontrollu hata testi.
- Overlay state store testleri.
- UI build ve manuel overlay kontrolu.

### Faz 6 - Decision Engine ve Safety Gates

Ana tasklar:

- Range rules, team/balloon/stability/zone gate modeli.
- Arm/disarm endpointleri.
- Fire request validation; default reject.
- Decision reason ve blocking reasons loglama.
- UI safety gates ve decision panel.

Ciktilar:

- Backend tarafinda guvenlik kapilari uygulanmis karar motoru.
- Fire request sadece gate gecerse Pico komut katmanina ilerler; mock modda dahi loglanir.

Testler:

- Her reject nedeni icin unit test.
- Armed/disarmed state transition testleri.
- E-stop, Pico timeout, target_friend, balloon_missing testleri.
- WebSocket `decision.gates` testi.

### Faz 7 - Motor/Taret Kontrol Paneli

Ana tasklar:

- Jog/home/stop endpointleri.
- Dry-run default motor command path.
- Motor settings schema.
- UI motor/taret paneli.

Ciktilar:

- Fiziksel hareket uretmeyen default motor kontrol paneli.
- Gercek komut icin config ve safety guard gereksinimi.

Testler:

- Dry-run command log testi.
- E-stop aktifken jog reddi.
- Limit switch yon kilidi testi.
- UI build ve manuel dry-run kontrolu.

### Faz 8 - Kalibrasyon ve Renk Dost/Dusman Ayarlari

Ana tasklar:

- Kamera/lens ayarlari.
- HSV/LAB threshold schema ve UI sliderlari.
- Mask preview mock/gercek pipeline.
- Friend/enemy karar metrikleri.

Ciktilar:

- Kalibrasyon ve renk tuning ekranlari.
- Config degisiklik loglari.

Testler:

- Threshold validation testleri.
- Config change log testi.
- Mask preview pipeline smoke testi.

### Faz 9 - Dataset, Replay ve Logging

Ana tasklar:

- Session dosya yapisi.
- Video/frame capture API'leri.
- Replay load/start/pause/seek.
- Error tagging ve JSONL yazimi.
- YOLO dataset export iskeleti.

Ciktilar:

- Veri toplama ve replay ekranlari.
- Senaryo metadata ve log export.

Testler:

- Metadata schema testleri.
- Error tag JSONL testi.
- Replay state transition testi.
- Export klasor yapisi testi.

### Faz 10 - Self-Test Wizard ve Kabul Testleri

Ana tasklar:

- Kamera, model, Pico, E-stop, motor dry-run, servo dry-run ve log self-test adimlari.
- Ready report uretimi.
- P0 kabul kriterlerinin otomasyonla kapsanmasi.

Ciktilar:

- UI self-test wizard.
- KTR/demo icin hazir sistem raporu.

Testler:

- Self-test adim unit/integration testleri.
- Failure injection testleri.
- P0 acceptance smoke testi.

### Faz 11 - KTR Export, Polish ve P1/P2 Genisletme

Ana tasklar:

- KTR-ready markdown report export.
- Latency profiler.
- Model registry compare/rollback.
- Role-based UI.
- Zone editor ve parkur digital twin.

Ciktilar:

- Sunum/KTR icin export edilebilir raporlar.
- P1/P2 profesyonel ekranlar.

Testler:

- Export format testleri.
- Latency metric hesap testleri.
- Role permission testleri.

## İlk Ana Task Önerisi

Ilk ana task olarak **Faz 1 - Proje Scaffold ve Backend Safety Cekirdegi** oneriyorum.

Neden:

- Repo bos; once guvenlik varsayimlari, schema validation, config, loglama ve mock altyapi kurulmadan UI veya hardware komutlarina gecmek dogru degil.
- P0'un neredeyse tum sonraki isleri backend state, WebSocket telemetry ve mock servislerine bagimli.
- `NO_FIRE`, `DISARMED`, dry-run ve reject-by-default davranisi en basta testlenirse ileride guvenlik borcu birikmez.

Bu task sonunda durulacak ve su formatta rapor verilecek:

- Yapilanlar.
- Degisen dosyalar.
- Calistirilan testler.
- Sonuclar.
- Bilinen eksikler.
- Bir sonraki onerilen task.
- Kullanici `devam` demeden sonraki ana taska gecilmeyecek.

## Kullanıcı Onayı Gereken Noktalar

Kod yazmaya baslamadan once asagidaki noktalarda onay gerekiyor:

- Ilk task olarak Faz 1 Backend Safety Cekirdegi ile baslamayi onayliyor musun?
- Paket yoneticisi tercihi: backend icin `uv`/`poetry`/standart `pip`; frontend icin `npm`/`pnpm`.
- Python hedefi `3.12+` olarak kabul edilsin mi?
- Frontend icin Vue 3 + Vite + Pinia + Tailwind aynen kullanilsin mi?
- Serial protokolde gelistirme icin once JSON-line, sonra binary/CRC fazina gecme yaklasimi onayli mi?
- Mock/dry-run default ve gercek donanim komutlari icin explicit config + safety gate zorunlulugu onayli mi?
- Dokumandaki ornek Pico pinleri ilk default profil olarak kullanilsin mi, yoksa gercek pin listesi verilecek mi?
- Repo Git olarak baslatilsin mi, yoksa mevcut dizin Git disi kalmaya devam mi etsin?
