# Gerçek Test ve Rekabet Hazırlığı Notları

Proje plan dokümanlarında mevcut fiziksel prototipin balon hedeflerini tespit ve takip ettiği, önceki saha çalışmalarında balon hedefiyle entegrasyon denemeleri yapıldığı belirtilmiştir. Ancak bu klasördeki mevcut Phase 43 evidence paketi, 5-10 m gerçek testlerin tarih, video, ölçüm ve hit/miss sayımı gibi resmi kanıt dosyalarını içermez.

Bu nedenle KTR'ye kopyalanacak final metinde gerçek 5-10 m hareketli balon testleri yalnızca ilgili kanıt dosyaları eklendikten sonra kesin sonuç olarak yazılmalıdır. Mevcut dijital ikiz paketi; arayüz, açıklanabilirlik, fixture/replay doğrulaması, asset entegrasyonu ve güvenlik sınırını kanıtlar.

Final KTR öncesi eklenmesi önerilen gerçek test kanıtları:

- Test tarihi, saat ve konum
- Hedef mesafesi: 5 m, 10 m veya ölçülen gerçek mesafe
- Hedef çapı ve hedef tipi
- Hedef hareket durumu: sabit / hareketli / parkur benzeri
- Aydınlatma koşulu
- Kamera modeli, çözünürlük, FPS ve lens bilgisi
- Aktif model adı ve model versiyonu
- Confidence threshold, NMS threshold ve takip ayarları
- Hedef tespit ekran görüntüsü veya video kaydı
- Dijital ikiz veya kokpit ekran görüntüsü
- Atış/angajman varsa güvenli saha prosedürü ve operatör onayı
- Hit/miss sayısı ve tekrar sayısı
- Operatör gözlem notları
- Test sonunda üretilen log ve evidence dosyaları

Bu bilgiler eklendiğinde, KTR'de “balon hedefi entegrasyon testi” ile “dijital ikiz açıklanabilirlik kanıtı” aynı test hikayesinde birleştirilebilir.
