# 00 — Kaynaklar, Gerçekler ve Varsayımlar

## 1. Kaynak hiyerarşisi

Çelişki halinde aşağıdaki sıra kullanılır:

1. Güncel resmî TEKNOFEST şartnamesi, resmî parkur ve hedef dosyaları.
2. KYS ve resmî yarışma duyuruları.
3. Takımın teslim edilmiş ÖTR/KTR belgeleri.
4. Fiziksel ölçüm, video, telemetri ve test kanıtı.
5. Çalışan kaynak kod ve firmware.
6. Repo içi raporlar ve bağlam paketi yorumları.
7. Varsayım veya plan.

KTR’de yazılmış bir iddia, fiziksel sistemde ölçülmedikçe “kanıtlandı” sayılmaz.

## 2. İncelenen ana kaynaklar

Bağlam kökü:

ISTIKLAL_Codex_Context_2026-07-15/ISTIKLAL_CODEX_CONTEXT

Ana belgeler:

- sources/01_official_technical_spec_2026.pdf
- sources/02_team_critical_design_report.pdf
- sources/03_parkur_layout_drawing.pdf
- sources/04_official_target_models.3mf
- sources/05_team_balloon_test.mp4
- 00_PROVENANCE_AND_GROUND_TRUTH.md
- 01_COMPETITION_MASTER_CONTEXT.md
- 02_OFFICIAL_SPEC_PAGE_BY_PAGE.md
- 03_TEAM_KTR_PAGE_BY_PAGE.md
- 04_PARKUR_TARGET_MODELS_AND_TASK_LOGIC.md
- 05_CURRENT_STATE_AND_VIDEO_EVIDENCE.md
- 09_ACCEPTANCE_TESTS_AND_DEFINITION_OF_DONE.md
- 13_EXECUTION_SCHEDULE_TO_VIDEO.md

Repo içinden özellikle incelenen alanlar:

- backend/app/services
- backend/app/api
- backend/app/schemas
- backend/tests
- frontend/src
- firmware
- eski_sistem_arayüz
- config/config.yaml
- start_linux.sh
- start_windows.bat
- reports
- exports/release
- logs

## 3. Resmî ve doğrulanmış gerçekler

| Konu | Gerçek |
|---|---|
| Video son teslim | 10 Ağustos 2026, 17:00 |
| Finalist açıklaması | 24 Ağustos 2026 |
| Video biçimi | Tek YouTube videosu, 2–5 dakika, en az 720p |
| Video sıra | Y1–Y5 resmî sırada, açık numaralı; Y6 opsiyonel |
| Toplam puan | 500 |
| ÖTR/KTR/sunum | 10 + 50 + 40 |
| Ebat | En uzun boyut 60 cm veya altı: 20; 60–100 cm: 0 |
| Aşama 1 | Manuel, en çok 100; sonraki aşama için en az 30 |
| Aşama 2 | Otonom, en çok 120; sonraki aşama için en az 20 |
| Aşama 3 | Otonom IFF, en çok 160; ödül uygunluğu için en az 10 |
| Final kurulum | 30 dakika |
| Toplam bakım | 10 dakika; her talep en az 30 saniye |
| E-Stop | Dışarı uzanan kablolu fiziksel E-Stop zorunlu |
| Yasak bölgeler | Harekete yasak ve atışa yasak bölgeler ayrı olmalı |
| Balon rengi | Değişebilir; dost ve düşmanda aynı olabilir |
| Dost/düşman | Gövde renkleri farklıdır; gerçek renk eşlemesi sabit verilmemiştir |

## 4. Repo ve fiziksel kanıt gerçekleri

| Konu | 15 Temmuz 2026 durumu |
|---|---|
| Branch / commit | main-2 / 83cee632b12b34148c4f94cb1b37b74abf9dc2b6 |
| Çalışma ağacı | Kirli; kullanıcı değişiklikleri korunmalı |
| Repo boyutu | Yaklaşık 70 GB |
| exports/release | Yaklaşık 54 GB |
| logs/backend.jsonl | Yaklaşık 8,7 GB; rotation yok |
| backend/.venv | Yaklaşık 5,4 GB |
| Frontend type check | Geçti |
| Backend test durumu | Yaklaşık yüzde 35’e kadar geçti; release testi paket kopyalama nedeniyle diski doldurdu |
| Seçilmiş çekirdek backend testleri | 166 test geçti; toplam testlerin önemli bölümü gerçek davranış yerine string/yorum varlığı kontrol ediyor |
| Firmware derleme | Arduino Pico 2 compile ve Python/MicroPython syntax compile geçti |
| Frontend production build | Geçti; unit/component test altyapısı bulunmadı |
| Fiziksel video | İki balonun ardışık imhasını gösteriyor |
| Kanıtlanmayanlar | Ölçülü 15 m, gerçek E-Stop, iki eksenli hareketli takip, sınıflandırma, Windows |

