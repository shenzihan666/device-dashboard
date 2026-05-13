"""FastAPI application factory with structured lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.exception_handlers import register_exception_handlers
from backend.api.middleware import register_middleware
from backend.api.routes import all_routers
from backend.config import get_settings
from backend.core.services.app_settings import AppSettingsState, load_effective
from backend.core.services.heartbeat_registry import HeartbeatRegistry
from backend.core.services.state_projector import StateProjector
from backend.infrastructure.database.models import Base
from backend.infrastructure.database.repositories.settings_repo import (
    SQLAlchemySettingsRepository,
)
from backend.infrastructure.database.session import get_session_factory, init_engine
from backend.infrastructure.websocket.broadcaster import Broadcaster
from backend.logging_config import configure_logging

logger = structlog.get_logger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
_NANO = 1_000_000_000


class HeartbeatManager:
    """Manages the lifecycle of the heartbeat registry based on app settings."""

    def __init__(
        self,
        registry: HeartbeatRegistry,
        broadcaster: Broadcaster,
        check_interval_s: int,
    ) -> None:
        self._registry = registry
        self._broadcaster = broadcaster
        self._check_interval_s = check_interval_s
        self._running = False

    @property
    def registry(self) -> HeartbeatRegistry:
        return self._registry

    async def apply(self, app_settings: AppSettingsState) -> None:
        """Start or stop the heartbeat registry to match *app_settings*."""
        if app_settings.point_to_point_enabled and not self._running:
            await self._registry.start_offline_checker(self._check_interval_s)
            self._running = True
            logger.info("heartbeat_manager_started")
        elif not app_settings.point_to_point_enabled and self._running:
            await self._registry.stop()
            self._registry.clear()
            self._running = False
            await self._broadcaster.broadcast({"type": "heartbeat_update"})
            logger.info("heartbeat_manager_stopped")

    async def shutdown(self) -> None:
        if self._running:
            await self._registry.stop()
            self._running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)

    engine = init_engine(settings)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.db_url.startswith("sqlite"):
        db_path = settings.db_url.split("///")[-1] if "///" in settings.db_url else None
        if db_path:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    state = StateProjector(offline_grace_ns=settings.offline_grace_s * _NANO)
    broadcaster = Broadcaster()

    app.state.projector = state
    app.state.broadcaster = broadcaster

    registry = HeartbeatRegistry(
        offline_grace_ns=settings.heartbeat_grace_s * _NANO,
        broadcaster=broadcaster,
        session_factory=get_session_factory(),
    )
    app.state.heartbeat_registry = registry

    heartbeat_manager = HeartbeatManager(
        registry=registry,
        broadcaster=broadcaster,
        check_interval_s=settings.heartbeat_check_interval_s,
    )
    app.state.heartbeat_manager = heartbeat_manager

    session_factory = get_session_factory()
    async with session_factory() as session:
        settings_repo = SQLAlchemySettingsRepository(session)
        app_settings = await load_effective(settings_repo)

    await heartbeat_manager.apply(app_settings)

    yield

    await heartbeat_manager.shutdown()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="WeCom AI Connection Dashboard",
        version="2.0.0",
        lifespan=lifespan,
    )

    register_middleware(app, settings)
    register_exception_handlers(app)

    for router in all_routers:
        app.include_router(router)

    _mount_frontend(app)

    return app


def _mount_frontend(app: FastAPI) -> None:
    """Mount the frontend SPA if it has been built."""
    dist_dir = FRONTEND_DIR / "dist"

    if dist_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa(full_path: str):
            file_path = dist_dir / full_path
            if full_path and file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(dist_dir / "index.html"))

    elif FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        async def index():
            return FileResponse(str(FRONTEND_DIR / "index.html"))


# Module-level app instance for uvicorn
app = create_app()
