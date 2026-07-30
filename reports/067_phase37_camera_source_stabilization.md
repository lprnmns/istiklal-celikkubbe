# Phase 37 Camera Source Stabilization

Safety invariant: `no_physical_command_generated=true`

Phase 37 stabilizes the USB camera display path without changing the tracker or physical-control behavior.

Known working capture profile:

```bash
ffmpeg -y -f v4l2 -input_format mjpeg -video_size 1280x720 -i /dev/video2 -frames:v 1 -update 1 /tmp/usb_camera_test.jpg
```

Implemented behavior:
- `/dev/video2` remains explicitly selectable through the camera runtime profile.
- OpenCV persistent capture is attempted first where available.
- If OpenCV fails and ffmpeg succeeds, the runtime reports `selected_backend=ffmpeg` and the UI treats the frame as real camera evidence.
- The cockpit no longer relies only on the old `USB_CAMERA_FRAME_UNAVAILABLE` placeholder state when ffmpeg can capture a valid frame.

Camera diagnostic fields exposed:
- `selected_device`
- `selected_backend`
- `input_format`
- `resolution`
- `last_frame_age_ms`
- `last_capture_error`
- `is_real_camera_evidence`

The implementation does not fake camera evidence. If no frame is available, the blocker remains visible through `last_capture_error` and cockpit warnings.

