# ISTIKLAL C2 Linux First Run

Bu launcher, ISTIKLAL C2 Console'u yerel FastAPI backend ve hazır frontend static build ile başlatır.

## Güvenlik

- Başlatıcı yalnızca yazılımı çalıştırır.
- Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya hardware enable çağrısı yapmaz.
- Varsayılan invariant: `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`.

## Çalıştırma

```bash
chmod +x release/linux/start_istiklal_c2.sh
./release/linux/start_istiklal_c2.sh
```

Python 3.12+ ve `uv` gerekir. Frontend `frontend/dist` içinde hazır gelmelidir; runtime sırasında `pnpm build` çalıştırılmaz.

## Saha Notları

- Pico görünmüyorsa kullanıcı `dialout` grubunda olmayabilir.
- Kamera yoksa sistem mock/no-camera fallback ile güvenli açılır.
- Production YOLO modeli yoksa OpenCV daire algılayıcı yalnızca test adaptörü olarak kalır; yarışma modeli değildir.
