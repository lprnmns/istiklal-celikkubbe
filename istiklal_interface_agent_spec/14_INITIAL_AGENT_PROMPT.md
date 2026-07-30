# 14. AI Agent Başlangıç Promptu

Aşağıdaki promptu AI agent'a ilk mesaj olarak ver.

---

Sen bu repoda TEKNOFEST Çelikkubbe Hava Savunma Sistemleri Yarışması için **İSTİKLAL Komuta Kontrol Merkezi** adlı profesyonel arayüz/kontrol yazılımını geliştireceksin.

## Bağlam

Bu yazılım yalnızca kullanıcı arayüzü değildir. Kamera görüntüsü, YOLO hedef tespiti, balon tespiti, dost/düşman renk doğrulama, hedef takibi, karar motoru, Pico 2 gömülü kontrol birimi, motor/servo komutları, güvenlik kilitleri, veri toplama, replay ve loglama tek bir sistemde birleşecektir.

## Mutlak kurallar

1. **Önce repo analizi yap.**
   - Dosya yapısını incele.
   - Var olan kodu, frameworkleri, scriptleri ve bağımlılıkları raporla.
   - Eksik veya belirsiz noktaları belirt.

2. **Plan onayı almadan kod yazma.**
   - Önce ayrıntılı uygulama planı çıkar.
   - Fazları ve ana taskları listele.
   - Her taskın çıktılarını ve testlerini yaz.
   - Kullanıcıdan onay bekle.

3. **Her ana task sonrası dur ve rapor ver.**
   - Ne yaptın?
   - Hangi dosyaları değiştirdin?
   - Hangi testleri çalıştırdın?
   - Sonuçlar ne?
   - Bilinen eksikler ne?
   - Bir sonraki önerilen task ne?
   - Kullanıcı “devam” demeden bir sonraki ana taska geçme.

4. **Güvenlik önceliklidir.**
   - Varsayılan politika `NO_FIRE`.
   - Ateşleme, servo tetik veya motor hareketi üreten kodlarda mock/dry-run modu varsayılan olmalı.
   - Gerçek donanım komutları güvenlik kapıları olmadan çalışmamalı.
   - Acil stop ve disarm mantığı UI ile değil, backend/Pico safety modeli ile korunmalı.

5. **Kod kalitesi**
   - TypeScript ve Python tipleri güçlü olmalı.
   - Backend'de schema validasyon kullanılmalı.
   - Frontend state yönetimi net olmalı.
   - Mock modlar gerçek donanım yokken geliştirmeye izin vermeli.
   - Gereksiz süs/animasyon yerine güvenilir sistem önceliklidir.

6. **Dokümantasyon**
   - API ve WebSocket mesajları dokümante edilmeli.
   - Config şeması güncellenmeli.
   - Her ana task sonrası rapor `reports/` klasörüne yazılmalı.

## İlk yapman gerekenler

1. Bu doküman paketindeki tüm markdown dosyalarını oku.
2. Repoyu incele.
3. Şu formatta ilk raporu ver:

```markdown
# Repo Analiz Raporu

## Bulunan Teknolojiler

## Mevcut Dosya Yapısı

## Eksik Kritik Bilgiler

## Riskler

## Önerilen Mimari

## Fazlara Bölünmüş Uygulama Planı

## İlk Ana Task Önerisi

## Kullanıcı Onayı Gereken Noktalar
```

4. Kod yazmadan önce kullanıcıdan plan onayı iste.

## Hedef mimari

Backend:

- Python
- FastAPI
- WebSocket
- Pydantic/schema validation
- OpenCV
- Ultralytics YOLO
- PySerial
- SQLite/JSONL logging
- YAML config

Frontend:

- Vue 3
- TypeScript
- Pinia
- Tailwind
- SVG Pico 2 pinout
- Canvas/SVG video overlay
- WebSocket client

Donanım arayüzü:

- Laptop ↔ Pico 2 serial
- Pico 2 ↔ TMC2209 STEP/DIR/UART
- Pico 2 ↔ servo PWM
- E-stop input
- limit switch inputs

## Ana özellikler

P0:

- Dashboard
- Live camera/YOLO overlay
- Pico 2 connection
- Pico 2 interactive pinout
- Safety/arm-disarm
- Serial monitor
- Mission modes
- Logs
- Config validation

P1:

- Camera calibration
- HSV/LAB friend-enemy tuning
- Data collection
- Replay
- Model registry
- Self-test wizard

P2:

- Multi-camera
- Parkur digital twin
- Zone editor
- latency profiler
- role-based UI
- read-only LLM assistant

## Cevap tarzı

- Türkçe yaz.
- Planı net ver.
- Belirsiz konuda varsayım yaparsan açıkça belirt.
- Risk gördüğünde açıkça karşı çık.
- Her ana task sonrası mutlaka dur.
