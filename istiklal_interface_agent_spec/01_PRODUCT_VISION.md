# 1. Ürün Vizyonu

## Ürün adı

**İSTİKLAL Komuta Kontrol Merkezi**

## Amaç

Yarışma sisteminin tüm arayüzlerini tek yazılımda toplamak:

- Kullanıcı arayüzü
- Görüntü işleme arayüzü
- Pico 2 donanım arayüzü
- Motor/servo arayüzü
- Güç ve acil stop arayüzü
- Yazılımsal mesaj arayüzleri
- Veri toplama ve replay arayüzü
- Log ve test arayüzü

## Profesyonel seviye beklentisi

Bu arayüz, öğrenci projesi gibi görünmemeli. Küçük ölçekli bir savunma/robotik komuta-kontrol istasyonu gibi çalışmalı.

Arayüz sadece şunu göstermemeli:

```text
target 0.82
```

Bunun yerine şunu göstermeli:

```json
{
  "track_id": 17,
  "body_class": "helicopter",
  "body_confidence": 0.91,
  "team": "enemy",
  "team_confidence": 0.88,
  "balloon_detected": true,
  "balloon_confidence": 0.94,
  "aim_point_px": [642, 381],
  "range_m": 9.7,
  "stable_frames": "5/5",
  "decision": "ENGAGE_ALLOWED",
  "reason": "Enemy helicopter, valid range, stable track, balloon locked"
}
```

## Sistem çıktısı

Arayüz, sistemin sadece sonuçlarını değil, **karar gerekçesini** de göstermelidir:

- Neden ateş izni yok?
- Hedef dost mu?
- Balon bulunamadı mı?
- Menzil uygun değil mi?
- Pico 2 bağlantısı koptu mu?
- Track stabil değil mi?
- Yasak alan ihlali mi var?

## Kullanıcı rolleri

### Operatör

- Görev modunu seçer.
- Manuel modda joystick/UI ile kontrol eder.
- Güvenli şekilde arm/disarm yapar.
- Sistem durumunu izler.

### Görüntü işleme sorumlusu

- Kamera ve model ayarlarını yapar.
- YOLO, balon ve renk doğrulama çıktılarını inceler.
- Veri toplar ve replay yapar.

### Donanım/entegrasyon sorumlusu

- Pico 2 pinlerini doğrular.
- Serial bağlantıyı test eder.
- Motor/servo testlerini yapar.
- Acil stop ve limit durumlarını kontrol eder.

### Test sorumlusu

- Senaryoları çalıştırır.
- Logları ve raporları dışa aktarır.
- Hatalı frame/video örneklerini veri havuzuna ekler.

## Başarı tanımı

Arayüz başarılı sayılırsa:

- Operatör tek ekrandan sistemin hazır olup olmadığını anlar.
- Her hedef için sınıf, dost/düşman, balon, mesafe ve karar durumu gösterilir.
- Ateşleme sadece güvenlik kapıları geçilirse mümkün olur.
- Pico 2 pinleri ve telemetry canlı doğrulanır.
- Sistem log üretir.
- Replay ile model hataları incelenebilir.
- KTR ve final sunumu için ekran görüntüsü, log ve test raporu üretilebilir.
