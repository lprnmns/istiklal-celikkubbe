from fastapi import APIRouter, Depends

from app.api.deps import get_runtime
from app.schemas.hardware import (
    HardwareCapabilities,
    HardwareConnectReadOnlyRequest,
    HardwareConnectResult,
    HardwareCommandBlockResult,
    HardwareRiskyCommandRequest,
    HardwareSerialPort,
    HardwareStatus,
    HardwareTelemetry,
    HardwareServoTuneRequest,
    HardwarePicoDiscoveryResult,
    HardwareTestJogRequest,
    HardwareTestCommandResult,
)
from app.schemas.log import LogLevel
from app.services.runtime_state import RuntimeState
import asyncio

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.post("/discover-pico", response_model=HardwarePicoDiscoveryResult)
async def discover_pico(runtime: RuntimeState = Depends(get_runtime)) -> HardwarePicoDiscoveryResult:
    port, code, detected_baudrate = await asyncio.to_thread(runtime.serial.discover_gateway_pico, 5.0, 460800)
    return HardwarePicoDiscoveryResult(
        found=port is not None, port=port, baudrate=detected_baudrate or 460800, reason_code=code,
        detail=f"Pico bulundu: {port}" if port else "5 saniye içinde Pico doğrulanamadı.",
    )


@router.get("/serial/ports", response_model=list[HardwareSerialPort])
def serial_ports(runtime: RuntimeState = Depends(get_runtime)) -> list[HardwareSerialPort]:
    return runtime.hardware.ports()


@router.get("/status", response_model=HardwareStatus)
def hardware_status(runtime: RuntimeState = Depends(get_runtime)) -> HardwareStatus:
    runtime.hardware.poll_readonly()
    return runtime.hardware.status(mock_pico_active=runtime.pico.status().mock_mode)


@router.post("/connect-readonly", response_model=HardwareConnectResult)
def connect_readonly(
    request: HardwareConnectReadOnlyRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> HardwareConnectResult:
    result = runtime.hardware.connect_readonly(request, mock_pico_active=runtime.pico.status().mock_mode)
    if result.accepted:
        runtime.serial.mark_real_readonly_connected(result.status.connection_state)
    return result


@router.post("/disconnect", response_model=HardwareConnectResult)
def disconnect(runtime: RuntimeState = Depends(get_runtime)) -> HardwareConnectResult:
    result = runtime.hardware.disconnect(mock_pico_active=runtime.pico.status().mock_mode)
    runtime.serial.mark_real_readonly_disconnected()
    return result


@router.get("/telemetry", response_model=HardwareTelemetry)
def telemetry(runtime: RuntimeState = Depends(get_runtime)) -> HardwareTelemetry:
    return runtime.hardware.poll_readonly()


@router.get("/capabilities", response_model=HardwareCapabilities)
def capabilities(runtime: RuntimeState = Depends(get_runtime)) -> HardwareCapabilities:
    return runtime.hardware.capabilities()


@router.post("/block-risky-command", response_model=HardwareCommandBlockResult)
def block_risky_command(
    request: HardwareRiskyCommandRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> HardwareCommandBlockResult:
    return runtime.hardware.block_risky_command(request)

@router.post("/test-trigger", response_model=HardwareTestCommandResult)
async def test_trigger(runtime: RuntimeState = Depends(get_runtime)) -> HardwareTestCommandResult:
    result = runtime.command_gateway.test_trigger(runtime, pulse_s=1.0)
    return HardwareTestCommandResult(
        accepted=result.accepted,
        message="Boş hazne tetik testi Gateway üzerinden kabul edildi." if result.accepted else f"Tetik testi engellendi: {', '.join(result.reason_codes)}",
        command=result.command, command_sent=result.physical_command_generated, pico_response=result.detail,
        driver_ack=result.pico_ack, reason_codes=result.reason_codes,
    )

@router.post("/test-servo-tune", response_model=HardwareTestCommandResult)
async def test_servo_tune(
    request: HardwareServoTuneRequest,
    runtime: RuntimeState = Depends(get_runtime),
) -> HardwareTestCommandResult:
    result = runtime.command_gateway.configure_trigger_servo(runtime, request.release_deg, request.fire_deg)
    return HardwareTestCommandResult(
        accepted=result.accepted,
        message="Servo başlangıç ve ateş açıları Pico'ya uygulandı." if result.accepted else f"Servo ayarı engellendi: {', '.join(result.reason_codes)}",
        command=result.command, command_sent=result.physical_command_generated, pico_response=result.detail,
        driver_ack=result.pico_ack, reason_codes=result.reason_codes,
    )

@router.post("/test-jog", response_model=HardwareTestCommandResult)
async def test_jog(request: HardwareTestJogRequest, runtime: RuntimeState = Depends(get_runtime)) -> HardwareTestCommandResult:
    result = runtime.command_gateway.send_motion(runtime, request.speed_x, request.speed_y)
    if not result.accepted:
        return HardwareTestCommandResult(
            accepted=False,
            message=f"Motion blocked by CommandGateway: {', '.join(result.reason_codes) or result.detail}",
            command=result.command,
            command_sent=False,
            pico_response=result.detail,
            driver_ack=result.pico_ack,
            reason_codes=result.reason_codes,
        )
    await asyncio.sleep(request.duration_ms / 1000.0)
    stop = runtime.command_gateway.stop_motion()

    return HardwareTestCommandResult(
        accepted=True,
        message=f"Jog tested: {request.speed_x}, {request.speed_y} for {request.duration_ms}ms.",
        command=result.command,
        command_sent=result.physical_command_generated,
        pico_response=result.detail,
        driver_ack=result.pico_ack,
        safe_stop_response=stop.detail,
        reason_codes=[*result.reason_codes, *stop.reason_codes],
    )


@router.post("/manual-stop", response_model=HardwareTestCommandResult)
async def manual_stop(runtime: RuntimeState = Depends(get_runtime)) -> HardwareTestCommandResult:
    result = runtime.command_gateway.stop_motion()
    return HardwareTestCommandResult(
        accepted=result.accepted,
        message="Manual motion safe-stop sent through CommandGateway." if result.accepted else f"Safe-stop failed: {', '.join(result.reason_codes)}",
    )
