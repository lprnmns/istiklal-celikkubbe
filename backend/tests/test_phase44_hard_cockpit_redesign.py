from pathlib import Path

from fastapi.testclient import TestClient


def test_phase44_routes_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200
    assert client.get("/cockpit?ktr_demo=1&perf=low").status_code == 200


def test_phase44_hard_layout_replaces_badge_dashboard() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    topbar = Path("frontend/src/components/cockpit/CockpitTopBar.vue").read_text(encoding="utf-8")
    shell = Path("frontend/src/components/layout/AppShell.vue").read_text(encoding="utf-8")

    assert "PHASE 44" in cockpit
    assert "PHASE 43 baseline replaced by Phase 44 hard cockpit redesign" in cockpit
    assert "isCockpitRoute" in shell
    assert '<RouterView v-if="isCockpitRoute" />' in shell
    assert "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)" in cockpit
    assert "height: clamp(520px, calc(100vh - 440px), 610px)" in cockpit
    assert "status-card" in topbar
    assert "Digital Twin Cockpit" in topbar
    assert "Read-only operational visualization / no physical command generated" in topbar


def test_phase44_camera_hud_operator_visuals() -> None:
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "KTR DEMO FIXTURE - NOT LIVE TARGET" in panel
    assert "truth=fixture" in panel
    assert "HUD TELEMETRY" in panel
    assert "hudVignette" in panel
    assert "Math.min(target.bbox.x, props.width - 360)" in panel
    assert "textLength=\"325\"" in panel
    assert "lengthAdjust=\"spacingAndGlyphs\"" in panel


def test_phase44_digital_twin_scene_rebuilt_and_capped() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "new THREE.PerspectiveCamera(38" in panel
    assert "camera.position.set(2.75, 2.05, 3.95)" in panel
    assert "proceduralGroup.scale.setScalar(1.2)" in panel
    assert "const far = 4.15" in panel
    assert "opacity: 0.006" in panel
    assert "render capped {{ renderFps }} FPS" in panel
    assert "document.hidden" in panel
    assert "STL-derived simplified digital twin" in panel
    assert "relative depth estimate" in panel


def test_phase44_reports_and_screenshot_manifest_exist() -> None:
    required = [
        "reports/086_phase44_hard_cockpit_redesign.md",
        "reports/087_phase44_3d_scene_rebuild.md",
        "reports/088_phase44_frontend_performance_mode.md",
        "reports/phase44_visual_acceptance_contract.json",
        "reports/phase44_safety_boundary_check.md",
        "reports/screenshots/phase44_hard_cockpit_redesign/screenshot_manifest.json",
    ]
    for path in required:
        assert Path(path).exists(), path


def test_phase44_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
