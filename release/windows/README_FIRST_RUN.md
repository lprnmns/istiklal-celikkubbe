# ISTIKLAL C2 Windows First Run

`start_istiklal_c2.bat` dosyasına çift tıklayarak taşınabilir konsolu başlatabilirsiniz.

## Güvenlik

- Başlatıcı yalnızca backend ve arayüzü çalıştırır.
- Motor, servo, tetik, atış, GPIO, STEP/DIR/PWM veya hardware enable çağrısı yapmaz.
- Varsayılan invariant: `DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`.

## Gereksinimler

- Python 3.12+
- uv
- Release paketinde hazır `frontend/dist`

Frontend static build yoksa launcher runtime sırasında `pnpm/npm` ile build almaz; paketin eksik veya bozuk olduğunu bildirir.

## İlk Kurulum

İlk çalıştırmada backend bağımlılıkları `.venv` içine kurulur. İnternet yoksa offline wheelhouse veya önceden hazırlanmış release paketi gerekir.
