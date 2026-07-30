# İSTİKLAL Komuta Kontrol Merkezi — AI Agent Kodlatma Paketi

Bu paket, TEKNOFEST Çelikkubbe Hava Savunma Sistemleri Yarışması için geliştirilecek **arayüz/kontrol yazılımını** bir AI agent'a planlı, güvenli ve iteratif biçimde kodlatmak amacıyla hazırlanmıştır.

Bu arayüz sadece “ekranda butonlar olan bir kullanıcı paneli” değildir. Sistem; kamera görüntüsü, YOLO hedef tespiti, balon/nişan noktası algısı, dost-düşman renk doğrulama, hedef takibi, karar motoru, Pico 2 gömülü kontrol birimi, motor/servo kontrolü, acil stop, güvenlik kilitleri, veri toplama, replay ve loglamayı tek merkezde birleştiren **komuta kontrol platformudur**.

## Agent'a nasıl verilecek?

1. Bu klasörü hedef repo içine koy: `docs/interface-agent-spec/`
2. `14_INITIAL_AGENT_PROMPT.md` dosyasını AI agent'a ilk prompt olarak ver.
3. Agent önce repo analizi ve uygulama planı çıkarmalı.
4. Agent plan onayı almadan kod yazmamalı.
5. Her ana task sonrası durup rapor vermeli.
6. Raporu sana attıktan sonra sen kontrol edeceksin; sonra `devam` diyeceksin.

## Dosya listesi

| Dosya | İçerik |
|---|---|
| `01_PRODUCT_VISION.md` | Ürün vizyonu ve profesyonel seviye hedefi |
| `02_FEATURE_CATALOG.md` | Eklenebilecek özelliklerin geniş kataloğu |
| `03_SYSTEM_ARCHITECTURE.md` | Backend, frontend, vision, Pico 2, safety mimarisi |
| `04_UI_UX_SPEC.md` | Sayfa, ekran, component ve kullanıcı akışı tasarımı |
| `05_INTERFACE_REQUIREMENTS_FOR_KTR.md` | KTR 4.3 Arayüzler bölümüne yazılabilecek teknik içerik |
| `06_BACKEND_API_AND_WEBSOCKET_SPEC.md` | REST ve WebSocket mesaj sözleşmeleri |
| `07_PICO2_PINOUT_AND_HARDWARE_UI.md` | İnteraktif Pico 2 pinout ekranı ve doğrulama kuralları |
| `08_SERIAL_PROTOCOL.md` | Laptop ↔ Pico 2 haberleşme protokolü |
| `09_VISION_AND_DECISION_UI.md` | YOLO, balon, HSV/LAB, tracking ve karar ekranları |
| `10_SAFETY_ARMING_STATE_MACHINE.md` | No-fire default, arm/disarm, acil stop state machine |
| `11_DATASET_REPLAY_LOGGING.md` | Veri toplama, replay, loglama ve model geliştirme döngüsü |
| `12_CONFIGURATION_AND_MODEL_REGISTRY.md` | Config, model kartı ve ayar versiyonlama |
| `13_TESTING_ACCEPTANCE_CRITERIA.md` | Test planı ve kabul kriterleri |
| `14_INITIAL_AGENT_PROMPT.md` | Agent'a verilecek başlangıç promptu |
| `15_AGENT_REPORT_TEMPLATE.md` | Agent'ın her ana task sonrası dolduracağı rapor şablonu |
| `16_RECOMMENDED_REPO_STRUCTURE.md` | Önerilen repo yapısı |
| `17_BACKLOG_AND_PHASES.md` | Fazlara bölünmüş backlog |
| `18_SOURCE_REFERENCES.md` | Teknik kaynaklar |

## Ana prensipler

- Varsayılan güvenlik politikası: `NO_FIRE`
- Ateşleme, motor ve servo komutları dry-run/mock mod olmadan geliştirme sırasında aktif olmamalı.
- Pico 2 pinleri UI'da interaktif ve doğrulanabilir olmalı.
- UI her kritik kararın nedenini göstermeli.
- WebSocket gerçek zamanlı telemetry için kullanılmalı.
- REST API ayar, dosya ve komut işlemleri için kullanılmalı.
- Config değişiklikleri validasyon ve logdan geçmeli.
- Her ana task sonrası agent durmalı ve rapor vermeli.
