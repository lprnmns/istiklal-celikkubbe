# 13 — Risk Kaydı ve Go/No-Go Kapıları

## 1. Risk değerlendirme ölçeği

- Olasılık: Düşük / Orta / Yüksek.
- Etki: 1 düşük, 5 yarışmadan elenme/güvenlik/büyük puan kaybı.
- Risk sahibi, riski tek başına çözmek zorunda değildir; karar ve eskalasyondan sorumludur.

## 2. Ana risk kaydı

| ID | Risk | Olasılık | Etki | Erken sinyal | Sahip | Önleme | Tetiklenirse fallback |
|---|---|---|---:|---|---|---|---|
| R-01 | Fiziksel ateş güvenlik motorunu atlar | Yüksek | 5 | Gateway dışı write, FIRE_REQUIRED_FRAMES=1 | Kontrol + Güvenlik | SAFE-05…07 | Gerçek fire kapalı; dry-run/HIL; son imzalı safety release |
| R-02 | full_active endpoint’i fire’ı tek çağrıyla açar | Yüksek | 5 | dry_run false ve allow fire audit’siz | Kontrol | SAFE-11 | Endpoint fiziksel fire için kapalı |
| R-03 | E-Stop tetik/servo enerjisini kesmez | Yüksek | 5 | 24 V kesilirken 6 V canlı | Donanım/Güvenlik | SAFE-01, SAFE-04 | Y4 ve bütün canlı atış NO-GO |
| R-04 | Firmware/pin/protokol uyumsuz | Yüksek | 5 | GP18/GP20 çelişkisi, probe yanıtı farklı | Firmware | SAFE-01, SAFE-02 | Enerji kapalı; tek kanonik build ve yeniden kablo audit |
| R-05 | ACK’siz komut başarılı sayılır/stale replay | Yüksek | 5 | “sent” var, gerçek ACK yok | Firmware + Backend | SAFE-05, SAFE-09 | Queue flush; physical arm kapalı |
| R-06 | Eski browser/frame fiziksel komut üretir | Orta-Yüksek | 5 | Tarayıcı kapalıyken track sürüyor | Vision/Platform | PLAT-10 | Browser input live fire’dan çıkar; safe stop |
| R-07 | 15 m başarı tekrarlanamaz | Orta | 5 | Son 10’da 9 altı, CO₂ etkisi | Kontrol + Saha | OPS-02, OPS-04, VID-02 | Son kanıtlı model/config; Y6 çıkar; ekstra çekim tamponu |
| R-08 | Y3 yalnız tek eksen veya duruş yetersiz | Orta | 5 | Tilt/pan’dan biri hareket/duruş göstermiyor | Donanım | SAFE-03, VID-03 | Y3 çekim NO-GO; hız düşür ve fiziksel düzelt |
| R-09 | Y4 kanıtı görsel olarak anlaşılmaz | Orta | 5 | Atış sayısı veya buton kadraj dışı | Video + Test | VID-04, VID-07 | Yedek geniş take; kurgu ile olay uydurulmaz |
| R-10 | Y5 tracker ID/latency/osilasyon sorunu | Yüksek | 5 | ID switch, p95 büyüme, limite çarpma | Vision + Kontrol | VID-05, PLAT-10 | Son stabil tracker/PID; tetik kapalı |
| R-11 | Opsiyonel Y6 zorunlu videoyu bozar | Yüksek | 5 | FPS düşer, 15 m label sıçrar | Vision + Lider | VID-06 | Y6 videodan tamamen çıkar |
| R-12 | Yanlış aktif model/surrogate gerçekmiş gibi görünür | Yüksek | 4 | runtime profile opencv surrogate | Vision | A3-02, A3-03 | Açık model-yok durumu; A3 fire NO-GO |
| R-13 | Dost sınıfı balloon diye işlenir | Yüksek | 5 | box.cls okunmuyor | Vision + Güvenlik | A3-03, A3-08 | Model kapalı; NO_FIRE |
| R-14 | IFF mock/sabit kırmızı-mavi varsayımı | Yüksek | 5 | mock_team veya hard-code | Vision | A3-04 | A3 fire kapalı; gerçek saha profili |
| R-15 | Yanlış body–balon linki dost vurur | Yüksek | 5 | ambiguous linkte fire adayı | Vision | A2-02, A3-05, A3-08 | Live fire durur; stable-only threshold |
| R-16 | Menzil sahte/identity calibration | Yüksek | 5 | sıfır hata/identity matrix | Vision | OPS-04, A3-06 | İlgili sınıf angajmanı NO-GO |
| R-17 | Aşama 1 yanlış sıra/skor | Orta | 4 | ilk hedef veya bonus yanlış | Backend + Operatör | A1-03, A1-04 | Muhafazakâr manuel read-back ve versioned scoring |
| R-18 | Aşama 2 yalnız nearest target ile 3/3 kaçırır | Yüksek | 4 | aynı hedefe tekrar, erken çıkış | Kontrol | A2-01…A2-05 | Son 105+ priority profile |
| R-19 | Aşama 3 üç ardışık miss ile 0 | Orta-Yüksek | 5 | miss streak 2, geç acquire | Kontrol + Vision | A3-09 | Güvenli erken acquire/reengage; aşırı threshold gevşetme yok |
| R-20 | Ebat 60 cm üstü ve 20 puan kaybı | Orta | 4 | ölçüm 59,5–60+ | Donanım | OPS-01 | Çıkıntı/montaj küçült; skor hedefini güncelle |
| R-21 | CO₂ yaklaşık 30 atışta performans düşürür | Yüksek | 4 | hız/isabet trendi düşer | Saha + Donanım | OPS-02, OPS-03 | Erken tüp değişimi ve yedek plan |
| R-22 | USB/COM/kamera index sahada değişir | Yüksek | 4 | config düzenleme gerekiyor | Platform | PLAT-04, PLAT-05 | Profile-locked Wizard; kod düzenleme yok |
| R-23 | Windows dönüşümü video takvimini tüketir | Orta-Yüksek | 4 | GPU/device agent geçmiyor | Lider + Platform | PLAT-06 | Linux golden rig |
| R-24 | Disk release/log ile dolar | Yüksek | 4 | boş alan hızla düşer | Platform | PLAT-01…03 | Release lane kapalı; kontrollü retention |
| R-25 | Release testi recursive package üretir | Yüksek | 4 | her run boyut katlanır | Platform | PLAT-02 | Bounded temp package veya son manuel artefact |
| R-26 | Self-test yanlış overall_ready verir | Orta-Yüksek | 5 | hardware disabled iken ready | Platform + Güvenlik | PLAT-11 | Görev/fire readiness kapalı |
| R-27 | Dirty worktree kullanıcı işini kaybettirir | Orta | 4 | reset/clean önerisi | Tüm geliştiriciler | GOV-03, GOV-04 | Patch/hash backup; değişiklik durur |
| R-28 | Testlerin bir kısmı davranış yerine string kontrolü | Yüksek | 3 | bozuk davranışta test yeşil | Test | EVD-04 | Kritik contract/negative test önceliği |
| R-29 | Kaynak/target revizyonu kaçırılır | Orta | 4 | hash değişikliği | Lider + Test | GOV-02, A3-01 | Etkilenen acceptance yeniden açılır |
| R-30 | Video linki/KYS idari hatası | Düşük-Orta | 5 | oturum kapalı link açılmıyor | KYS sorumlusu | VID-09 | Yedek upload/link; 12:00 iç teslim |
| R-31 | Ekip kapasitesi planı taşımaz | Orta | 5 | P0 sahipsiz/gecikmiş | Takım Lideri | GOV-01, günlük gate | Y6/Windows/UI kes; P0 tamponu koru |
| R-32 | 30 dk kurulum veya 10 dk bakım aşılır | Orta | 4 | prova süreleri uzun | Saha Operatörü | OPS-03 | Kit/iş sırası sadeleşir; gereksiz özellik çıkar |