## 5. Kaynak bütünlüğü notu

Bağlam klasöründe 167 dosya vardır; manifest 164 dosya bildirir. SHA256SUMS içindeki payload’ların biri uyuşmaz:

- Dosya: 10_CODEX_BOOTSTRAP_PROMPT.md
- Beklenen SHA-256: 86f40b160d5f5d92dcebff38cc17e6eacc9e45888c65eab232179a7524de8c12
- Mevcut SHA-256: aab3431e429682ffbd9ef6ac2e337a6c95f19715df3c28d2577134dd9ad727b7

Bu dosya paket üretiminden sonra değişmiş kabul edilir ve yarışma gereksinimleri için otoritatif kaynak olarak kullanılmaz. Resmî PDF, parkur, 3MF ve bunların sayfa metinleri esas alınır.

## 6. Bilinen belirsizlikler

| ID | Belirsizlik | Plan kararı |
|---|---|---|
| U-01 | Gerçek ÖTR ve KTR sayısal puanları yok | Onay sonrası ilk gün bulunacak; toplam hedef formülü güncellenecek |
| U-02 | Çekim/final bilgisayarının işletim sistemi kesin değil | Video için çalışan Linux golden rig varsayılır; Windows yalnız zorunluysa kritik yola girer |
| U-03 | Gerçek aktif firmware ve pin kablolaması çelişkili | Fiziksel süreklilik ölçümü ve fotoğraflı pin sözleşmesi olmadan enerji verilmez |
| U-04 | Hava aracı modelinin hazır olma ve gerçek kalitesi bilinmiyor | Y6 ve A3 için bağımsız model go/no-go kapısı kullanılır |
| U-05 | Final tarihi kesin değil | Video sonrası plan relatif haftalarla yürütülür; resmî duyuruda yeniden bazlanır |
| U-06 | Dost/düşman gerçek renkleri sabit değil | Saha profiliyle yapılandırılır; hard-code yasaktır |
| U-07 | Nihai hedef dosyaları güncellenebilir | Haftalık resmî dosya hash kontrolü yapılır |
| U-08 | Aşama 1 iki cezanın kümülatif olup olmadığı açık değil | En muhafazakâr yorumla hem doğru sıra hem ilk Balistik Füze zorunlu kabul edilir |
| U-09 | Takım kapasitesi ve rol sahipleri bilinmiyor | Plan rol bazlıdır; onay sonrası kişilere atanır |
| U-10 | Ebat yaklaşık 60 cm beyan edilmiş | Final konfigürasyonunda 58–59 cm tasarım marjı hedeflenir |
| U-11 | Aktif runtime profilinin gerçek model mi surrogate mı olduğu kullanıcı algısında belirsiz | Runtime truth esas alınır; opencv_live_circle_surrogate gerçek model diye sunulmaz |

## 7. Plan varsayımları

- Güvenli backstop ve kontrollü fiziksel test alanına erişim vardır.
- Donanım, yazılım ve video işleri en azından kısmen paralel yürütülebilir.
- Mevcut balon takip çekirdeği yeniden üretilebilir.
- Yarışma kapsamında kullanılan atış düzeneği ve hedefler resmî kurallara uygundur.
- Testler yetkili ekip üyeleri, gözlemci ve yazılı checklist ile yürütülür.
- Golden baseline alınmadan dosya temizliği veya büyük refactor yapılmaz.
- Video için opsiyonel Y6’nın çıkarılması başarısızlık değil, risk yönetimi kararıdır.

## 8. Onay sonrası kullanıcıdan alınacak beş kritik bilgi

1. ÖTR ve KTR’nin gerçek puanları.
2. Ekip üyeleri, rolleri ve günlük erişilebilir saatleri.
3. Çekim bilgisayarı ile final bilgisayarının işletim sistemi/GPU bilgisi.
4. Aktif firmware, gerçek Pico modeli, pinout ve güncel kablo fotoğrafları.
5. Hava aracı modelinin dosyası, veri seti, sınıf sırası ve ölçülmüş metrikleri.

Bu bilgiler planı başlatmak için yararlıdır; ancak planın onaylanmasına engel değildir.
