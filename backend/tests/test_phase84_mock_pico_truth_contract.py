from pathlib import Path


def test_mock_transport_cannot_be_reported_as_a_healthy_physical_pico() -> None:
    truth = Path("frontend/src/composables/useRuntimeTruth.ts").read_text(encoding="utf-8")

    assert "hardware.status.transport_mode !== 'mock'" in truth
    assert "serial.status.transport_mode !== 'mock'" in truth
    assert "serial.status.transport_source !== 'mock'" in truth
    assert "const picoHealthy = computed(() => hardwarePicoHealthy.value || serialPicoHealthy.value)" in truth
    assert "const picoSimulated" in truth
    assert "Pico simülasyon" in truth


def test_primary_operator_surfaces_show_mock_pico_as_simulation() -> None:
    cockpit = Path("frontend/src/views/CockpitView.vue").read_text(encoding="utf-8")
    console = Path("frontend/src/views/CompetitionConsoleView.vue").read_text(encoding="utf-8")
    system_map = Path("frontend/src/views/SystemMapView.vue").read_text(encoding="utf-8")

    assert "if (truth.picoSimulated.value) return 'Simülasyon'" in cockpit
    assert "PICO SİMÜLASYON" in console
    assert "const picoConnected = computed(() => truth.picoHealthy.value)" in system_map
    assert "'SIMÜLASYON'" in system_map
