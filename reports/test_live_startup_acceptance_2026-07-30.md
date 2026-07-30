# Test / Canlı Sistem başlangıç kabulü

Tarih: 2026-07-30

## Operatör matrisi

| UI seçimi | Gateway profili | Pico trigger durumu | Fiziksel hareket | Fiziksel FIRE | Takip |
|---|---|---|---|---|---|
| TEST | `LIVE_TEST` | `ARM,0` ACK zorunlu | Preflight uygunsa açık | Kapalı | Kokpit açılınca otomatik |
| CANLI SİSTEM | `LIVE_TEST` | `ARM,1` ACK zorunlu | Preflight uygunsa açık | Preflight uygunsa açık | Kokpit açılınca otomatik |

`DRY_RUN` backend/mock testleri için korunur fakat ana operatör başlangıç
seçeneği değildir.

## Başlangıç davranışı

- `Windows Taret HIL` kayıtlı profili varsayılan seçilir.
- Profil kamera indexi yerine mümkün olduğunda USB stable identity ile,
  Pico ise seri numarası/VID:PID ile yeniden eşlenir.
- Kamera ve Windows capture worker için kısa warm-up süresince preflight tekrar
  çalıştırılır.
- TEST için `physical_motion_enabled`, CANLI SİSTEM için
  `physical_fire_enabled` doğrulanmadan kokpite geçilmez.
- Eksik koşullar başlangıç ekranında gate detayı ve reason code ile gösterilir.
- Başarılı geçiş `autotrack=1` ile kokpitte takip döngüsünü otomatik başlatır.

## Korunan gerçek engeller

- `PICO_HANDSHAKE_FAILED`
- `PICO_CONNECTION_FAULT`
- `PICO_HEARTBEAT_STALE`
- `ESTOP_ACTIVE` / `ESTOP_STATE_UNKNOWN`
- `CAMERA_STALE`
- `MOTION_FAULT_OR_ESTOP`
- hareket/soft-limit/forbidden-zone reason code'ları
- TEST için `ARM,0` başarısızsa `ACTUATOR_DISARM_FAILED`
- CANLI SİSTEM için `ARM,1` başarısızsa `ACTUATOR_ARM_FAILED`

Bunlar kaynak kod veya environment kilidi değildir; bağlı fiziksel sistemin
görünür durumudur. Düzeltildikten sonra UI üzerinden preflight yeniden
çalıştırılabilir.

## Windows saha kurulumu

- Host: `100.122.178.87`, proje: `C:\ISTIKLAL`
- Uygulama: `http://127.0.0.1:8000/`
- Varsayılan profil: `windows-taret-hil`
- Kamera: `camera-index:2`, 640x480 MJPG
- Pico: `COM8`, 460800 baud, serial `0416D21629149FFB`
- Balon modeli SHA-256:
  `206BE8354B179A04A52A2E690727BCF2515D7277406B143E3482FBB2C36D1F58`
- Tek tık: `C:\ISTIKLAL\ISTIKLAL_TEK_TIK.cmd`
- Windows kalıcı başlatma Task Scheduler üzerinden, aç/kapat kararı yeni
  launcher üzerinden yapılır.
- Gerçek tek-tık durdur -> başlat -> health -> varsayılan profil testi geçti.
- Son durumda Windows sunucusu çalışıyor; yerel Ubuntu sunucusu kapalı.

## Yazılım doğrulaması

- Gateway, tracking, trigger, E-Stop, kamera ownership, dijital ikiz, takip
  tuning, setup profil ve yeni başlangıç kontrat testleri geçti.
- Frontend `vue-tsc` ve production Vite build geçti.
- Python compile ve `git diff --check` geçti.
- Windows PowerShell launcher parser kontrolü geçti.
- Bu kabul sırasında hareket veya FIRE komutu gönderilmedi.
