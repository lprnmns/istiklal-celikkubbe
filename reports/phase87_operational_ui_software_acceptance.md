# Phase 87 — Yazılımsal kabul kaydı

Tarih: 2026-07-16

## Uygulanan işlevler

- Başlangıç ekranı yalnız `DRY RUN` ve `LIVE HARDWARE` seçimi sunar.
- Dört readiness satırı authoritative frontend store ve CommandGateway
  preflight sonucundan türetilir: Backend, Kamera, Pico + E-Stop, Hareket +
  Tetik.
- `DRY RUN` seçimi gerçek `POST /api/safety/command-profile` çağrısı yapar.
- LIVE niyeti dört adımlı Setup'a yönlenir; gerçek Pico bağlantısı yalnız
  `/api/safety/pico-connect`, arm/preflight yalnız `/api/safety/preflight`
  kullanır.
- Eski `/api/setup/pico/*`, `/api/setup/motor/test` ve
  `/api/setup/actuator/safe-test` endpointleri yeni UI tarafından kullanılmaz;
  cevapları artık `deprecated` ve replacement yolunu taşır.
- Operator üst barda mod/görev/sistem engeli/E-Stop olmak üzere dört durum
  gösterir. FIRE düğmesi yalnız Gateway readiness'e göre etkinleşir ve blocker
  code'u title/özet alanında görünür.
- Preflight paneli varsayılan kapalı drawer'dır. Engineer kontrolleri ayrı
  sağ drawer'da tek sekme halinde açılır.
- Debug ve legacy route'lar normal sidebar'dan kaldırıldı; doğrudan URL uyumluluğu
  korunuyor.

## Otomatik doğrulama

| Kontrol | Sonuç |
|---|---|
| `pnpm typecheck` | PASS |
| `pnpm build` | PASS |
| Vue production derlemesi | PASS |
| Gateway + mock Pico contract (`11` test) | PASS |

## Donanım bekleyen kabul

Gerçek Pico, E-Stop, hareket ve tetik doğrulamaları
`reports/HIL_PICO_TARET_KABUL_TESTI.md` içindeki **HIL-17** altında kayıtlıdır.
Bu maddeler yazılımın yerini tutmaz; gerçek cihaz geldiğinde aynı UI akışıyla
çalıştırılacaktır.
