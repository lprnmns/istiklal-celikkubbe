# P1 — Aşama 3 gerçek perception kanıt sözleşmesi

Tarih: 2026-07-15. Kapsam: A3-02/03/04/06 altyapısı; gerçek model ve saha kalibrasyonu henüz bulunmadığından canlı Aşama 3 fire **NO-GO** kalır.

## Uygulanan zincir

`YOLO box.cls → role-aware parser → BodyDetection(class id/name/provenance) → persistent body track → body-only BGR/HSV ROI → temporal IFF → model-hash bağlı range profile → DecisionEngine`

- Body ve balloon model slotları ayrı okunur; aynı ağırlık iki slotta seçilirse combined detector olarak yalnız bir kez çalışır.
- Registry sınıf adı ile gerçek output sınıf adı uyuşmazsa kutu reddedilir (`model_class_mapping_mismatch`). Her kutunun balloon olarak ezilmesi kaldırılmıştır.
- Production model paketi `golden_cases.json` içindeki gerçek frame'lerde ağırlığı gerçekten çalıştırıp her zorunlu sınıfın tensor `class_id → class_name` eşlemesini doğrulamazsa `competition_ready` olamaz. Metadata veya sentetik test kutusu yeterli değildir.
- Aşama 2 generic body modeli `generic_target` üretir; bunu F16 gibi göstermediği için Aşama 3 model kapısını geçemez.
- IFF yalnız gövde ROI'sinden üretilir. Balon kutusu ROI'den çıkarılır; `mock_sample` sonucu hiçbir zaman live-fire kanıtı değildir.
- Enemy için ardışık gerçek ROI consensus gerekir; FRIEND ilk frame'de dahi fail-closed olur. UNKNOWN/ambiguous NO_FIRE'dır.
- Range profili her dört sınıf için 5/10/15 m alan gözlemi ister; model dosyası hash'i değiştiğinde profil otomatik geçersizdir. Tahmin metre + belirsizlik aralığıdır; A3 aralığı ancak tamamı sınıf penceresinin içindeyse geçer.

## Reason code'lar

| Durum | Kod |
|---|---|
| Gerçek/uyumlu body model yok | `a3_body_model_missing_or_unverified` |
| Gerçek ROI veya temporal IFF yok | `a3_iff_real_roi_unavailable` |
| Saha range profili/model hash uyumsuz | `a3_range_calibration_unavailable` / `A3_RANGE_MODEL_FINGERPRINT_MISMATCH` |
| Output sınıf eşlemesi yanlış | `model_class_mapping_mismatch:<model>:<id>` |
| IFF zaman penceresi dolmadı | `iff_temporal_consensus_pending` |

## Otomatik kanıt

`backend/tests/test_phase73_stage3_perception_contract.py` şunları doğrular:

1. Sahte YOLO tensoründe `box.cls` body/balloon ayrımını korur; yanlış mapping kutuyu reddeder.
2. BGR gövde ROI'sindeki dost renkli balon pikselini maskeleyerek üç frame real-ROI enemy consensus üretir.
3. Mock sample'ın real IFF yerine geçemediğini doğrular.
4. 5/10/15 m range profili metre/belirsizlik üretir ve model hash değişiminde invalid olur.
5. Registry'ye elle eklenmiş bir fixture modelin gerçek tensor/golden model paketi yerine geçemediğini; IFF ve range kanıtı geçse bile body-model kapısının kırmızı kaldığını doğrular.

## Donanım geldiğinde

HIL-09'a her sınıf için 5/10/15 m capture id, bbox/mesafe örneği, model hash, profile hash ve holdout hata dağılımı eklenir. Bir false-enemy, class mapping veya range sınır ihlalinde A3 physical fire derhal NO-GO'dur.
