from fastapi import APIRouter, Depends

from app.api.deps import get_runtime
from app.schemas.calibration import (
    CalibrationConfigModel,
    CalibrationPointCreate,
    CalibrationStatus,
    CameraCalibrationConfig,
    DirectionCalibrationProfile,
    DirectionCalibrationStatus,
    DirectionObservationRequest,
    DirectionObservationResult,
    DirectionSimulationRequest,
    DirectionSimulationResult,
    FovEstimateRequest,
    FovEstimateResponse,
)
from app.services.runtime_state import RuntimeState

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


@router.get("/status", response_model=CalibrationStatus)
def get_calibration_status(runtime: RuntimeState = Depends(get_runtime)) -> CalibrationStatus:
    return runtime.calibration.status()


@router.get("/config", response_model=CameraCalibrationConfig)
def get_calibration_config(runtime: RuntimeState = Depends(get_runtime)) -> CameraCalibrationConfig:
    return runtime.calibration.config_model()


@router.put("/config", response_model=CameraCalibrationConfig)
def update_calibration_config(
    update: CalibrationConfigModel,
    runtime: RuntimeState = Depends(get_runtime),
) -> CameraCalibrationConfig:
    return runtime.calibration.update_config(update)


@router.post("/points", response_model=CalibrationStatus)
def add_calibration_point(
    point: CalibrationPointCreate,
    runtime: RuntimeState = Depends(get_runtime),
) -> CalibrationStatus:
    return runtime.calibration.add_point(point)


@router.delete("/points/{point_id}", response_model=CalibrationStatus)
def delete_calibration_point(
    point_id: str,
    runtime: RuntimeState = Depends(get_runtime),
) -> CalibrationStatus:
    return runtime.calibration.delete_point(point_id)


@router.post("/compute", response_model=CalibrationStatus)
def compute_calibration(runtime: RuntimeState = Depends(get_runtime)) -> CalibrationStatus:
    runtime.calibration.compute()
    return runtime.calibration.status()


@router.post("/fov-estimate", response_model=FovEstimateResponse)
def estimate_fov(
    request: FovEstimateRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> FovEstimateResponse:
    return runtime.calibration.fov_estimate(request)


@router.post("/reset", response_model=CalibrationStatus)
def reset_calibration(runtime: RuntimeState = Depends(get_runtime)) -> CalibrationStatus:
    return runtime.calibration.reset()


@router.get("/direction/status", response_model=DirectionCalibrationStatus)
def direction_status(runtime: RuntimeState = Depends(get_runtime)) -> DirectionCalibrationStatus:
    return runtime.calibration.direction_status()


@router.post("/direction/simulate", response_model=DirectionSimulationResult)
def direction_simulate(
    request: DirectionSimulationRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> DirectionSimulationResult:
    return runtime.calibration.direction_simulate(request)


@router.post("/direction/record-observation", response_model=DirectionObservationResult)
def direction_record_observation(
    request: DirectionObservationRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> DirectionObservationResult:
    return runtime.calibration.direction_record_observation(request)


@router.post("/direction/save-profile", response_model=DirectionCalibrationProfile)
def direction_save_profile(runtime: RuntimeState = Depends(get_runtime)) -> DirectionCalibrationProfile:
    return runtime.calibration.direction_save_profile()


@router.post("/direction/reset", response_model=DirectionCalibrationStatus)
def direction_reset(runtime: RuntimeState = Depends(get_runtime)) -> DirectionCalibrationStatus:
    return runtime.calibration.direction_reset()


@router.get("/direction/latest", response_model=DirectionCalibrationProfile)
def direction_latest(runtime: RuntimeState = Depends(get_runtime)) -> DirectionCalibrationProfile:
    return runtime.calibration.direction_latest()
