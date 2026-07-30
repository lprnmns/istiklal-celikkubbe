# Paket kapsamı

Bu paket 30 Temmuz 2026 proje ağacından üretilmiştir. Güncel backend, derlenmiş frontend, Pico firmware kaynakları, ana kinematik taret dijital ikizi ve Windows HIL tanı araçlarını içerir.

Boyutu ve hata yüzeyini azaltmak için şunlar bilinçli olarak pakete alınmamıştır:

- YOLO `.pt` / ONNX modelleri (Setup Wizard içinden sonradan seçilir)
- `.venv`, `node_modules`, test cache ve Python bytecode dosyaları
- Eski release ZIP'leri
- Ana kinematik model dışındaki yinelenen büyük STEP/STL/GLB taret varyantları
- Makineye özgü aktif kamera, model ve görev profilleri
- Parola, Tailscale tokeni veya SSH özel anahtarı

Fiziksel hareket ve tetik kabul adımları `10_DONANIM_TEST_NOTLARINI_AC.cmd` ile açılır. Otomatik cihaz taraması yalnız `PING` ve `STAT` gönderir; hareket veya tetik üretmez.
