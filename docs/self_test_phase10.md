# Faz 10: Self-Test Wizard ve Kabul Testleri

## Amaç

Self-Test Wizard, yarışma veya demo öncesinde sistemin ana bileşenlerini tek ekrandan doğrulamak için eklendi. Kontrol listesi backend, config, safety, Pico, serial, vision, model registry, motion dry-run, dataset/replay ve logging katmanlarını kapsar.

Self-test readiness does not enable physical fire.

## Readiness Levels

- `not_ready`: Kritik güvenlik veya sistem kontrolü başarısız.
- `demo_ready`: Mock/dry-run ortamı kabul edilebilir; fiziksel donanım yetkisi yok.
- `field_test_ready`: İleride gerçek donanım güvenli şekilde etkinleştirildiğinde kullanılacak seviye.
- `hardware_blocked`: Donanım tarafı açıkça bloke veya eksik.

Bu fazda `hardware_enabled=false` olduğu için başarılı sonuçlar normalde `demo_ready` seviyesinde kalır.

## Step Categories

- system/backend/config
- safety
- pico
- serial
- vision
- model
- motion
- dataset
- replay
- logging

Her step `pending`, `running`, `passed`, `warning`, `failed` veya `skipped` durumlarından birini alır. Critical failed step varsa overall readiness false olur.

## Safety Invariant

Self-test şu invariantı doğrular:

- `DISARMED` veya dry-run standby state
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
- risky serial TX rejected
- fire request rejected by default
- motion commands dry-run only
- model/replay/dataset outputs physical action üretmez

Self-test sonucu READY olsa bile fiziksel atış veya hareket izni anlamına gelmez.

## Dry-Run Behavior

Motion jog, out-of-limit validation, serial DISARM JSON-line ve model inference kontrolleri sadece mock/dry-run path üzerinde çalışır. Gerçek motor, servo, fire veya physical serial komutu üretilmez.

## Rapor Formatı

Her run şu dosyaları üretir:

```text
reports/self_tests/self_test_<timestamp>_<run_id>.json
reports/self_tests/self_test_<timestamp>_<run_id>.md
```

Markdown rapor:

- overall result
- readiness level
- no physical command generated evidence
- passed/warning/failed/skipped counts
- critical failed steps
- suggested actions
- timestamp/build bilgisi
- step listesi

## UI Kullanım Akışı

1. Sidebar üzerinden `Self-Test` ekranı açılır.
2. `Run self-test` butonuna basılır.
3. Overall Readiness kartı ve progress bar izlenir.
4. Warning/failed adımlar Suggested Actions panelinden incelenir.
5. Report bağlantısı ile markdown rapor açılır.
6. Logs ekranında `self_test.*` eventleri filtrelenebilir.

## Gerçek Donanım Gerektiren Kontroller

Bu fazda gerçek donanım gerektiren kontroller fail olarak yorumlanmaz; mock/disabled state'in doğru temsil edilmesi beklenir:

- physical Pico connected
- real serial transport
- real motor movement
- real servo/fire path

Bu kontroller field test fazlarında ayrı güvenlik kapılarıyla genişletilmelidir.

## Mock/Simülasyon Kontrolleri

- Mock Pico telemetry
- Mock serial JSON-line DISARM/ACK
- Motion dry-run jog/stop/out-of-limit
- Vision latest event/overlay metadata
- OpenCV circle detector test adapter
- Dataset/replay service availability

## Yarışma Günü Kullanım Prosedürü

1. Backend ve frontend başlatılır.
2. Safety lock alanında `NO_FIRE`, `DRY RUN`, `REAL HARDWARE DISABLED` doğrulanır.
3. Self-Test çalıştırılır.
4. Critical failure varsa demo/yarışma akışı durdurulur.
5. Warning varsa suggested action listesi uygulanır.
6. Üretilen markdown rapor ekip kayıtlarına alınır.
7. Fiziksel donanım testleri sadece ayrıca onaylanmış saha prosedürüyle yapılır.
