# ISTIKLAL tek tık çalıştırma

## Normal kullanım

Windows'ta proje ana klasöründeki `ISTIKLAL_TEK_TIK.cmd`, Linux'ta
`ISTIKLAL_TEK_TIK.desktop` kullanılır.

- Sistem kapalıysa backend ve hazır frontend tek süreçte başlatılır.
- `8000-8099` aralığındaki ilk boş port otomatik seçilir.
- Sağlık kontrolü geçince tarayıcı açılır ve erişim adresleri
  `ISTIKLAL_URL.txt` dosyasına yazılır.
- Aynı kısayola yeniden basılırsa yalnız bu başlatıcının açtığı ISTIKLAL
  süreci durdurulur.
- Zaten kapalı olan sistemi durdurmak hata oluşturmaz. Hızlı çift tıklama ikinci
  sunucuyu açmaz.

İlk kullanımdan önce `backend/.venv` kurulmuş ve `frontend/dist/index.html`
üretilmiş olmalıdır. Çalışma logları `logs/one_click/` altındadır.

## Gerçek donanım

USB kamera, Pico seri bağlantısı ve Windows CUDA/DirectShow için native Windows
kısayolu kullanılmalıdır. Başlatıcı kendi başına Test/Canlı mod seçmez, taret
hareketi üretmez, sistemi arm etmez ve FIRE göndermez. Bunlar görünür uygulama
akışındaki profil ve CommandGateway preflight koşullarına bağlı kalır.

## Docker

`docker/ISTIKLAL_DOCKER_TEK_TIK.cmd` veya `.desktop` yalnız Test/CI ve arayüz
incelemesi içindir. Docker profili fiziksel USB/COM taret yolu olarak
kullanılmaz. Docker da boş host portu seçer ve aynı kısayolla açılıp kapanır.

## Teknik yedekler

Sorun giderme için `windows/` ve `linux/` klasörlerinde ayrı Başlat, Durdur ve
Durum kısayolları bulunur. Normal operatör bunlara ihtiyaç duymaz.
