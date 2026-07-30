# P1 — Gerçek inference cihazı ve benchmark doğruluğu

Tarih: 2026-07-15. Kapsam: PLAT-08 için CPU/CUDA seçiminin ve latency benchmarkının gerçek çalışma durumunu göstermesi.

## Düzeltilen davranış

Önceki YOLO çalışma yolu `VisionRuntimeProfile.device` ne olursa olsun `device="cpu"` geçiriyordu; model paketinin önerdiği `cuda` da sessizce CPU'ya çevriliyordu. Bu, GPU seçilmiş görünürken CPU üzerinde çalışabilen ve sahte benchmark üreten bir akıştı.

Yeni yol:

`VisionRuntimeProfile.device → VisionRuntimeSettingsService.resolve_device → VisionPipeline Ultralytics kwargs.device`

| İstek | Sonuç | Görünür code/reason |
|---|---|---|
| `cpu` | CPU çalışır | `cpu_requested` |
| `cuda`, izin + host CUDA var | CUDA çalışır | `cuda_requested` |
| `cuda`, izin kapalı | Profil uygulanmaz | `cuda_not_allowed` |
| `cuda`, host CUDA yok | Profil uygulanmaz | `cuda_unavailable` |
| `auto` | İzinli CUDA varsa CUDA, yoksa CPU | `auto_cuda_selected` veya açık CPU nedeni |

`half=true` CUDA dışında sessizce half precision olduğunu iddia etmez; `half_disabled_without_cuda` uyarısı görünür.

`/api/vision/runtime/warmup` ve `/api/vision/runtime/benchmark` artık tahmini latency döndürmez. Sadece aktif production YOLO + golden evidence + çözümlenmiş cihaz + reload edilmiş modelle gerçek frame ölçer. Aksi durumda örneğin `REAL_YOLO_ADAPTER_REQUIRED`, `PRODUCTION_MODEL_GOLDEN_EVIDENCE_REQUIRED` veya `MODEL_RELOAD_REQUIRED` ile reddeder.

## Otomatik kanıt

`backend/tests/test_phase80_runtime_device_truth_contract.py`:

1. Explicit CUDA'nın izin kapalıyken `cuda_not_allowed` ile reddedilip CPU'ya sessiz dönüşmediğini;
2. `auto` modunun CUDA yokken gerçek çözümünü `cpu` ve `auto_cpu_cuda_unavailable` olarak raporladığını;
3. Test adapter için warmup/benchmarkın sahte `estimated_latency_ms` üretmek yerine reddedildiğini

doğrular.

Gerçek model/final PC benchmarkı HIL-12 olmadan henüz yapılmış sayılmaz.
