# Task Raporu: Faz 6 - Decision Engine ve Safety Gates

## Yapilanlar

- Housekeeping olarak Faz 5 raporu commit'e alindi.
- Backend decision engine katmani eklendi.
- Safety gate service eklendi.
- Decision state, safety gate, fire evaluation ve arm/disarm result schemalari eklendi.
- Decision API eklendi:
  - `GET /api/decision/state`
- Safety API genisletildi:
  - `POST /api/safety/arm`
  - `POST /api/safety/disarm`
  - `GET /api/safety/state`
  - `GET /api/safety/gates`
  - `POST /api/safety/fire-request`
- Fire request decision engine'e baglandi ama gercek serial/motor/servo komutu uretilmedi.
- Range rules config'e eklendi.
- Team, balloon, stability ve forbidden zone placeholder logic eklendi.
- WebSocket eventleri eklendi:
  - `decision.updated`
  - `safety.gates`
  - `safety.armed`
  - `safety.disarmed`
  - `safety.fire_request_rejected`
  - `safety.fire_request_accepted_dry_run`
  - `safety.fault`
- Frontend decision store ve Safety ekraninin yeni surumu eklendi.
- Dashboard Safety karti decision store'dan beslenecek sekilde guncellendi.
- Dokumantasyon eklendi.

## Olusturulan / Degistirilen Dosyalar

| Dosya | Degisiklik |
|---|---|
| `backend/app/schemas/decision.py` | Decision state, gate ve evaluation modelleri eklendi. |
| `backend/app/services/decision_engine.py` | Decision/range/team/balloon/stability gate degerlendirmesi eklendi. |
| `backend/app/services/safety_gate_service.py` | Gate helper katmani eklendi. |
| `backend/app/api/decision.py` | Decision state endpointi eklendi. |
| `backend/app/api/routes_safety.py` | Arm/disarm/fire-request/gates/state akisi genisletildi. |
| `backend/app/api/routes_ws.py` | Decision ve safety WebSocket eventleri eklendi. |
| `backend/app/schemas/config.py` | Decision/range/safety config validation eklendi. |
| `config/config.yaml` | Decision ve safety default ayarlari eklendi. |
| `backend/tests/test_decision.py` | Decision engine ve safety gate testleri eklendi. |
| `frontend/src/types/decision.ts` | Decision frontend tipleri eklendi. |
| `frontend/src/api/decision.ts` | Decision/safety REST client eklendi. |
| `frontend/src/stores/decisionStore.ts` | Decision state ve safety event store eklendi. |
| `frontend/src/views/SafetyView.vue` | Safety ekraninin yeni decision/gate UI'i eklendi. |
| `frontend/src/views/DashboardView.vue` | Dashboard Safety karti guncellendi. |
| `docs/decision_safety_phase6.md` | Faz 6 decision/safety dokumantasyonu eklendi. |
| `reports/008_phase6_decision_safety.md` | Bu rapor eklendi. |

## Calistirilan Komutlar

```bash
git status --short
git add reports/007_phase5_vision_pipeline.md
git commit -m "docs: add phase 5 vision pipeline report"
PATH="$HOME/.local/bin:$PATH" uv run pytest
pnpm typecheck
pnpm build
curl -sS http://127.0.0.1:8000/api/decision/state
curl -sS -X POST http://127.0.0.1:8000/api/safety/fire-request -H 'Content-Type: application/json' -d '{"operator_confirmed":true}'
curl -sS -I http://127.0.0.1:5173/safety
git add backend config docs/decision_safety_phase6.md frontend/src
git commit -m "feat: add decision engine and safety gates"
```

## Test / Build Sonuclari

```text
Backend pytest: 64 passed in 4.08s
Frontend pnpm typecheck: passed
Frontend pnpm build: passed
Manual /api/decision/state: passed
Manual /api/safety/fire-request: rejected without physical command
Manual /safety route: HTTP 200
```

