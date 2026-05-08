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
from backend.core.services.poller_service import PollerService
from backend.core.services.state_projector import StateProjector
from backend.infrastructure.database.models import Base
from backend.infrastructure.database.repositories.entity_repo import (
    SQLAlchemyEntityRepository,
)
from backend.infrastructure.database.repositories.event_repo import (
    SQLAlchemyCursorRepository,
    SQLAlchemyEventRepository,
)
from backend.infrastructure.database.repositories.settings_repo import (
    SQLAlchemySettingsRepository,
)
from backend.infrastructure.database.session import get_session_factory, init_engine
from backend.infrastructure.external.grafana_client import GrafanaClient
from backend.infrastructure.websocket.broadcaster import Broadcaster
from backend.logging_config import configure_logging

logger = structlog.get_logger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
_NANO = 1_000_000_000


class PollerManager:
    """Manages the lifecycle of the Grafana Loki poller based on app settings."""

    def __init__(
        self,
        settings: object,
        state: StateProjector,
        broadcaster: Broadcaster,
    ) -> None:
        self._settings = settings
        self._state = state
        self._broadcaster = broadcaster
        self._poller: PollerService | None = None

    @property
    def poller(self) -> PollerService | None:
        return self._poller

    async def apply(self, app_settings: AppSettingsState) -> None:
        """Start or stop the poller to match *app_settings*."""
        should_run = app_settings.grafana_enabled and bool(self._settings.api_token)  # type: ignore[attr-defined]
        if should_run and self._poller is None:
            await self._start()
        elif not should_run and self._poller is not None:
            await self._stop()

    async def _start(self) -> None:
        settings = self._settings  # type: ignore[attr-defined]
        grafana_client = GrafanaClient(settings.grafana_url, settings.api_token)
        session_factory = get_session_factory()

        async with session_factory() as session:
            event_repo = SQLAlchemyEventRepository(session)
            entity_repo = SQLAlchemyEntityRepository(session)
            cursor_repo = SQLAlchemyCursorRepository(session)

            self._poller = PollerService(
                settings=settings,
                event_repo=event_repo,
                entity_repo=entity_repo,
                cursor_repo=cursor_repo,
                state=self._state,
                broadcaster=self._broadcaster,
                grafana_client=grafana_client,
            )
            await self._poller.start()
            logger.info("poller_manager_started")

    async def _stop(self) -> None:
        if self._poller:
            await self._poller.stop()
            logger.info("poller_manager_stopped")
            self._poller = None

    async def shutdown(self) -> None:
        await self._stop()


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

    poller_manager = PollerManager(settings=settings, state=state, broadcaster=broadcaster)
    app.state.poller_manager = poller_manager

    session_factory = get_session_factory()
    async with session_factory() as session:
        settings_repo = SQLAlchemySettingsRepository(session)
        app_settings = await load_effective(settings_repo)

    await poller_manager.apply(app_settings)

    # Backward-compat: expose .poller for status route
    app.state.poller = poller_manager.poller

    yield

    await poller_manager.shutdown()


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
