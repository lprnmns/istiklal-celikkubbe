import importlib.util
from pathlib import Path


def _load_capture_module():
    path = Path("scripts/capture_phase20_4_screenshots.py")
    spec = importlib.util.spec_from_file_location("capture_phase20_4_screenshots", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manual_smoke_endpoints_are_rendered_as_separate_rows() -> None:
    module = _load_capture_module()
    rows = module.manual_smoke_rows()
    labels = [label for label, _value in rows]
    assert "/api/demo/readiness, /api/demo/run, /api/demo/latest" not in labels
    assert ("/api/demo/readiness", "HTTP 200") in rows
    assert ("/api/demo/run", "HTTP 200") in rows
    assert ("/api/demo/latest", "HTTP 200") in rows


def test_report_spacing_rows_keep_label_and_value_separate() -> None:
    module = _load_capture_module()
    rows = module.report_spacing_rows()
    assert ("demo_readiness_summary.md", "Contains no_physical_command_generated: true") in rows
    assert all(label and value for label, value in rows)