## 3. Go/No-Go kapıları

### G0 — Plan ve sahiplik

GO:

- Kullanıcı planı onayladı.
- P0 rol sahipleri belli.
- Donanım test alanı ve güvenlik sorumlusu mevcut.

NO-GO:

- E-Stop/power kararını kimin vereceği belli değil.

### G1 — Golden baseline ve donanım gerçeği

GO:

- 10 baseline run.
- Commit/config/model/firmware/device manifesti.
- As-built pin/power audit.
- Ebat ölçümü.

NO-GO:

- Aktif firmware/pin belirsiz.
- Baseline tekrar üretilemiyor.

### G2 — Güvenli fiziksel komut

GO:

- E-Stop hareket ve tetik enerjisini kesiyor.
- Tek kanonik firmware.
- SafetyDecision + CommandGateway.
- full_active yetkili/preflight bağlı.
- Stale/ACK/queue testleri yeşil.

NO-GO:

- Gateway bypass.
- ACK’siz success.
- E-Stop sonrası enerji/atış.
- Reconnect sonrası otomatik arm.

### G3 — Y1–Y5 ayrı yetenek acceptance

GO:

- Y1 gerçek runtime.
- Y2 15 m.
- Y3/Y4 üçer ardışık.
- Y5 üç ardışık.

