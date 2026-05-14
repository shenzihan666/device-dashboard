"""Shared test fixtures: in-memory DB, TestClient, DI overrides."""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.api.dependencies import get_db_session, get_state_projector
from backend.config import Settings, get_settings
from backend.core.services.state_projector import StateProjector
from backend.infrastructure.database.models import Base
from backend.main import create_app

_NANO = 1_000_000_000


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        log_level="DEBUG",
        log_format="console",
    )


@pytest_asyncio.fixture
async def async_engine(test_settings: Settings):
    engine = create_async_engine(
        test_settings.db_url,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def state_projector() -> StateProjector:
    return StateProjector(offline_grace_ns=90 * _NANO)


@pytest_asyncio.fixture
async def client(
    async_engine, db_session: AsyncSession, state_projector: StateProjector, test_settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    # Override dependencies for testing
    async def _override_session():
        yield db_session

    def _override_state(request=None):
        return state_projector

    def _override_settings():
        return test_settings

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_state_projector] = _override_state
    app.dependency_overrides[get_settings] = _override_settings

    # Set app.state attributes the routes/websocket handlers expect
    app.state.projector = state_projector
    from backend.infrastructure.websocket.broadcaster import Broadcaster

    app.state.broadcaster = Broadcaster()
    app.state.poller = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