Build ciktisi:

```text
dist/index.html                  0.45 kB
dist/assets/index-*.css         21.56 kB
dist/assets/index-*.js         150.37 kB
```

## Git Commit Hashleri

```text
d1b06d0 docs: add phase 5 vision pipeline report
4b24e55 feat: add decision engine and safety gates
```

## Decision Engine Ozeti

Decision engine runtime'dan su kaynaklari okur:

- system state
- latest vision event
- Pico mock status
- serial status
- decision config

Urettigi ana model:

- decision state
- active target
- body/balloon selection
- target class/team/range
- stable frames
- gate list
- blocking reasons
- decision reason
- aim point telemetry

## Safety Gates Ozeti

Eklenen gate'ler:

- `system_disarmed_gate`
- `system_armed_gate`
- `dry_run_gate`
- `hardware_enabled_gate`
- `estop_gate`
- `pico_connected_gate`
- `pico_heartbeat_gate`
- `serial_ok_gate`
- `vision_running_gate`
- `body_detected_gate`
- `balloon_detected_gate`
- `team_classified_gate`
- `enemy_target_gate`
- `friend_rejection_gate`
- `range_valid_gate`
- `stable_track_gate`
- `forbidden_zone_gate`
- `operator_confirm_gate`

Her gate `pass/fail/warning/not_applicable` status ve `info/warning/critical` severity tasir.

## Range / Team / Balloon / Stability Karar Kurallari

- `friend` hedef kesin `NO_FIRE`.
- `unknown` team `WAIT`; `FIRE_READY` olamaz.
- `enemy` degilse `FIRE_READY` olamaz.
- Balloon yoksa `FIRE_READY` olamaz.
- `stable_frames < required` ise gate fail olur.
- Forbidden zone bu fazda disabled ve `not_applicable`.
- Range rules:
  - f16: 10-15 m
  - helicopter: 5-15 m
  - ballistic_missile: 5-15 m
  - mini_micro_uav: 0-15 m
  - unknown/rule olmayan class: fire forbidden

## Frontend Safety Ekrani Ozeti

- Current decision state card.
- Fire policy card.
- Arm/Disarm controls.
- Fire Request dry-run evaluation button.
- Safety gates matrix.
- Blocking reasons list.
- Active target summary.
- Range rule display.
- Latest decision events.
- UI uyarisi: `No physical fire command is generated in Phase 6.`

## Bilinen Eksikler

- Decision engine henuz tam tracking servisine bagli degil; stable frame bilgisi vision event placeholder alanindan okunuyor.
- Forbidden zone gercek hesaplama yapmiyor; placeholder gate var.
- Team classification gercek HSV/LAB pipeline'dan gelmiyor; mock/vision event alanindan okunuyor.
- Fire request hicbir kosulda gercek komut uretmiyor; bu bilincli guvenlik karari.
- Frontend unit test eklenmedi; typecheck/build ve manuel smoke yapildi.
- `reports/008_phase6_decision_safety.md` commit sonrasinda olusturuldu; bu rapor henuz commitlenmedi.

## Riskler

- `Arm Dry-run` UI'da operator tarafindan yanlis anlasilmamali; hardware yetkisi vermez.
- Decision engine FIRE_READY uretse bile `hardware_enabled=false` fiziksel komutu engeller.
- Gercek team/range/tracking entegrasyonlari gelmeden decision sonucu saha atis yetkisi icin kullanilmamalidir.
- Faz 7 motor/taret entegrasyonunda bu gate modelinin disindan komut yolu acilmamalidir.

## Bir Sonraki Onerilen Task

Faz 7 - Motor/Taret Kontrol Paneli:

- Jog/home/stop endpointleri.
- Dry-run default motor command path.
- Motor settings schema.
- UI motor/taret paneli.
- E-stop, limit switch ve safety gate entegrasyonu.

Kullanici `devam` demeden Faz 7'ye gecilmeyecek.
