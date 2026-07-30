# P1 — Ayrı hareket/ateş güvenlik sektörü profili

Tarih: 2026-07-15. Kapsam: SAFE-08 yazılım sözleşmesinin operatörce görünür, kalıcı ve fail-safe profili.

## Kanonik yol

`Motion ekranı → /api/safety-zones/profile → SafetyZoneProfileService → config.runtime safety_zones.active.json → CommandGateway / DecisionEngine`

Profil iki ayrı liste taşır:

| Kapsam | Gateway sonucu | Reason code |
|---|---|---|
| Hareket sektörü | `SPD` reddedilir | `MOTION_FORBIDDEN_ZONE` |
| Ateş sektörü | `LZR,1` reddedilir | `FIRE_FORBIDDEN_ZONE` |

Sektörler soft pan/tilt limitlerinin dışında tanımlanamaz (`SAFETY_ZONE_OUTSIDE_SOFT_LIMITS:<name>`). Aynı kapsam içinde yinelenen ad reddedilir. A3 COMPETITION çalışırken profil sabittir (`A3_PROFILE_LOCKED`).

Her profil değişikliği `LZR,0 → STP → DRV,0` güvenli durdurma zincirini gönderir, arm/preflight durumunu geçersiz kılar ve `SAFETY_ZONE_PROFILE_CHANGED` reason code’unu görünür bırakır. Devam etmek için mevcut normal `preflight → arm` akışı kullanılır; ek operatör/şifre/onay katmanı yoktur.

## Otomatik kanıt

`backend/tests/test_phase79_safety_zone_profile_contract.py` mock Pico ile:

1. Ayrı profilin kalıcı dosyaya yazıldığını ve hash ile geri döndüğünü;
2. Canlı yetkinin profil değişiminde güvenli durup preflight gerektirdiğini;
3. Aynı açıdaki hareket ve fire isteklerinin kendi ayrı reason code'larıyla reddedildiğini;
4. Soft limit dışı sektörün ve A3 çalışma sırasındaki mutasyonun reddedildiğini

doğrular.

Bu sözleşme fiziksel E-Stop veya limit switch yerine geçmez. Gerçek konum/limit telemetrisi ve sektör sınır HIL-11 ile kanıtlanana kadar sektör profili ilave yazılım katmanıdır.
