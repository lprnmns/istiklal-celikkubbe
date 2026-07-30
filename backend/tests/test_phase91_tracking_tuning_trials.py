from pathlib import Path

from fastapi.testclient import TestClient

from app.schemas.tracking import TrackingState, TrackingUpdate
from app.services.tracking_tuning_service import TrackingTuningService


def test_tracking_tuning_records_comparable_metrics(tmp_path: Path, client: TestClient) -> None:
    service = TrackingTuningService(tmp_path / "trials.json")
    tracker = client.app.state.runtime.auto_tracker

    service.start("smooth_precision_pd", tracker)
    service.observe(TrackingUpdate(state=TrackingState.TRACKING, target_center_x=100, target_center_y=100, distance_to_center=42, speed_x=400, speed_y=-200))
    service.observe(TrackingUpdate(state=TrackingState.LOCKED, target_center_x=100, target_center_y=100, distance_to_center=5, speed_x=0, speed_y=0, deadband_zone="locked"))
    service.observe(TrackingUpdate(state=TrackingState.SEARCHING, target_lost_frames=1))
    result = service.finish()["results"][-1]

    assert result["preset_id"] == "smooth_precision_pd"
    assert result["target_frames"] == 2
    assert result["lost_frames"] == 1
    assert result["locked_frames"] == 1
    assert result["mean_error_px"] == 23.5
    assert (tmp_path / "trials.json").exists()


def test_tracking_tuning_api_starts_and_stops_real_tracker(client: TestClient) -> None:
    started = client.post("/api/motion/tracking/tuning/start", json={"preset_id": "field_baseline_pd"})

    assert started.status_code == 200
    assert started.json()["active_trial"]["preset_id"] == "field_baseline_pd"
    assert client.app.state.runtime.auto_tracker.tracking_active is True

    stopped = client.post("/api/motion/tracking/tuning/stop")

    assert stopped.status_code == 200
    assert stopped.json()["active_trial"] is None
    assert stopped.json()["results"][-1]["preset_id"] == "field_baseline_pd"
    assert client.app.state.runtime.auto_tracker.tracking_active is False


def test_live_trial_presets_keep_installed_y_axis_direction(client: TestClient) -> None:
    for preset_id in ("field_baseline_pd", "smooth_precision_pd", "fast_intercept_pd", "kalman_lead_pd"):
        response = client.post(f"/api/motion/tracking/tuning/apply/{preset_id}")
        assert response.status_code == 200
        assert client.app.state.runtime.auto_tracker.invert_y is True
