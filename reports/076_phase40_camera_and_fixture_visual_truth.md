# Phase 40 Camera and Fixture Visual Truth

Camera display rules remain truth-first:

- Laptop camera development mode is allowed for UI verification.
- External USB camera absence is shown as `USB OFFLINE_EXPECTED`, not a critical failure.
- Pico absence is shown as `PICO OFFLINE_EXPECTED`, not a critical failure.
- Fixture/surrogate target overlays remain labelled as `FIXTURE TARGET - NOT REAL CAMERA EVIDENCE`.
- No screenshot or report claims external USB camera acceptance while the USB camera is absent.

During Phase 40 development, the laptop camera was available as `/dev/video0` through OpenCV. This is valid for cockpit visual verification, but it is not external USB camera acceptance.

`no_physical_command_generated=true`
