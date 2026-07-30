# 10 — Model, IFF, Association ve Menzil Planı

## 1. Mevcut gerçek

Gerçek YOLO akışı ağırlıklı olarak BalloonDetection üretiyor ve body_detections boş kalıyor. Model paketi/registry iskeleti var; fakat gerçek sınıf çıktısı, class ID mapping, GPU performansı ve final koşulu doğrulanmış değil. Bu nedenle Aşama 3 perception kabuğu ile gerçek kabiliyet birbirinden ayrılmalıdır.

15 Temmuz audit’inde aktif runtime profili opencv_live_circle_surrogate, body/balloon model ID’leri boş bulundu. Legacy registry’de dost/düşman sınıfları balloon etiketi gibi kayıtlı ve pipeline box.cls semantiğini korumuyor. Bu üç durum düzelmeden Y6 veya Aşama 3 gerçek model kabulü yoktur.

## 2. Hedef perception çıktısı

Her frame/track için:

- BodyDetection: bbox, class_id, class_name, confidence.
- BalloonDetection: bbox, confidence, color özellikleri yalnız görselleştirme/association için.
- Track: kalıcı ID, hız, yaş, freshness.
- IFF: FRIEND, ENEMY, UNKNOWN, confidence, profile hash.
- Association: body_track_id ↔ balloon_track_id, state, confidence.
- Range: metre, belirsizlik, calibration hash.
- Performance: inference, tracking ve end-to-end latency.

## 3. Model teslim sözleşmesi

Model paketi:

- Ağırlık dosyası.
- Format ve opset.
- Input shape/preprocess.
- Gerçek sınıf sırası.
- Thresholds.
- Eğitim veri kaynağı ve lisans.
- Train/val/test bölümü.
- Commit/model hash.
- Hedef cihaz benchmark’ı.
- Örnek gerçek inference çıktıları.

Production-ready kontrolü metadata okumakla bitmez. Paket, bilinen golden görüntülerde inference çalıştırır ve gerçek output tensor/class ID eşleşmesini doğrular.

active_models seçimi, runtime vision profile, API health ve UI aynı model ID/hash’i göstermelidir. Surrogate açıkça SURROGATE/DEMO olarak işaretlenir.

## 4. Veri stratejisi

Kaynaklar:

- Güncel resmî 3MF ve render’lar.
- Takımın gerçek basılı maketleri.
- 5/10/15 m kontrollü çekimler.
- Farklı ışık, açı, arka plan ve motion blur.
- Dost/düşman renk varyasyonları.
- Balon rengi varyasyonları.
- Negatif arka plan ve insan/ekipman örnekleri.

Veri bölümü aynı çekim videosundan rastgele frame ayırarak yapılmaz. Capture session, mesafe ve sahne bazında ayrılarak leakage engellenir.

Resmî hedef dosyası haftalık hash kontrolüyle izlenir; revizyon gelirse impact analizi yapılır.

## 5. Eğitim ve değerlendirme sırası

1. Golden veri seti ve sınıf sözleşmesi.
2. Baseline gerçek model inference.
3. Hata matrisi: sınıf, mesafe, ışık, açı.
4. Model/threshold iyileştirmesi.
5. GPU export/benchmark.
6. Tracker entegrasyonu.
7. IFF.
8. Association.
9. Range.
10. Aşama 3 uçtan uca replay ve fiziksel acceptance.

Model iyileştirmesi tek başına Aşama 3 tamamlanmış sayılmaz.

## 6. Y6 video kabul eşiği

Her sınıf × 5/10/15 m için kayıtlı test:

- En az 10 bağımsız kısa klip veya saha geçişi.
- UI etiketi stabilite oranı raporlu.
- 15 m recall ve etiket sıçramaları ayrıca raporlu.
- Dört sınıflı confusion matrix.
- Zorunlu Y5 üzerinde performans regresyonu yok.

Kesin accuracy/latency eşiği ilk golden benchmark’tan sonra takımca kilitlenir. Video kararı için görsel olarak stabil ve tekrar edilebilir olmayan model çıkarılır.

## 7. Final model kabul eşiği

- Gerçek saha test seti eğitimden ayrı.
- Sınıf başına ve mesafe başına recall/precision.
- Unknown/OOD davranışı.
- Track boyunca temporal class voting.
- Hedef cihazda p50/p95 inference.
- Frame→decision p50/p95.
- 30 dakikalık soak.
- Model crash/timeout durumunda NO_FIRE.

