# Faz 9 Raporu - Model Management, Dataset, Session Recording ve Replay

## Yapılanlar

- Model registry, model metadata upload, active model selection ve test inference API katmanı eklendi.
- OpenCV circle detector test adapter eklendi ve UI'da production model olmadığı açıkça gösterildi.
- Session recording, snapshot metadata, JSONL event kayıtları ve annotation review veri modeli eklendi.
- Replay service ve replay API'leri eklendi.
- YOLO dataset export, dataset validation ve dataset health servisleri eklendi.
- Data Lab frontend ekranı eklendi: Models, Capture, Sessions, Replay, Annotation Review, YOLO Export, Dataset Health sekmeleri.
- Dashboard Data Collection kartı ve Vision aktif model özeti eklendi.
- `models` ve `dataset` config blokları eklendi.
- Model/session/dataset/replay/annotation WebSocket eventleri eklendi.
- Büyük runtime çıktıları için `.gitignore` genişletildi.
- Faz 9 dokümantasyonu yazıldı.

## Oluşturulan/değiştirilen dosyalar

- Backend API: `backend/app/api/models.py`, `backend/app/api/dataset.py`, `backend/app/api/replay.py`
- Backend schema: `backend/app/schemas/model_registry.py`, `session.py`, `dataset.py`, `annotation.py`, `replay.py`, `config.py`
- Backend service: `model_registry_service.py`, `model_upload_service.py`, `inference_adapter_service.py`, `opencv_stub_detector.py`, `session_service.py`, `dataset_service.py`, `annotation_service.py`, `replay_service.py`, `storage_paths.py`, `runtime_state.py`
- WebSocket/router: `backend/app/main.py`, `backend/app/api/routes_ws.py`
- Frontend: `frontend/src/views/DataLabView.vue`, `frontend/src/api/dataLab.ts`, `frontend/src/stores/dataLabStore.ts`, `frontend/src/types/dataLab.ts`
- Frontend entegrasyon: `DashboardView.vue`, `VisionView.vue`, `AppShell.vue`, `router/index.ts`, `systemStore.ts`
- Config/dokümantasyon/test: `.gitignore`, `config/config.yaml`, `docs/model_dataset_replay_phase9.md`, `backend/tests/test_phase9_model_dataset_replay.py`

## Test/build sonuçları

- `cd backend && uv run pytest -q`: 117 passed.
- `cd frontend && pnpm typecheck`: başarılı.
- `cd frontend && pnpm build`: başarılı.
- Manual route smoke:
  - `/`: 200
  - `/data-lab`: 200
  - `/vision`: 200
  - `/logs`: 200
  - `/api/models`: 200
  - `/api/health`: 200

Not: Repo kökünden `uv run pytest -q` çalıştırıldığında mevcut test import düzeni nedeniyle `tests.conftest` import hatası oluşuyor. Backend test komutu `backend/` klasöründen çalıştırılmalı.

## Git commit hashleri

- `6110c03` - `feat: add model management dataset replay and yolo export`

## Model management özeti

- Model metadata registry `models/active/registry.json` runtime dosyası üzerinden yönetiliyor.
- Upload endpointi `.pt`, `.onnx`, `.yaml` uzantılarını kabul ediyor.
- Active model slotları: body, balloon, combined, test adapter.
- Gerçek model adapter yoksa controlled warning dönüyor; backend crash etmiyor.

## Vision team/interface team scope ayrımı

- Interface tarafı model yükleme, metadata, active selection, test inference, replay test ve export akışını sağlar.
- Vision ekibi production YOLO/ONNX modeli, class listesi, input size, threshold önerisi ve adapter bilgisini sağlar.
- OpenCV circle detector sadece UI ve replay/test altyapısını doğrulayan test adapter'dır.

## Session recording özeti

- Session metadata, snapshot placeholder, frame metadata ve JSONL event kayıtları eklendi.
- `detections.jsonl`, `color_decisions.jsonl`, `decisions.jsonl`, `operator_actions.jsonl`, `annotations.jsonl` dosya yapısı oluşturuluyor.
- Her kayıt `no_physical_command_generated=true` güvenlik bilgisini koruyor.

## Replay özeti

- Replay session load/play/pause/stop/step/speed API'leri eklendi.
- Replay state WebSocket eventleriyle UI'a akabiliyor.
- Replay source advisory olarak işaretleniyor; fiziksel komut üretmiyor.

## Annotation/YOLO export özeti

- Manual annotation ve model prediction to annotation akışı eklendi.
- YOLO export `data.yaml`, images/train-val, labels/train-val, metadata.json üretir.
- Export modları: body_multiclass, balloon_singleclass, combined_body_balloon, target_singleclass.
- Friend/enemy bilgisi YOLO class yapılmadı; metadata/color pipeline bilgisi olarak bırakıldı.

## Dataset Health ekranı özeti

- Total sessions/images/annotations, class/distance/team/lens/model dağılımları gösteriliyor.
- Eksik veri için öneri metinleri üretiliyor.
- Dashboard'da Data Collection kartı active session/model/export/health durumunu özetliyor.

## Bilinen eksikler

- Gerçek Ultralytics/ONNX adapter implementasyonu vision ekibinin model tesliminden sonra bağlanmalı.
- Gerçek video recording ve gerçek canvas bbox editor bu fazda minimum kapsam dışında bırakıldı.
- Upload endpointi bu fazda metadata/file-name tabanlı güvenli kayıt yapıyor; büyük binary dosya transferi için ileride multipart veya artifact storage akışı eklenebilir.
- Repo kökünden backend test çalıştırma import düzeni mevcut proje yapısı nedeniyle uygun değil; backend testleri `backend/` içinden çalıştırılıyor.

## Riskler

- Runtime `data/` ve `models/` çıktıları Git dışında; saha cihazında backup/cleanup politikası gerekir.
- Dataset export kalitesi annotation doğruluğuna bağlıdır; model prediction sonuçları operatör doğrulaması olmadan training set'e alınmamalı.
- OpenCV stub adapter production model gibi yorumlanırsa yanlış beklenti oluşturur; UI ve docs içinde test adapter uyarısı özellikle korundu.

## Bir sonraki önerilen task

Faz 10: Self-test wizard ve sistem sağlık doğrulama akışı. Faz 10'a geçmeden önce vision ekibinden beklenen model teslim formatı ve gerçek artifact upload yaklaşımı netleştirilebilir.
