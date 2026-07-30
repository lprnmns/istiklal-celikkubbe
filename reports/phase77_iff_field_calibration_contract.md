# P1 — Aşama 3 gerçek IFF saha referansı sözleşmesi

Tarih: 2026-07-15. HSV ayarları tek başına A3 physical fire için yeterli değildir.

## Kalibrasyon akışı

1. Bilinen enemy gövde gerçek kamera ROI'sinde üç farklı frame/capture ID ile temporal olarak ENEMY olur.
2. Operatör `Son ROI’yi referans yap` ile bu üç gerçek sonucu kaydeder.
3. Aynı işlem bilinen friend gövde için üç farklı frame/capture ID ile yapılır.
4. Altı referans, aktif HSV profil hash'i ve gerçek ROI provenance ile `IFF FIELD PROFILE VERIFIED` üretir.

Mock sample, kullanıcı beyanı veya balon rengi referans olamaz. Her IFF referansı real body ROI, yeterli body piksel, beklenen team ve unique capture/frame ister. Enemy referansı ayrıca temporal live-fire consensus ister.

HSV/threshold profil değiştiğinde tüm referanslar geçersizleşir. A3 yarışma profilinde referans ekleme/reset ve HSV ayar değişimi `A3_PROFILE_LOCKED` ile engellenir.

DecisionEngine, current-frame real ROI + temporal consensus + geçerli saha referansı olmadan `a3_iff_real_roi_unavailable` üretir.

## Otomatik kanıt

`backend/tests/test_phase77_iff_field_calibration_contract.py`:

- üç enemy tek başına yeterli olmadığını;
- üç enemy + üç friend gerçek frame referansının IFF'i açtığını;
- HSV profil değişiminin kalibrasyonu sıfırladığını;
- mock sample'ın referans olarak reddedildiğini doğrular.
