# P1 — Aşama 1 manuel görev sözleşmesi

Tarih: 2026-07-15. Kapsam: A1-02/A1-03/A1-04 için kanonik görev durum makinesi, manuel Gateway yolu ve güvenli giriş davranışı.

## Eski ve kanonik yol

| Eski yol | Sorun | Kanonik yol |
|---|---|---|
| `PUT /api/mission/status` ile `stage1_hits`, `stage1_wrong_hits`, `stage1_order` | yarışma sırasında sıra/counter serbestçe değişiyordu | Bu alanlar Aşama 1 için `STAGE1_EVENT_API_REQUIRED` ile reddedilir. |
| Tracker `send_motion` / fire candidate | Manuel modda otomatik komut sızabilirdi | Kilitli Aşama 1’de `MANUAL_TRACKING_MOTION_BLOCKED` ve `MANUAL_OPERATOR_COMMAND_REQUIRED`. |
| Motion ekranı `test-jog` | Yarışma manuel niyeti görev bağlamına bağlı değildi | `POST /api/mission/manual-motion`; yalnız `COMPETITION + stage1` bağlamında kilitli plan + çalışan timer + Gateway zorunlu. |

## Aşama 1 akışı

1. Operatör dört benzersiz hedef sırasını girer; ilk hedef `Balistik Füze` değilse API reddeder.
2. `POST /api/mission/stage1/start` read-back sonrası sırayı ve zamanlayıcıyı aynı atomik geçişte başlatır.
3. Yarışma başlamadan sıra düzeltilebilir; başladıktan sonra kilitlidir.
4. `LIVE_TEST`/`VIDEO_DEMO`da manuel hareket ve FIRE yalnız Gateway preflight ile çalışır; hedef planı/timer aranmaz. `COMPETITION + Aşama 1`de ise kilitli/çalışan görev zorunludur.
5. Doğru imha, yalnız sıradaki hedef için 5/10/20 puanla kaydedilir. Yanlış hedef ayrı olay ve `-5` ceza üretir.
6. Ham görev puanı 80 ile sınırlıdır; ancak dört hedef tamamlanıp ham puan 80 olduğunda `20 × kalan_saniye / 300` bonusu eklenir.
7. Aşama değişiminde `STP` gönderilir, tracking döngüsü ve seçili tracker kapanır.

## Kanıt

`backend/tests/test_mission_operations.py`:

- yanlış ilk hedef reddi;
- kilit/timer zorunluluğu;
- dört sıradaki 20 puanlık hit, 75. saniyede `80 ham + 15 bonus`;
- yanlış hedef sonrası `90` net puan.

`backend/tests/test_phase65_stage1_manual_mission.py`:

- locked manual modda tracking motion/fire NO_FIRE;
- explicit manuel fire Gateway üzerinden `LZR,1` ACK;
- manual movement Gateway üzerinden `SPD` ve `STP`;
- güvenli manual-stop;
- stage geçişinde tracker + motion safing.

Son doğrulama: seçili P0/P1 backend sözleşme testleri `33 passed`; frontend `vue-tsc -b` geçti.

## Operatör arayüzü

`MissionModesView` artık planı kaydetme/kilitleme, sıradaki hedef, ham/ceza/bonus ayrımı, doğru/yanlış olay kaydı ve doğrudan manuel FIRE sunar. `MotionView` klavye ve gamepad için dead-zone destekler; key-up, browser blur, görünürlük kaybı veya gamepad nötr/kopma durumunda Gateway `STP` çağrısı üretir.

`DRY_RUN`, `LIVE_TEST`, `VIDEO_DEMO` ve `COMPETITION` Cockpit güvenlik panelinden seçilir. LIVE_TEST/VIDEO_DEMO manual hareket ve fire için Aşama 1 planı veya yarışma timer'ı istemez. Sadece `COMPETITION + stage1` hedef planı/timer kilidine bağlanır; stage2/stage3 bu durumdan bağımsızdır.
