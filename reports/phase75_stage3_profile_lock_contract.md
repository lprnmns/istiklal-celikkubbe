# P1 — Aşama 3 yarışma profili kilidi

Tarih: 2026-07-15. Aşama 3 yarışma profili `COMPETITION` seçilip aktif aşama `stage3` olduğunda perception kararını değiştirebilecek saha profili mutasyonlarını engeller.

Kilit aşağıdakileri `409 A3_PROFILE_LOCKED` ile reddeder:

- HSV IFF renk profili güncellemesi;
- A3 range observation ekleme/silme/doğrulama/reset;
- kamera runtime profil/controls/default reset;
- vision runtime profil/preset/model reload;
- model paket/model activation veya deactivation.

Bu ek bir operatör onayı, token veya şifre değildir. Yarışma başladıktan sonra hedef sınıfı, IFF, kamera ya da menzil varsayımının sessizce değişmesini önleyen görünür bir bütünlük kuralıdır. Aşama 1 planı/timer'ına bağımlı değildir.

`backend/tests/test_phase75_stage3_profile_lock.py`, competition profil seçimi preflight'ı yeşil olmasa dahi bu mutasyonların aynı reason code ile engellendiğini doğrular.
