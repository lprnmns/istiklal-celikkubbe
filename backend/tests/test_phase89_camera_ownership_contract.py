from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.schemas.camera_runtime import CameraRuntimeProfile


class _Frame:
    shape = (360, 640, 3)

    def copy(self):
        return self


def test_stale_camera_frame_is_not_reported_as_live_evidence(client: TestClient) -> None:
    camera = client.app.state.runtime.camera_runtime
    camera.profile = CameraRuntimeProfile(
        source_type="laptop",
        device_id="camera_dev_video0",
        device_path="/dev/video0",
        width=640,
        height=360,
        fps=30,
    )
    camera.last_frame = _Frame()
    camera.last_frame_at = time.time() - 10
    camera.last_capture_backend = "opencv"

    stale = camera.status()
    assert stale.last_frame_age_ms is not None and stale.last_frame_age_ms >= 9000
    assert stale.is_real_camera_evidence is False
    assert stale.running is False

    camera.last_frame_at = time.time()
    fresh = camera.status()
    assert fresh.is_real_camera_evidence is True
    assert fresh.running is True


def test_cockpit_does_not_auto_claim_camera_from_browser_and_backend() -> None:
    source = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "backendCameraConfigured" in source
    assert "Waiting for `realFrameEvidence` creates a deadlock" in source
    assert "backend !== 'released'" in source
    assert "'fallback', 'released'" not in source
    assert "if (!props.ktrDemoMode) void startBrowserCamera()" not in source
    assert "Browser getUserMedia is an explicit engineering fallback only" in source


def test_cockpit_uses_browser_safe_single_frame_preview_instead_of_mjpeg_img() -> None:
    api = Path("backend/app/api/vision.py").read_text(encoding="utf-8")
    frontend_api = Path("frontend/src/api/vision.ts").read_text(encoding="utf-8")
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert '@camera_router.get("/frame.jpg")' in api
    assert '"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"' in api
    assert "/api/camera/frame.jpg" in frontend_api
    assert "refreshBackendFrame" in panel
    assert "URL.createObjectURL(blob)" in panel
    assert 'cache: \'no-store\'' in panel
    assert ':src="props.streamUrl"' not in panel


def test_single_frame_endpoint_is_no_store_jpeg(client: TestClient) -> None:
    response = client.get("/api/camera/frame.jpg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.content.startswith(b"\xff\xd8")


def test_camera_preview_consumers_share_one_capture_worker() -> None:
    service = Path("backend/app/services/camera_runtime_service.py").read_text(encoding="utf-8")
    pipeline = Path("backend/app/services/vision_pipeline.py").read_text(encoding="utf-8")
    api = Path("backend/app/api/vision.py").read_text(encoding="utf-8")

    assert "def live_preview_frame(self):" in service
    assert "self._ensure_capture_worker(path)" in service
    assert "frame, warnings = self.live_preview_frame()" in service
    assert "time.sleep(1 / max(self.profile.fps, 1))" in service
    assert 'return None, ["windows_camera_worker_warming"]' in service
    assert "self.camera_runtime.live_preview_frame()" in pipeline
    assert "runtime.camera_runtime.live_preview_frame()" in api


def test_live_camera_does_not_overlay_mock_detections_on_real_camera() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "latestFrameMatchesSelectedCamera" in cockpit
    assert "frameOrigin === 'real_capture'" in cockpit
    assert "sourceKind === 'real_camera'" in cockpit
    assert ':latest-frame="latestFrameMatchesSelectedCamera ? latestFrame : null"' in cockpit
    assert ':vision-bodies="activeBodies"' in cockpit
