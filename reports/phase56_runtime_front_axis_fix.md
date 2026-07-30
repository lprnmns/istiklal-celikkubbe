# Phase 56 Runtime Front Axis Fix

## Finding

The Phase 56 device-frame contract defines the browser runtime front direction as `+Z`:

- CAD front: `-Y`
- Runtime front: `+Z`
- Transform: `runtimeX=CAD X, runtimeY=CAD Z, runtimeZ=-CAD Y`

The 3D tactical overlay code still used older `-Z` assumptions for:

- target balloon placement,
- camera optical axis line,
- FOV far plane,
- range bands,
- no-go zone position,
- debug labels.

This could make the browser overlay appear on the wrong side of the KTR model and make the weapon/camera relationship look misleading.

## Fix

Runtime overlays now use `+Z` consistently:

- target projection: `camera.z + depth`
- FOV volume: `origin.z + far`
- camera optical axis: positive runtime Z
- range bands: positive runtime Z
- no-go zone: positive runtime Z

## Scope

This is a visualization-axis correction only. It does not modify YOLO detection, tracking behavior, serial communication, Pico behavior, or physical command paths.

## Safety

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
