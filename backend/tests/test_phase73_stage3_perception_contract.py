from __future__ import annotations

import time
from types import SimpleNamespace

import numpy as np
from fastapi.testclient import TestClient

from app.schemas.color import ColorClassifySampleRequest, TeamValue
from app.schemas.color import ColorCalibrationReferenceRequest
from app.schemas.model_registry import ModelMetadata
from app.schemas.stage3_range import STAGE3_CLASSES, Stage3RangeObservationCreate
from app.schemas.vision import BBox, BalloonDetection, BodyDetection, VisionEvent
from app.services.stage3_range_calibration_service import Stage3RangeCalibrationService
from app.services.vision_pipeline import VisionPipeline


class _Box:
    def __init__(self, xyxy: list[float], confidence: float, class_id: int) -> None:
        self.xyxy = np.asarray([xyxy], dtype=float)
        self.conf = np.asarray([confidence], dtype=float)
        self.cls = np.asarray([class_id], dtype=float)


class _Result:
    def __init__(self, boxes: list[_Box], names: dict[int, str]) -> None:
        self.boxes = boxes
        self.names = names


def _parser_pipeline() -> VisionPipeline:
    pipeline = object.__new__(VisionPipeline)
    pipeline.vision_runtime = SimpleNamespace(profile=SimpleNamespace(target_class_map={}))
    return pipeline


def _body(track_id: int = 7, body_id: int = 1) -> BodyDetection:
    return BodyDetection(
        id=body_id,
        track_id=track_id,
        class_name="f16",
        class_id=0,
        confidence=0.95,
        bbox=BBox(x=10, y=10, w=60, h=60),
    )


def _calibrate_real_iff(classifier) -> None:
    enemy = _body(track_id=701)
    enemy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    enemy_frame[10:70, 10:70] = (0, 0, 255)
    for frame_id in range(1, 6):
        enemy = classifier.classify_frame_bodies(enemy_frame, frame_id, [enemy], [])[0]
        if frame_id >= 3:
            classifier.record_calibration_reference(
                ColorCalibrationReferenceRequest(expected_team=TeamValue.ENEMY, capture_id=f"enemy-{frame_id}")
            )

    friend = _body(track_id=702)
    friend_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    friend_frame[10:70, 10:70] = (255, 0, 0)
    for frame_id in range(6, 9):
        friend = classifier.classify_frame_bodies(friend_frame, frame_id, [friend], [])[0]
        classifier.record_calibration_reference(
            ColorCalibrationReferenceRequest(expected_team=TeamValue.FRIEND, capture_id=f"friend-{frame_id}")
        )
    assert classifier.calibration_status().valid is True


def test_yolo_tensor_class_semantics_are_not_collapsed_into_balloons() -> None:
    pipeline = _parser_pipeline()
    result = _Result([_Box([10, 20, 80, 100], 0.93, 0)], {0: "F-16", 1: "balloon"})

    bodies, balloons, warnings = pipeline._detections_from_results(
        [result], 640, 360, model_id="body-v1", role="body", class_names=["f16", "balloon"]
    )
    assert len(bodies) == 1
    assert bodies[0].class_name == "f16"
    assert bodies[0].class_id == 0
    assert balloons == []
    assert warnings == []

    body_and_balloon = _Result(
        [_Box([10, 20, 80, 100], 0.93, 0), _Box([90, 20, 120, 50], 0.88, 1)],
        {0: "F-16", 1: "balloon"},
    )
    bodies, balloons, warnings = pipeline._detections_from_results(
        [body_and_balloon], 640, 360, model_id="combined-v1", role="combined", class_names=["f16", "balloon"]
    )
    assert [item.class_name for item in bodies] == ["f16"]
    assert len(balloons) == 1
    assert warnings == []

    mismatched = _Result([_Box([10, 20, 80, 100], 0.93, 0)], {0: "balloon"})
    bodies, balloons, warnings = pipeline._detections_from_results(
        [mismatched], 640, 360, model_id="body-v1", role="body", class_names=["f16"]
    )
    assert bodies == []
    assert balloons == []
    assert warnings == ["model_class_mapping_mismatch:body-v1:0"]

    generic = _Result([_Box([10, 20, 80, 100], 0.93, 0)], {0: "target_carrier"})
    bodies, balloons, warnings = pipeline._detections_from_results(
        [generic], 640, 360, model_id="a2-body-v1", role="body", class_names=["target_carrier"]
    )
    assert [item.class_name for item in bodies] == ["generic_target"]
    assert balloons == []
    assert warnings == []


def test_real_body_roi_iff_needs_temporal_enemy_evidence_and_excludes_balloon_pixels(client: TestClient) -> None:
    classifier = client.app.state.runtime.color_classifier
    body = _body()
    balloon = BalloonDetection(id=1, confidence=0.9, bbox=BBox(x=30, y=30, w=25, h=25), center_x=42, center_y=42)
    # Red body is enemy in the configured profile; the blue balloon is friend
    # coloured on purpose.  It is inside the body ROI and must not alter IFF.
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[10:70, 10:70] = (0, 0, 255)
    frame[30:55, 30:55] = (255, 0, 0)

    for frame_id in (1, 2):
        current = classifier.classify_frame_bodies(frame, frame_id, [body], [balloon])[0]
        result = classifier.latest_for_body(current)
        assert current.target_team == "unknown"
        assert result is not None
        assert result.evidence_source == "real_body_roi"
        assert result.balloon_mask_applied is True
        assert result.usable_for_live_fire is False
        body = current

    current = classifier.classify_frame_bodies(frame, 3, [body], [balloon])[0]
    result = classifier.latest_for_body(current)
    assert result is not None
    assert current.target_team == "enemy"
    assert result.usable_for_live_fire is True
    assert result.consistent_frames == 3
    assert result.profile_hash

    # The engineering sample endpoint remains informational and cannot replace
    # a current body-ROI record.
    classifier.reset()
    classifier.classify_sample(
        ColorClassifySampleRequest(
            frame_id=4,
            detection_id=1,
            mock_team=TeamValue.ENEMY,
            balloon_bbox_present=True,
            body_pixel_count=400,
        )
    )
    ready, detail = classifier.real_iff_ready_for(_body(track_id=99))
    assert ready is False
    assert "No current body-ROI" in detail


