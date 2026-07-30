from fastapi.testclient import TestClient


def test_first_run_readiness_profiles(client: TestClient) -> None:
    response = client.post("/api/first-run/check")
    assert response.status_code == 200
    body = response.json()
    profiles = body["profile_statuses"]
    assert profiles["development_ready"] in {"passed", "warning"}
    assert profiles["demo_ready"] in {"passed", "warning"}
    assert profiles["hardware_telemetry_ready"] in {"blocked", "warning"}
    assert "competition_rehearsal_ready" in profiles


def test_device_profile_save_verify_reset(client: TestClient) -> None:
    saved = client.post("/api/device-profiles/save", json={"profile_id": "default"})
    assert saved.status_code == 200
    assert saved.json()["no_physical_command_generated"] is True
    active = client.get("/api/device-profiles/active")
    assert active.status_code == 200
    verified = client.post("/api/device-profiles/verify", json={"profile_id": "default"})
    assert verified.status_code == 200
    assert verified.json()["profile"]["verification_status"] in {
        "mock_verified",
        "demo_verified",
        "hardware_readonly_verified",
        "hardware_pending",
        "mismatch",
    }
    assert verified.json()["profile"]["competition_status"] == "competition_not_verified"
    reset = client.post("/api/device-profiles/reset")
    assert reset.status_code == 200


def test_camera_runtime_requested_actual_fields(client: TestClient) -> None:
    status = client.get("/api/camera/runtime/status")
    assert status.status_code == 200
    body = status.json()
    assert body["requested_width"] == body["profile"]["width"]
    assert "actual_fps_measured" in body
    probe = client.post("/api/camera/runtime/probe-current")
    assert probe.status_code == 200
    assert probe.json()["last_probe_result"]["no_physical_command_generated"] is True


def test_vision_runtime_presets_and_active_verify(client: TestClient) -> None:
    presets = client.get("/api/vision/runtime/presets")
    assert presets.status_code == 200
    assert any(item["name"] == "balanced" for item in presets.json())
    applied = client.post("/api/vision/runtime/apply-preset", json={"preset_name": "balanced"})
    assert applied.status_code == 200
    assert applied.json()["no_physical_command_generated"] is True
    verify = client.post("/api/vision/runtime/verify-active")
    assert verify.status_code == 200
    assert verify.json()["no_physical_command_generated"] is True
    test = client.post("/api/vision/runtime/test-active-model")
    assert test.status_code == 200
    assert test.json()["no_physical_command_generated"] is True


def test_release_status_and_check(client: TestClient) -> None:
    status = client.get("/api/release/status")
    assert status.status_code == 200
    body = status.json()
    assert body["no_physical_command_generated"] is True
    assert "checks" in body
    check = client.post("/api/release/check")
    assert check.status_code == 200


def test_interface_inventory_phase14_fields(client: TestClient) -> None:
    body = client.get("/api/interfaces/inventory").json()
    first = body["interfaces"][0]
    assert "verification_status" in first
    assert "display_name" in first
    assert "category_label" in first
    assert "readiness_profile_dependency" in first
    assert "operator_visible" in first
    assert "export_evidence_path" in first
    ktr = client.get("/api/interfaces/ktr-section").json()["markdown"]
    assert "OpenCV daire algılayıcı yalnızca test adaptörü" in ktr
    assert "Kullanıcı Arayüzü" in ktr
    assert "Yazılımsal Arayüzler" in ktr
    assert "Elektronik Güç/Sinyal Arayüz Tanımı" in ktr
    inventory_md = client.get("/api/interfaces/inventory").json()["interfaces"]
    assert any(item["display_name"] == "Taşınabilir Başlatıcı Arayüzü" for item in inventory_md)


def test_phase14_safety_invariant(client: TestClient) -> None:
    system = client.get("/api/system/state").json()
    hardware = client.get("/api/hardware/status").json()
    assert system["mode"] == "DISARMED"
    assert system["fire_policy"] == "NO_FIRE"
    assert system["dry_run"] is True
    assert system["hardware_enabled"] is False
    assert hardware["physical_command_enabled"] is False
