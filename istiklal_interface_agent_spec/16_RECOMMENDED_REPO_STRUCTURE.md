# 16. Önerilen Repo Yapısı

```text
istiklal-command-center/
  README.md
  config/
    config.yaml
    pin_profiles/
      pico2_default.yaml
  backend/
    app/
      main.py
      api/
        routes_health.py
        routes_camera.py
        routes_vision.py
        routes_pico.py
        routes_safety.py
        routes_config.py
        routes_dataset.py
        routes_replay.py
      core/
        settings.py
        event_bus.py
        logging.py
        errors.py
      schemas/
        system.py
        camera.py
        vision.py
        pico.py
        safety.py
        config.py
      services/
        camera_service.py
        vision_service.py
        tracking_service.py
        decision_engine.py
        serial_service.py
        config_service.py
        log_service.py
        replay_service.py
        dataset_service.py
      protocols/
        serial_binary.py
        serial_json.py
        crc16.py
      mocks/
        mock_camera.py
        mock_pico.py
        mock_vision.py
      tests/
        test_config.py
        test_serial_protocol.py
        test_decision_engine.py
        test_pin_validation.py
    pyproject.toml
  frontend/
    src/
      main.ts
      App.vue
      router/
      stores/
        systemStore.ts
        cameraStore.ts
        visionStore.ts
        picoStore.ts
        safetyStore.ts
        logStore.ts
      components/
        layout/
        dashboard/
        camera/
        pico/
        safety/
        motor/
        logs/
        replay/
      views/
        DashboardView.vue
        MissionModesView.vue
        VisionView.vue
        PicoPinoutView.vue
        MotorView.vue
        SafetyView.vue
        CalibrationView.vue
        DatasetView.vue
        ReplayView.vue
        LogsView.vue
        ConfigView.vue
        SelfTestView.vue
      api/
        client.ts
        websocket.ts
      types/
        system.ts
        vision.ts
        pico.ts
        safety.ts
        config.ts
    package.json
    vite.config.ts
  firmware/
    pico2/
      src/
        main.c
        serial_protocol.c
        motor_control.c
        safety.c
      include/
      CMakeLists.txt
  models/
    body/
    balloon/
    model_cards/
  data/
    raw/
    sessions/
    datasets/
  logs/
  reports/
  docs/
    interface-agent-spec/
```

## Modül Sınırları

Backend:

- `api/`: HTTP/WebSocket giriş noktaları
- `services/`: iş mantığı
- `schemas/`: veri modelleri
- `protocols/`: serial protokol
- `mocks/`: donanım yokken geliştirme

Frontend:

- `views/`: sayfalar
- `components/`: UI parçaları
- `stores/`: Pinia state
- `api/`: REST/WebSocket client
- `types/`: TypeScript tipleri

## Reports

```text
reports/
  001_repo_analysis.md
  002_backend_skeleton.md
  003_dashboard_ui.md
```
