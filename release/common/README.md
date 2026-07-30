# Release Common Payload

Bu klasör ZIP release paketinde platformdan bağımsız taşınacak içerikler için ayrılmıştır.

- `config/`: güvenli varsayılan config kopyaları
- `models/`: model import alanı ve README dosyaları
- `firmware/`: telemetry-only Pico firmware yönergeleri
- `docs/`: saha ve ilk kurulum dokümanları
- `reports/`: örnek/şablon rapor içerikleri
- `scripts/`: release kontrol yardımcıları

Büyük runtime çıktıları, model binary dosyaları, loglar ve exportlar Git'e alınmaz.
