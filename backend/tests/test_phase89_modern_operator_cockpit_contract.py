from pathlib import Path


COCKPIT = Path("frontend/src/views/CockpitView.vue")
CAMERA = Path("frontend/src/components/cockpit/LiveCameraPanel.vue")
DRAWER = Path("frontend/src/components/cockpit/EngineerTechnicalTabs.vue")


def test_operator_surface_has_two_primary_panels_and_one_action_dock() -> None:
    cockpit = COCKPIT.read_text(encoding="utf-8")

    assert 'class="cockpit-main-grid"' in cockpit
    assert 'class="camera-secondary-section"' in cockpit
    assert 'class="hero-world-section"' in cockpit
    assert 'class="operator-dock"' in cockpit
    assert "Hedefi bırak" in cockpit
    assert "Takibi başlat" in cockpit
    assert ">FIRE<" in cockpit
    assert "SAFE STOP" in cockpit


def test_legacy_operator_layout_blocks_are_removed() -> None:
    cockpit = COCKPIT.read_text(encoding="utf-8")

    for legacy_class in (
        "operator-actions",
        "operator-operation-strip",
        "camera-secondary-toolbar",
        "mission-grid-primary",
        "mission-grid-secondary",
    ):
        assert legacy_class not in cockpit


def test_operator_camera_hides_engineering_truth_overlays() -> None:
    camera = CAMERA.read_text(encoding="utf-8")

    assert 'v-if="!props.operatorMode" class="absolute right-4 top-4' in camera
    assert 'v-if="!props.operatorMode" class="absolute right-4 top-[86px]' in camera
    assert 'v-if="!props.operatorMode" class="absolute bottom-4 left-4' in camera
    assert ':show-local-controls="false"' in COCKPIT.read_text(encoding="utf-8")


def test_engineering_controls_live_in_accessible_reka_drawer() -> None:
    cockpit = COCKPIT.read_text(encoding="utf-8")
    drawer = DRAWER.read_text(encoding="utf-8")

    assert "<EngineerTechnicalTabs" in cockpit
    assert "DialogRoot" in drawer
    assert "DialogOverlay" in drawer
    assert "DialogContent" in drawer
    assert "TabsRoot" in drawer
    for tab in ("Kamera", "Algılama", "Hareket", "Kalibrasyon", "Kayıtlar"):
        assert tab in drawer


def test_operator_layout_is_one_viewport_until_mobile_breakpoint() -> None:
    cockpit = COCKPIT.read_text(encoding="utf-8")

    assert "height:100vh" in cockpit
    assert "overflow:hidden" in cockpit
    assert 'grid-template-areas:"camera world"' in cockpit
    assert "@media(max-width:1180px)" in cockpit


def test_operator_labels_translate_internal_profile_and_stage_names() -> None:
    cockpit = COCKPIT.read_text(encoding="utf-8")

    assert "if (profile === 'DRY_RUN') return 'TEST'" in cockpit
    assert "if (profile === 'LIVE_TEST') return 'CANLI TEST'" in cockpit
    assert "if (profile === 'COMPETITION') return 'YARIŞMA'" in cockpit
    assert "if (mission.snapshot.state.active_stage === 'stage1') return 'AŞAMA 1'" in cockpit