def test_range_profile_requires_field_distances_and_invalidates_on_model_change(tmp_path) -> None:
    model_path = tmp_path / "body.pt"
    model_path.write_bytes(b"body-model-v1")
    service = Stage3RangeCalibrationService(logger=SimpleNamespace(emit=lambda *args, **kwargs: None), path=tmp_path / "range.json")

    for class_name in STAGE3_CLASSES:
        for distance_m in (5.0, 10.0, 15.0):
            service.add_observation(
                Stage3RangeObservationCreate(
                    class_name=class_name,
                    distance_m=distance_m,
                    bbox_height_px=1000.0 / distance_m,
                    capture_id=f"{class_name}-{distance_m}",
                )
            )
    status = service.validate("body-v1", str(model_path))
    assert status.valid is True
    assert status.calibration_hash

    estimate = service.estimate(_body().model_copy(update={"bbox": BBox(x=10, y=10, w=60, h=100)}), "body-v1", str(model_path))
    assert estimate.ready is True
    assert estimate.range_m == 10.0
    assert estimate.lower_bound_m is not None and estimate.upper_bound_m is not None

    model_path.write_bytes(b"body-model-v2")
    changed = service.status("body-v1", str(model_path))
    assert changed.valid is False
    assert changed.reason_codes == ["A3_RANGE_MODEL_FINGERPRINT_MISMATCH"]


def test_real_iff_evidence_cannot_be_reused_for_a_new_frame(client: TestClient) -> None:
    classifier = client.app.state.runtime.color_classifier
    body = _body()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[10:70, 10:70] = (0, 0, 255)
    for frame_id in (1, 2, 3):
        body = classifier.classify_frame_bodies(frame, frame_id, [body], [])[0]

    _calibrate_real_iff(classifier)
    body = classifier.classify_frame_bodies(frame, 9, [body], [])[0]

    ready, detail = classifier.real_iff_ready_for(body, frame_id=10)
    assert ready is False
    assert "current frame" in detail


def test_stage3_readiness_accepts_only_real_iff_and_model_bound_range_profile(client: TestClient, tmp_path) -> None:
    runtime = client.app.state.runtime
    model_path = tmp_path / "f16-body.pt"
    model_path.write_bytes(b"real-model-fixture")
    runtime.model_registry.upsert_model(
        ModelMetadata(
            model_id="f16-body-fixture",
            name="F16 body fixture",
            model_type="body_detector",
            framework="ultralytics",
            file_path=str(model_path),
            file_name="f16-body.pt",
            class_names=["f16", "helicopter", "ballistic_missile", "mini_micro_uav"],
            status="validated",
            provided_by="vision_team",
        )
    )
    runtime.vision_runtime.profile = runtime.vision_runtime.profile.model_copy(update={"active_body_model_id": "f16-body-fixture"})
    for class_name in STAGE3_CLASSES:
        for distance_m in (5.0, 10.0, 15.0):
            runtime.stage3_range.add_observation(
                Stage3RangeObservationCreate(
                    class_name=class_name,
                    distance_m=distance_m,
                    bbox_height_px=1000.0 / distance_m,
                    capture_id=f"fixture-{class_name}-{distance_m}",
                )
            )
    assert runtime.stage3_range.validate("f16-body-fixture", str(model_path)).valid is True

    _calibrate_real_iff(runtime.color_classifier)
    body = _body().model_copy(update={"bbox": BBox(x=10, y=10, w=60, h=80)})
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[10:70, 10:70] = (0, 0, 255)
    for frame_id in (9, 10, 11):
        body = runtime.color_classifier.classify_frame_bodies(frame, frame_id, [body], [])[0]
    body = runtime.stage3_range.attach_estimates([body], "f16-body-fixture", str(model_path))[0]
    event = VisionEvent(
        frame_id=11,
        timestamp_ms=int(time.time() * 1000),
        source="stage3-contract",
        frame_width=640,
        frame_height=360,
        fps=30,
        preprocess_ms=1,
        inference_ms=1,
        postprocess_ms=1,
        total_latency_ms=3,
        body_detections=[body],
        balloon_detections=[BalloonDetection(id=1, confidence=0.9, bbox=BBox(x=80, y=80, w=20, h=20), center_x=90, center_y=90)],
    )
    assert client.put("/api/mission/status", json={"active_stage": "stage3"}).status_code == 200
    runtime.vision.latest_event = event
    decision = runtime.decision_engine.evaluate(runtime)
    gates = {gate.name: gate.status.value for gate in decision.gates}
    # A raw registry entry (even with complete metadata) is not allowed to
    # impersonate a model package with real tensor/golden inference evidence.
    assert gates["a3_body_model_gate"] == "fail"
    assert gates["a3_iff_real_roi_gate"] == "pass"
    assert gates["a3_range_calibration_gate"] == "pass"
    assert gates["range_valid_gate"] == "pass"