NO-GO:

- Herhangi zorunlu yetenek yalnız mock, tek eksen veya tek şanslı run.

### G4 — Video release

GO:

- Aynı rig ile iki tam prova.
- 2–5 dakika.
- Release/hash ve iki günlük çekim tamponu.

NO-GO:

- Y6/Windows/yeni feature zorunlu akışı bozuyor.

### G5 — Teslim

GO:

- YouTube iki cihaz/ağda.
- KYS iç teslim 12:00.
- Gönderim kanıtı ve yedek.

NO-GO:

- Link erişilemiyor, sıra/numara/süre yanlış.

### G6 — Aşama 1

GO:

- A1-06 son 10 run kriterleri.

NO-GO:

- Auto komut manual modda.
- Yanlış sıra/ilk hedef.

### G7 — Aşama 2

GO:

- Üç seri 105+, biri 120.

NO-GO:

- Zero-hit tur, yanlış association veya nearest-only kararsızlığı.

### G8 — Aşama 3

GO:

- Üç seri 120+, biri 140+.
- Dost vuruşu 0.
- Üç ardışık miss yok.

NO-GO:

- Mock IFF, sahte menzil, ambiguous linkte fire veya yanlış sınıf mapping.

### G9 — Final saha release

GO:

- 30 dk kurulum ve 10 dk bakım provalı.
- CO₂/atış bütçesi.
- Ebat.
- Final dossier ve mülakat.
- Aynı release manifesti.

NO-GO:

- Son dakika hardware/model/OS değişimi acceptance olmadan.

## 4. Y6 karar matrisi

| Durum | Karar |
|---|---|
| Y1–Y5 henüz iki tam yeşil prova değil | Y6 NO-GO |
| 4×3 matris eksik | Y6 NO-GO |
| 15 m etiket kararsız | Y6 NO-GO |
| Y5 latency/FPS kötüleşiyor | Y6 NO-GO |
| Tümü yeşil ve 45 sn altında anlatılıyor | Y6 GO |

## 5. Windows karar matrisi

| Durum | Karar |
|---|---|
| Çekim bilgisayarı Windows olmak zorunda değil | Linux golden rig |
| Windows device access/GPU/offline/preflight 27 Temmuz’da geçmiyor | Linux golden rig |
| Windows zorunlu ve bütün kapılar üç soğuk başlangıçta geçiyor | Windows dondurulabilir |
| Son hafta driver/OS değişikliği gerekiyor | Değişiklik NO-GO |

## 6. Derhal çalışma durdurma koşulları

- E-Stop sonrası herhangi fiziksel hareket veya tetik.
- Dost/insan/unknown/ambiguous aday için fire komutu.
- Gateway dışından fiziksel write.
- Kamera/Pico stale iken hareket/atış.
- Limit/zone dışına kontrolsüz yönelim.
- Güvenli backstop veya yetkili safety gözlemcisi olmadan fiziksel test.
- Config/firmware pin gerçeğinin bilinmemesi.
- Diskin log/release nedeniyle kritik dolulukta olması.

Durdurma, görevin başarısızlığı değil güvenli planın doğru çalışmasıdır.