Aşama 3 fiziksel ateşi için yalnız genel mAP değil, yanlış sınıfın menzil/IFF kararına etkisi değerlendirilir.

## 8. IFF planı

IFF gövde renginden üretilir:

- Kamera white-balance/exposure kilidi veya kontrollü profili.
- Gövde ROI’si; arka plan/balon pikselinden ayrım.
- HSV/Lab özellikleri ve gerekirse segmentasyon.
- Track boyunca temporal aggregation.
- Saha kalibrasyon örnekleri.
- Yapılandırılabilir friend/enemy renk kümeleri.

Request içindeki mock_team veya kullanıcı tarafından verilmiş sonuç gerçek IFF girdisi değildir; yalnız test fixture’ında kullanılabilir.

Testler:

- Renk eşlemesini ters çevir.
- Aynı sınıfta dost/düşman.
- Değişen aydınlatma.
- Renk sınırında UNKNOWN.
- Balon rengi değişse de IFF sabit.

Bir adet false-enemy fiziksel olay, IFF canlı ateş kapısını kapatır.

## 9. Association planı

İlk sürüm:

- Resmî modelde balon bağlantı bölgesi.
- Body bbox’a göre normalize edilmiş aday alan.
- Yakınlık ve yön.
- Ortak optical flow/hız.
- Track sürekliliği.

Gelişmiş sürüm:

- Bipartite matching maliyet matrisi.
- Sınıfa özel geometri.
- Kalibre edilmiş perspektif.
- Histerezis ve minimum stabil frame.

Kabul senaryoları:

- 1 body/1 balloon.
- 2/2 çapraz.
- 3/3 Aşama 2.
- Dost+düşman yakın geçiş.
- Orphan balloon.
- Body/balloon kaybı.
- Ambiguous link.

Ambiguous link ateş üretmez.

## 10. Menzil planı

Tercih sırası:

1. Mevcut ve yarışmaya uygun gerçek range sensörü varsa kalibre edilmiş sensör füzyonu.
2. Bilinen hedef boyutu + kamera intrinsics + target-specific apparent size.
3. Parkur geometrisi/track konumu ile destek.

Tek kare ham bbox yüksekliği tek başına güvenilir metrik menzil kabul edilmez.

Identity homography ve her durumda sıfır kalibrasyon hatası placeholder kabul edilir; final kararına bağlanmaz.

Kalibrasyon:

- Kamera intrinsics/distortion.
- Her sınıf için gerçek boyut referansı.
- 5/10/15 m ve ara noktalar.
- Farklı açı ve yükseklik.
- Tahmin hatası ve confidence interval.

Karar:

- Nokta tahmini değil belirsizlik aralığı.
- Sınıf menzil penceresiyle güvenli kesişim.
- Sınırda hysteresis.
- Calibration/model hash değişince range profili geçersiz.

## 11. Performans bütçesi

İlk baseline’dan sonra sayısal bütçe kilitlenir:

- Kamera FPS ve stale frame.
- Decode/preprocess.
- Inference p50/p95.
- Tracking.
- IFF/association/range.
- Decision.
- Serial ACK.
- Toplam frame→guidance.

Kontrol loop periyodunu aşan p95 latency ile canlı takip kabul edilmez. UI çizimi inference/control thread’ini bloklamaz.

## 12. Muhtemel kod/veri alanları

- backend/app/services/vision_pipeline.py
- backend/app/services/inference_adapter_service.py
- backend/app/services/model_package_service.py
- backend/app/services/model_registry_service.py
- backend/app/services/color_classifier_service.py
- backend/app/services/kalman_tracker.py
- backend/app/schemas/vision.py
- backend/app/schemas/model_package.py
- config/config.yaml
- models veya onaylı harici model deposu
- datasets veya onaylı harici veri deposu
- backend/tests/fixtures/model_packages
- yeni golden inference/replay benchmark’ları

## 13. Geri dönüş

- Yeni model class mapping testini geçmezse yüklenmez.
- GPU export gerçek output’u değiştirirse önceki format kullanılır.
- IFF/association/range kapılarından biri kırmızıysa Aşama 3 gerçek fire kapalıdır.
- Model Y1–Y5’i bozarsa video dalından tamamen çıkarılır.
- Model yokluğu balon baseline’ını bozmamalıdır; adapter açık fail state üretir.
