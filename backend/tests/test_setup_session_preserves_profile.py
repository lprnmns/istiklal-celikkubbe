def test_setup_session_preserves_camera_vision_and_pico_bindings(client):
    runtime = client.app.state.runtime
    camera_profile = runtime.camera_runtime.profile.model_copy(deep=True)
    vision_config = runtime.vision_pipeline.status().model_copy(deep=True)

    response = client.post("/api/setup/reset-session")

    assert response.status_code == 200
    assert response.json()["reset"] is True
    assert runtime.camera_runtime.profile == camera_profile
    status = runtime.vision_pipeline.status()
    assert status.body_model_path == vision_config.body_model_path
    assert status.balloon_model_path == vision_config.balloon_model_path
    assert "SETUP_SESSION_RESET" in runtime.command_gateway.last_preflight.reason_codes
