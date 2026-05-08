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
from backend.infrastructure.database.session import get_session_factory, init_engine
from backend.infrastructure.external.grafana_client import GrafanaClient
from backend.infrastructure.websocket.broadcaster import Broadcaster
from backend.logging_config import configure_logging

logger = structlog.get_logger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
_NANO = 1_000_000_000


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)

    engine = init_engine(settings)

    # Create tables if they don't exist (for dev; production uses Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure data directory exists
    if settings.db_url.startswith("sqlite"):
        db_path = settings.db_url.split("///")[-1] if "///" in settings.db_url else None
        if db_path:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Initialize shared services
    state = StateProjector(offline_grace_ns=settings.offline_grace_s * _NANO)
    broadcaster = Broadcaster()

    app.state.projector = state
    app.state.broadcaster = broadcaster

    # Start poller if API token is configured
    poller: PollerService | None = None
    if settings.api_token:
        grafana_client = GrafanaClient(settings.grafana_url, settings.api_token)
        session_factory = get_session_factory()

        async with session_factory() as session:
            event_repo = SQLAlchemyEventRepository(session)
            entity_repo = SQLAlchemyEntityRepository(session)
            cursor_repo = SQLAlchemyCursorRepository(session)

            poller = PollerService(
                settings=settings,
                event_repo=event_repo,
                entity_repo=entity_repo,
                cursor_repo=cursor_repo,
                state=state,
                broadcaster=broadcaster,
                grafana_client=grafana_client,
            )
            app.state.poller = poller
            await poller.start()
    else:
        logger.warning("api_token_not_set", detail="Poller disabled, running in offline/demo mode")
        app.state.poller = None

    yield

    # Shutdown
    if poller:
        await poller.stop()
    if hasattr(app.state, "_grafana_client"):
        await app.state._grafana_client.close()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="WeCom AI Connection Dashboard",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Middleware (order matters: last added = first executed)
    register_middleware(app, settings)

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    for router in all_routers:
        app.include_router(router)

    # Static file serving for SPA
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
