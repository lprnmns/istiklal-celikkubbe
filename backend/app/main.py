import asyncio
from contextlib import suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.calibration import router as calibration_router
from app.api.color import router as color_router
from app.api.hardware import router as hardware_router
from app.api.devices import router as devices_router
from app.api.device_profiles import router as device_profiles_router
from app.api.first_run import router as first_run_router
from app.api.interfaces import router as interfaces_router
from app.api.logs import router as logs_router
from app.api.routes_health import router as health_router
from app.api.decision import router as decision_router
from app.api.data_lab import router as data_lab_router
from app.api.demo import router as demo_router
from app.api.digital_twin import router as digital_twin_router
from app.api.engagement_evidence import router as engagement_evidence_router
from app.api.dataset import annotation_router, dataset_router, session_router
from app.api.models import router as models_router
from app.api.mission import router as mission_router
from app.api.motion import router as motion_router
from app.api.operator_config import router as operator_config_router
from app.api.person_safety import router as person_safety_router
from app.api.replay import router as replay_router
from app.api.reports import router as reports_router
from app.api.release import router as release_router
from app.api.self_test import router as self_test_router
from app.api.setup import router as setup_router
from app.api.stage3 import router as stage3_router
from app.api.routes_motor import router as motor_router
from app.api.routes_pico import router as pico_router
from app.api.routes_safety import router as safety_router
from app.api.safety_zones import router as safety_zones_router
from app.api.routes_serial import router as serial_router
from app.api.routes_system import router as system_router
from app.api.routes_ws import router as websocket_router
from app.api.vision import camera_router, vision_router
from app.services.config_service import ConfigService, default_config_path
from app.services.log_service import default_log_dir
from app.services.runtime_state import build_runtime
from app.services.storage_paths import project_root


def create_app(
    config_path: Path | None = None,
    log_dir: Path | None = None,
    report_dir: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="ISTIKLAL Command Center Backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:8014",
            "http://localhost:8014",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    config = ConfigService(config_path or default_config_path()).load()
    app.state.runtime = build_runtime(config=config, log_dir=log_dir or default_log_dir(), report_dir=report_dir)

    @app.on_event("startup")
    async def start_gateway_maintenance() -> None:
        async def maintain() -> None:
            while True:
                await asyncio.to_thread(app.state.runtime.command_gateway.maintenance_tick, app.state.runtime)
                await asyncio.sleep(0.1)

        app.state.gateway_maintenance_task = asyncio.create_task(maintain())

    @app.on_event("shutdown")
    async def stop_gateway_maintenance() -> None:
        task = getattr(app.state, "gateway_maintenance_task", None)
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    app.include_router(health_router)
    app.include_router(decision_router)
    app.include_router(system_router)
    app.include_router(safety_router)
    app.include_router(safety_zones_router)
    app.include_router(motor_router)
    app.include_router(hardware_router)
    app.include_router(devices_router)
    app.include_router(device_profiles_router)
    app.include_router(motion_router)
    app.include_router(operator_config_router)
    app.include_router(setup_router)
    app.include_router(pico_router)
    app.include_router(serial_router)
    app.include_router(calibration_router)
    app.include_router(color_router)
    app.include_router(vision_router)
    app.include_router(camera_router)
    app.include_router(models_router)
    app.include_router(mission_router)
    app.include_router(stage3_router)
    app.include_router(person_safety_router)
    app.include_router(session_router)
    app.include_router(annotation_router)
    app.include_router(dataset_router)
    app.include_router(data_lab_router)
    app.include_router(demo_router)
    app.include_router(digital_twin_router)
    app.include_router(engagement_evidence_router)
    app.include_router(replay_router)
    app.include_router(self_test_router)
    app.include_router(first_run_router)
    app.include_router(interfaces_router)
    app.include_router(reports_router)
    app.include_router(release_router)
    app.include_router(logs_router)
    app.include_router(websocket_router)
    _enable_static_frontend(app, config)
    return app


def _enable_static_frontend(app: FastAPI, config) -> None:
    frontend_dist = project_root() / "frontend" / "dist"
    index_path = frontend_dist / "index.html"
    if not config.runtime_mode.frontend_static_enabled or not index_path.exists():
        return
    assets_path = frontend_dist / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=assets_path), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path == "api" or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not found")
        requested = frontend_dist / full_path
        if requested.is_file():
            return FileResponse(requested)
        return FileResponse(index_path)


app = create_app()
