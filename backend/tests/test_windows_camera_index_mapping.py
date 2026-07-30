from __future__ import annotations

from app.services.device_manager_service import DeviceManagerService


class _Capture:
    def __init__(self, index: int) -> None:
        self.index = index

    def isOpened(self) -> bool:
        return self.index in {1, 2, 3}

    def set(self, *_args) -> bool:
        return True

    def read(self):
        return (self.index in {1, 2, 3}, object() if self.index in {1, 2, 3} else None)

    def release(self) -> None:
        return None


def test_windows_capture_indices_preserve_real_directshow_gap(monkeypatch) -> None:
    monkeypatch.setattr(
        DeviceManagerService,
        "windows_camera_path_responds",
        staticmethod(lambda path: int(path.rsplit(":", 1)[1]) in {1, 2, 3}),
    )

    assert DeviceManagerService._windows_capture_indices(2) == [1, 2]
