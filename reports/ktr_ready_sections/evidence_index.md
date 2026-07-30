# KTR Evidence Index

Bu indeks Phase 31-42 arasında üretilen dijital ikiz, güvenlik, kamera truth, asset ve kokpit kanıtlarını KTR bölümleriyle eşleştirir.

| Kanıt | Amaç | Desteklediği KTR bölümü | Truth modu | Güvenlik notu |
| --- | --- | --- | --- | --- |
| `reports/061_phase31_32_digital_twin_foundation.md` | Dijital ikiz temel mimarisi ve read-only başlangıç | Yazılım Tasarımı, Sistem Blok Diyagramı | fixture/replay | Fiziksel komut yok |
| `reports/062_phase33_digital_twin_live_state_mapping.md` | Backend state -> dijital ikiz mapping | Yazılım Tasarımı, Yöntem | read-only state | Telemetry yoksa fixture/estimate ayrımı |
| `reports/063_phase34_person_safety_gate.md` | Person safety gate özeti | Güvenlik, Yazılım Tasarımı | software safety | Fire gate blokajı ek güvenlik katmanıdır |
| `reports/064_phase35_digital_twin_spatial_projection.md` | 2B bbox -> 3B sahne projeksiyonu | Yöntem, Yazılım Tasarımı | projection estimate | Metrik menzil iddiası yok |
| `reports/074_phase40_real_asset_digital_twin_integration.md` | Gerçek STL asset entegrasyonu | Mekanik Tasarım, Yazılım Tasarımı | STL-derived | CAD/STL görselleştirme amaçlı |
| `reports/077_phase41_digital_twin_asset_transform_calibration.md` | Asset transform ve 30 mm ofset | Mekanik Tasarım, Yöntem | calibrated visualization | Ofset fiziksel komut için kullanılmaz |
| `reports/080_phase42_ktr_digital_twin_presentation.md` | KTR sunum seviyesi dijital ikiz anlatımı | Proje Özeti, Yazılım, Yöntem | fixture | `no_physical_command_generated=true` |
| `reports/081_phase42_operator_cockpit_explainability.md` | Operatör panel açıklanabilirliği | Yazılım Tasarımı, Organizasyon | fixture/read-only | Operatör güvenlik durumunu görür |
| `reports/082_phase42_scene_truth_and_safety_boundary.md` | Fixture/live ayrımı ve güvenlik sınırı | Güvenlik, Risk | fixture | Fiziksel komut yolu yok |
| `reports/digital_twin_ktr_story_contract.json` | Dijital ikiz sahne hikayesi kontratı | Yazılım Tasarımı, Kanıt | fixture/read-only | Safety invariant alanları var |
| `reports/cockpit_projection_explainability_contract.json` | Projeksiyon açıklanabilirlik kontratı | Yöntem, Yazılım | projection estimate | Fire solution değildir |
| `reports/screenshots/phase42_ktr_digital_twin_presentation/` | KTR demo ekran görüntüleri | Proje Özeti, Arayüz, Kanıt | fixture | Görseller fiziksel komut üretmez |

Ek Phase 43 paketi:

- `reports/ktr_ready_sections/00_executive_summary_digital_twin.md`
- `reports/ktr_ready_sections/01_dijital_ikiz_kokpit_aciklamasi.md`
- `reports/ktr_ready_sections/02_algilama_3d_projeksiyon_mimarisi.md`
- `reports/ktr_ready_sections/03_operator_kokpiti_ve_aciklanabilirlik.md`
- `reports/ktr_ready_sections/04_guvenlik_katmanlari_ve_komut_siniri.md`
- `reports/ktr_ready_sections/05_ktr_demo_senaryosu.md`
- `reports/ktr_ready_sections/06_gercek_test_ve_rekabet_hazirligi_notlari.md`

Tüm Phase 43 anlatımı için güvenlik notu: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`.
