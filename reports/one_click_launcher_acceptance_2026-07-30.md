# ISTIKLAL tek tık launcher kabul kaydı

Tarih: 2026-07-30

## Native launcher

- `8000-8003` doluyken boş porta otomatik geçti.
- `/api/health` başarılı oldu ve frontend aynı porttan GET ile servis edildi.
- İkinci `start` yeni süreç açmadan mevcut URL'yi kullandı.
- Aynı tek tık komutu çalışan, launcher'a ait süreci durdurdu.
- Hızlı çift tıklamada yalnız bir işlem yürüdü; ikinci sunucu oluşmadı.
- PID oluşturulma zamanı doğrulanmadan süreç sonlandırılmıyor.
- Test sonunda native launcher kapalı bırakıldı.

## Docker TEST launcher

- Compose yapılandırması doğrulandı ve image başarıyla build edildi.
- Hafif TEST image'ı Torch, Ultralytics ve CUDA indirmiyor.
- Docker boş host portu olarak `32797`, ikinci çalıştırmada `32798` seçti.
- `/api/health` ve frontend GET başarılı oldu.
- Container içi güvenli profil doğrulandı:
  - `dry_run=true`
  - `hardware_enabled=false`
  - `physical_command_enabled=false`
  - `allow_physical_motion=false`
  - `allow_physical_fire=false`
  - `serial.transport_mode=mock`
  - `serial.serial_tx_enabled=false`
- Aynı Docker tek tık komutu container/network'ü durdurup kaldırdı; kalıcı
  volume'ler korundu.
- Hızlı çift tıklama kilidi doğrulandı.
- Test sonunda Docker servisi kapalı bırakıldı.

## Otomatik kontroller

`release/one_click/tests/test_one_click_launchers.py`:

- Dolu port boş kabul edilmez.
- Native hızlı çift tık ikinci işlemi reddeder.
- Docker hızlı çift tık ikinci işlemi reddeder.
- Eski/yeniden kullanılmış PID başka bir sürecin kapatılmasına yol açmaz.

Python compile, shell syntax, Compose config ve `git diff --check` kontrolleri
başarılıdır.
