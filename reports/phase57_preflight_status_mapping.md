# Phase 57: Pre-Flight Diagnostics Status & LED Mapping

This document details how the startup checklist LED states are mapped to system data points.

| Diagnostic Item | Data Source | Green State | Yellow/Amber State (Degraded) | Red State (Failure) |
|---|---|---|---|---|
| **1. Pico Bağlantısı** | `truth.picoHealthy` | Connected via serial port | expected offline in dev (`real_serial_enabled` is false) | Hardware/permission error |
| **2. Pico Komut Kabulü** | `serial.status` | Last ACK is verified (`'ack'`) | expected offline in dev (`real_serial_enabled` is false) | Timeout or NACK received |
| **3. Pico Telemetri Cevabı** | `serial.status` | Telemetry packets active | expected offline in dev (`real_serial_enabled` is false) | No telemetry packet received |
| **4. Step Motor Sürücüleri** | `system.picoTelemetry` | Driver active (`DRV,1`) | Driver disabled/telemetry unknown | Thermal/fault state detected |
| **5. Kamera Sistemi** | `runtime.inventory` | Cameras > 0 and stream active | Device connected, stream inactive | No cameras detected |
| **6. Algılama Modeli** | `runtime.visionStatus` | YOLOv8s Balloon loaded | Circle Finder fallback loaded | Load failure |
| **7. 3D Dijital İkiz** | `digitalTwinState` | GLB Turret mesh rendering | Degraded/fallback mesh | Viewport render error |
