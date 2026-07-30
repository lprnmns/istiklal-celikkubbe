from __future__ import annotations

from types import SimpleNamespace

from app.services.vision_pipeline import VisionPipeline


class _Registry:
    def __init__(self, models: dict[str, object]) -> None:
        self._models = models
        self.requests: list[str] = []

    def get_model(self, model_id: str):
        self.requests.append(model_id)
        return self._models[model_id]


def test_setup_selected_balloon_path_overrides_stale_registry_model(tmp_path) -> None:
    selected = tmp_path / "selected.pt"
    selected.write_bytes(b"selected")
    stale = tmp_path / "stale.pt"
    stale.write_bytes(b"stale")
    registry = _Registry(
        {
            "legacy-balloon-yolo": SimpleNamespace(
                model_id="legacy-balloon-yolo",
                file_path=str(stale),
                class_names=["dost", "dusman"],
            )
        }
    )
    pipeline = object.__new__(VisionPipeline)
    pipeline.vision = SimpleNamespace(body_model_path=None, balloon_model_path=str(selected))
    pipeline.vision_runtime = SimpleNamespace(
        profile=SimpleNamespace(active_body_model_id=None, active_balloon_model_id="legacy-balloon-yolo"),
        models=registry,
    )

    assert pipeline._active_yolo_model_specs() == [
        {
            "role": "balloon",
            "model_id": "setup_balloon_path",
            "path": str(selected),
            "class_names": [],
        }
    ]
    assert registry.requests == []


def test_registry_still_fills_a_role_not_selected_in_setup(tmp_path) -> None:
    selected_balloon = tmp_path / "selected-balloon.pt"
    selected_balloon.write_bytes(b"balloon")
    registry_body = tmp_path / "registry-body.pt"
    registry_body.write_bytes(b"body")
    registry = _Registry(
        {
            "body-v1": SimpleNamespace(
                model_id="body-v1",
                file_path=str(registry_body),
                class_names=["f16"],
            )
        }
    )
    pipeline = object.__new__(VisionPipeline)
    pipeline.vision = SimpleNamespace(body_model_path=None, balloon_model_path=str(selected_balloon))
    pipeline.vision_runtime = SimpleNamespace(
        profile=SimpleNamespace(active_body_model_id="body-v1", active_balloon_model_id=None),
        models=registry,
    )

    specs = pipeline._active_yolo_model_specs()

    assert [item["role"] for item in specs] == ["balloon", "body"]
    assert specs[0]["path"] == str(selected_balloon)
    assert specs[1]["model_id"] == "body-v1"
    assert registry.requests == ["body-v1"]
