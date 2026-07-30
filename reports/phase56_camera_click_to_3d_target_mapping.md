# Phase 56 Camera Click To 3D Target Mapping

Status: implemented through existing camera target selection state.

Mapping:
- Camera detection center `(x_norm, y_norm)` maps into the camera FOV basis.
- `x_norm < 0.5` places the target left of FOV center.
- `x_norm > 0.5` places the target right of FOV center.
- `y_norm < 0.5` places the target above/mid in FOV.
- `y_norm > 0.5` places the target lower/mid in FOV.
- Detection box area estimates depth using the 13 cm radius balloon assumption.
- Estimated depth is clamped to the expected 5-15 m operating range.

Selected target behavior:
- Clicking a target in the camera HUD sets the selected target id.
- The 3D world renders only the selected target as the main orange/red marker.
- The launcher muzzle to selected target ray updates with the selected target position.

If live detections are unavailable, fixture/offline target data is used only as a labeled visualization estimate.

## 2026-07-15 — Laptop kamera manuel DRY_RUN kabul kaydı

Operatör, Cockpit üzerindeki gerçek laptop kamera akışında (`Laptop Dev`, 1280×720,
`Real Frame Dev`) görülen `ID #1 | BALON` algı kutusuna tıkladı.

- Başlangıç durumu: `TARGET none` / `HEDEF YOK`.
- Sonuç: `TARGET #1`, `Selected #1` ve `HEDEF SEÇİLİ` durumları göründü; seçilen
  kutu yeşile döndü.
- 3D dijital ikizde yalnız seçili hedefin ana turuncu/sarı küre temsili güncellendi.
- Güvenlik sınırı doğrulandı: `DRY_RUN / NO TX` ve `FIRE GATE BLOCKED / NO TX`
  durumları test boyunca kaldı; bu testte fiziksel hareket veya atış komutu yoktur.

Bu kayıt kamera → algı kutusu → operatör seçimi → 3D hedef temsili zincirini
doğrular. Telefon ekranındaki örnek nesne ile yapılan bu çalışma, üretim balon
modelinin semantik doğruluğu, menzil/kalibrasyon veya fiziksel taret davranışı
için kabul kanıtı değildir.
