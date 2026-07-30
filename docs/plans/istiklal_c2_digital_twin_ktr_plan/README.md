# İSTİKLAL C2 Digital Twin + KTR Tam Puan Plan Paketi

Oluşturulma: 2026-05-23 09:32

Bu klasör, mevcut çalışan balon takip sistemini bozmadan yeni **telemetry-driven digital twin / operasyonel dijital ikiz** arayüzüne geçmek için hazırlanmış MD dosyalarını içerir.

Ana ilke:

- Mevcut çalışan balon tespit + takip + indirme akışı korunacak.
- Digital twin ilk aşamada **read-only telemetry mirror** olacak.
- 3D panel, tracker veya Pico komut hattının sahibi olmayacak.
- Cihaz yanımızda değilken yapılacak işler fixture/replay/mock telemetry ile sınırlı kalacak.
- Gerçek cihaz bağlandığında ayrıca acceptance test yapılacak.
- KTR'de mekanik + elektronik + yazılım + arayüz + test + güvenlik + özgünlük bölümlerine ayrı ayrı kanıt üretilecek.

Dosyalar:

1. `00_MASTER_AGENT_PROMPT_DIGITAL_TWIN.md`  
   Kodlama yapan AI agent'a verilecek ana kapsamlı prompt.

2. `01_KTR_FULL_SCORE_STRATEGY.md`  
   KTR puan kalemlerine göre hangi özelliğin hangi bölüme yazılacağı.

3. `02_DIGITAL_TWIN_ARCHITECTURE.md`  
   Telemetry contract, frontend/backend mimarisi, 3D viewer ve replay tasarımı.

4. `03_PHASE_31_35_IMPLEMENTATION_PLAN.md`  
   Faz 31-35 ayrıntılı görev planı, DoD ve test kriterleri.

5. `04_ASSET_AND_MODEL_PIPELINE.md`  
   STEP/3MF/.model -> GLB pipeline, 4 yarışma sınıfı model varlık akışı.

6. `05_STABLE_TRACKER_REGRESSION_AND_SAFETY.md`  
   Mevcut çalışan takip sisteminin bozulmaması için regression ve safety guard planı.

7. `06_KTR_SECTION_DRAFTS.md`  
   KTR'ye doğrudan uyarlanabilecek kısa metin taslakları.

8. `model_inventory.json`  
   Yüklenen `.model` dosyalarının format/sha256 envanteri.

Kullanım önerisi:

- Önce `00_MASTER_AGENT_PROMPT_DIGITAL_TWIN.md` dosyasını agent'a ver.
- Sonra agent'tan **yalnızca Faz 31 + 32** için uygulama planı ve diff istemek daha güvenli.
- Cihaz yokken Faz 33-35'in yalnızca replay/fixture tarafı yapılmalı.
- Gerçek Pico/kamera/motor acceptance cihaz yanındayken ayrı yürütülmeli.
