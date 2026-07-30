from fastapi import APIRouter, Depends

from app.api.deps import get_runtime
from pydantic import BaseModel, Field

from app.schemas.serial import (
    SerialCommandResult,
    SerialLogEntry,
    SerialSendJsonRequest,
    SerialSimulateRxRequest,
    SerialStatus,
)
from app.services.runtime_state import RuntimeState

router = APIRouter(prefix="/api/serial", tags=["serial"])


class MagazineResetRequest(BaseModel):
    capacity: int | None = Field(default=None, ge=0, le=64)


@router.get("/status", response_model=SerialStatus)
def get_serial_status(runtime: RuntimeState = Depends(get_runtime)) -> SerialStatus:
    return runtime.serial.status()


@router.get("/logs", response_model=list[SerialLogEntry])
def get_serial_logs(runtime: RuntimeState = Depends(get_runtime)) -> list[SerialLogEntry]:
    return runtime.serial.recent_logs()


@router.post("/send-json", response_model=SerialCommandResult)
def send_json(
    request: SerialSendJsonRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> SerialCommandResult:
    return runtime.serial.send_json(request)


@router.post("/clear-logs", response_model=SerialCommandResult)
def clear_logs(runtime: RuntimeState = Depends(get_runtime)) -> SerialCommandResult:
    return runtime.serial.clear_logs()


@router.post("/magazine/reset", response_model=SerialCommandResult)
def reset_magazine(
    request: MagazineResetRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> SerialCommandResult:
    return runtime.serial.reset_magazine(request.capacity)


@router.post("/simulate-rx", response_model=SerialCommandResult)
def simulate_rx(
    request: SerialSimulateRxRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> SerialCommandResult:
    return runtime.serial.simulate_rx(request)
