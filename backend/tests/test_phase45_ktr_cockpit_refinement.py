from pathlib import Path

from fastapi.testclient import TestClient


def test_phase45_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200
    assert client.get("/cockpit?ktr_demo=1&perf=low").status_code == 200


def test_phase45_header_short_labels_and_truth_mode() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    topbar = Path("frontend/src/components/cockpit/CockpitTopBar.vue").read_text(encoding="utf-8")

    assert "PHASE 45" in cockpit
    assert "TRUTH " in cockpit
    assert "KTR Fixture" in cockpit
    assert "Real Frame Dev" in cockpit
    assert "Live System" in cockpit
    assert "YOLO Balloon" in cockpit
    assert "Offline Expected" in cockpit
    assert "grid-cols-8" in topbar
    assert "status-card" in topbar


def test_phase45_person_safety_unavailable_not_clear() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "Person Check N/A" in cockpit
    assert "PERSON CHECK: UNAVAILABLE" in cockpit
    assert "personSafetyAvailable" in cockpit
    assert "No clear claim is shown while classifier availability is unknown." in cockpit


def test_phase45_camera_hud_truth_and_compact_target_label() -> None:
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")

    assert "KTR Fixture - Not Live Target" in panel
    assert "Truth:" in panel
    assert "HUD TELEMETRY" in panel
    assert "targetLabelPrefix" in panel
    assert "BALON ADAYI" in cockpit
    assert "person_check=" in panel
    assert "textLength=\"325\"" in panel


def test_phase45_digital_twin_fov_and_no_go_refinement() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "opacity: 0.003" in panel
    assert "opacity: 0.34" in panel
    assert "props.ktrDemoMode || nextState.engagement.person_safety_blocked" in panel
    assert "offset=30mm camera→launcher" in panel
    assert "PERF 10 FPS LOW" in panel
    assert "relative depth estimate" in panel
    assert "document.hidden" in panel


def test_phase45_operator_log_no_screenshot_scrollbar() -> None:
    log_panel = Path("frontend/src/components/cockpit/OperatorLogPanel.vue").read_text(encoding="utf-8")
    evidence = Path("frontend/src/components/cockpit/EvidenceReplayPanel.vue").read_text(encoding="utf-8")

    assert "MAX_VISIBLE_EVENTS = 4" in log_panel
    assert "props.events.slice(0, MAX_VISIBLE_EVENTS)" in log_panel
    assert "overflow-auto" not in log_panel
    assert "View all logs" in log_panel
    assert "Projection" in evidence
    assert "Safety" in evidence


def test_phase45_reports_and_contracts_exist() -> None:
    required = [
        "reports/089_phase45_ktr_cockpit_refinement.md",
        "reports/090_phase45_truth_mode_and_safety_labels.md",
        "reports/091_phase45_digital_twin_visual_readability.md",
        "reports/092_phase45_operator_cards_refinement.md",
        "reports/phase45_visual_acceptance_contract.json",
        "reports/phase45_performance_contract.json",
        "reports/phase45_safety_boundary_check.md",
        "reports/screenshots/phase45_ktr_cockpit_refinement/screenshot_manifest.json",
    ]
    for path in required:
        assert Path(path).exists(), path


def test_phase45_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
