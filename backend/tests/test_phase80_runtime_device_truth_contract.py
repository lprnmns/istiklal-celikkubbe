from app.schemas.vision_runtime_settings import VisionRuntimeProfile


def test_explicit_cuda_is_rejected_without_silent_cpu_substitution(client) -> None:
    runtime = client.app.state.runtime
    previous_device = runtime.vision_runtime.profile.device
    profile = VisionRuntimeProfile(inference_adapter="opencv_circle_test", device="cuda")

    result = runtime.vision_runtime.apply(profile)

    assert result.accepted is False
    expected = "cuda_unavailable" if runtime.config.vision_runtime.allow_cuda else "cuda_not_allowed"
    assert expected in result.errors
    assert runtime.vision_runtime.profile.device == previous_device


def test_auto_device_reports_cpu_fallback_reason_when_cuda_is_unavailable(client) -> None:
    runtime = client.app.state.runtime
    runtime.config.vision_runtime.allow_cuda = True
    runtime.vision_runtime.cuda_available = lambda: False  # host-independent contract fixture
    profile = VisionRuntimeProfile(inference_adapter="opencv_circle_test", device="auto")

    result = runtime.vision_runtime.apply(profile)

    assert result.accepted is True
    assert result.status.requested_device == "auto"
    assert result.status.resolved_device == "cpu"
    assert result.status.device_reason == "auto_cpu_cuda_unavailable"


def test_warmup_and_benchmark_refuse_test_adapter_instead_of_inventing_latency(client) -> None:
    warmup = client.post("/api/vision/runtime/warmup")
    benchmark = client.post("/api/vision/runtime/benchmark")

    assert warmup.status_code == 200
    assert warmup.json()["accepted"] is False
    assert "REAL_YOLO_ADAPTER_REQUIRED" in warmup.json()["reason_codes"]
    assert benchmark.status_code == 200
    assert benchmark.json()["accepted"] is False
    assert "REAL_YOLO_ADAPTER_REQUIRED" in benchmark.json()["reason_codes"]
    assert "estimated_latency_ms" not in benchmark.json()
