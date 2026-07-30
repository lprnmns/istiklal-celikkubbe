# Faz 7 Motion/Turret Dry-Run Mimarisi

## Amaç

Bu faz taret ve motor kontrol yüzeyini, backend motion validation katmanını ve dry-run komut yolunu kurar. Gerçek motor hareketi, gerçek Pico/serial motion komutu ve atış/servo/tetik komutu bu fazda yoktur.

Varsayılan güvenlik durumu korunur:

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- `motion.real_motion_enabled=false`

## Backend Bileşenleri

- `app.schemas.motion`: motion state, settings, komut istekleri ve komut response şemaları.
- `app.services.motion_service`: dry-run komut planlama, soft limit validation, E-stop/limit/fault engelleri ve JSONL loglama.
- `app.services.turret_service`: taret katmanı için servis sarmalayıcı.
- `app.api.motion`: `/api/motion/*` endpointleri.

## Motion State Modeli

`motion_state` değerleri:

- `IDLE`
- `JOGGING`
- `HOMING`
- `SCANNING`
- `TRACKING_DRY_RUN`
- `STOPPED`
- `FAULT`

Durum nesnesi pan/tilt derece ve step değerlerini, hedef açıları, limit switch durumlarını, E-stop, driver, `dry_run`, son komut ve son hata bilgisini taşır.

## Motor Settings

`config/config.yaml` altında `motion:` bölümü eklendi. Varsayılan değerler placeholder kabul edilir ve kalibrasyon gerektirir.

Önemli alanlar:

- pan/tilt min-max soft limitleri
- steps per degree
- max speed ve acceleration
- jog step
- tracking gain
- deadband
- scan min/max/speed
- soft limits enabled

Backend validation:

- `pan_min_deg < pan_max_deg`
- `tilt_min_deg < tilt_max_deg`
- `scan_min_deg < scan_max_deg`
- speed/acceleration negatif olamaz
- steps per degree `> 0`
- `motion.dry_run=false` reddedilir
- `motion.real_motion_enabled=true` reddedilir

## Endpointler

- `GET /api/motion/status`
- `GET /api/motion/settings`
- `PUT /api/motion/settings`
- `POST /api/motion/jog`
- `POST /api/motion/go-to`
- `POST /api/motion/home`
- `POST /api/motion/stop`
- `POST /api/motion/scan/start`
- `POST /api/motion/scan/stop`
- `POST /api/motion/track-dry-run`

## Dry-Run Command Path

Her komut `MotionCommandResponse` döndürür:

- `accepted`
- `dry_run`
- `command_id`
- `command_type`
- `requested_target`
- `blocking_reasons`
- `safety_gates`
- `generated_steps`
- `no_physical_command_generated=true`
- `reason`

Kabul edilen komutlar sadece simüle state üretir. Serial/Pico transport katmanına motion mesajı gönderilmez.

## Motion Validation Kuralları

Komut reddi üreten başlıca nedenler:

- sistem ARMED ise `system_not_test_safe`
- E-stop aktifse `estop_active`
- soft limit dışı hedefte `pan_soft_limit` veya `tilt_soft_limit`
- limit switch aktif yönde hareket isteğinde ilgili limit reason
- `FAULT` durumunda stop dışı komutta `motion_fault`
- hardware/real motion aktifleşmeye çalışırsa `real_motion_disabled_by_phase7`

`stop` ve `scan_stop` güvenli durdurma komutları olarak dry-run state içinde kabul edilir.

## Safety Gate Entegrasyonu

Decision engine gate listesine şu motion gate’leri eklendi:

- `motion_soft_limits_gate`
- `motion_estop_gate`
- `motion_fault_gate`
- `motion_driver_gate`
- `motion_dry_run_gate`

Driver disabled ve dry-run gate’leri Phase 7’de bilgilendirici/warning seviyesinde kalır. Fiziksel hareket yetkisi vermez.

## WebSocket Eventleri

Eklenen eventler:

- `motion.status`
- `motion.command_requested`
- `motion.command_accepted_dry_run`
- `motion.command_rejected`
- `motion.stopped`
- `motion.fault`
- `motion.settings_updated`

Frontend system store bu eventleri motion store’a işler.

## Frontend Kullanım Akışı

`/motion` ekranı:

- motion state kartı
- pan/tilt pozisyon göstergeleri
- E-stop, driver ve limit switch durumları
- dry-run uyarısı
- jog kontrolleri
- go-to dry-run formu
- home/stop/scan kontrolleri
- tracking preview paneli
- 2D taret görselleştirmesi
- editable motion settings paneli
- komut log tablosu

Dashboard’a motion status kartı eklendi. Safety ekranındaki gate matrisi motion gate’lerini decision gate listesi içinde gösterir.

## Bilinçli Olarak Yapılmayanlar

- Gerçek motor hareketi yok.
- Gerçek Pico/serial motion komutu yok.
- Fire/servo/tetik komutu yok.
- Closed-loop tracking yok.
- Kalibrasyon wizard yok.
- Motion settings kalıcı config dosyasına yazılmıyor; runtime memory state olarak kalıyor.
