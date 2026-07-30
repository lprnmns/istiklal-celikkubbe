from pathlib import Path

from fastapi.testclient import TestClient


def test_phase43_routes_and_perf_query_render(client: TestClient) -> None:
    assert client.get("/cockpit").status_code == 200
    assert client.get("/cockpit?ktr_demo=1").status_code == 200
    assert client.get("/cockpit?ktr_demo=1&perf=low").status_code == 200


def test_phase43_layout_and_backend_banner_present() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    topbar = Path("frontend/src/components/cockpit/CockpitTopBar.vue").read_text(encoding="utf-8")

    assert "İSTİKLAL C2" in topbar
    assert "Read-only operational visualization / no physical command generated" in topbar
    assert "cockpit-main-grid" in cockpit
    assert "operator-grid" in cockpit
    assert "Backend bağlantısı yok — canlı veri güncellenmiyor." in cockpit
    assert "PHASE 43" in cockpit
    assert "NO PHYSICAL COMMAND" in cockpit


def test_phase43_camera_hud_polish_and_clamping() -> None:
    panel = Path("frontend/src/components/cockpit/LiveCameraPanel.vue").read_text(encoding="utf-8")

    assert "KTR DEMO FIXTURE - NOT LIVE TARGET" in panel
    assert "truth=fixture" in panel
    assert "hudVignette" in panel
    assert "Math.min(target.bbox.x, props.width - 360)" in panel
    assert "textLength=\"325\"" in panel
    assert "lengthAdjust=\"spacingAndGlyphs\"" in panel


def test_phase43_digital_twin_render_capped_and_simplified_truth() -> None:
    panel = Path("frontend/src/components/digital-twin/DigitalTwinPanel.vue").read_text(encoding="utf-8")

    assert "renderFps" in panel
    assert "metadata 2Hz" in panel
    assert "document.hidden" in panel
    assert "props.performanceMode === 'LOW' ? 10" in panel
    assert "STL-derived simplified digital twin" in panel
    assert "launcher axis / no physical command" in panel
    assert "aim reference only / no physical command" in panel


def test_phase43_safety_invariants(client: TestClient) -> None:
    state = client.get("/api/digital-twin/state").json()
    pico = client.get("/api/pico/protocol/status").json()

    assert state["safety"]["physical_command_enabled"] is False
    assert state["no_physical_command_generated"] is True
    assert pico["latest_telemetry"]["serial_tx_enabled"] is False
    assert pico["latest_telemetry"]["physical_command_enabled"] is False
    assert pico["latest_telemetry"]["no_physical_command_generated"] is True
