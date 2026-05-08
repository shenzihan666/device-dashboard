"""FastAPI dependency injection providers."""

from __future__ import annotations

from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings, get_settings
from backend.core.services.state_projector import StateProjector
from backend.infrastructure.database.repositories.entity_repo import (
    SQLAlchemyEntityRepository,
)
from backend.infrastructure.database.repositories.event_repo import (
    SQLAlchemyCursorRepository,
    SQLAlchemyEventRepository,
)
from backend.infrastructure.database.repositories.layout_repo import (
    SQLAlchemyLayoutRepository,
)
from backend.infrastructure.database.session import get_session_factory

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_event_repository(session: DBSessionDep) -> SQLAlchemyEventRepository:
    return SQLAlchemyEventRepository(session)


def get_entity_repository(session: DBSessionDep) -> SQLAlchemyEntityRepository:
    return SQLAlchemyEntityRepository(session)


def get_cursor_repository(session: DBSessionDep) -> SQLAlchemyCursorRepository:
    return SQLAlchemyCursorRepository(session)


def get_layout_repository(session: DBSessionDep) -> SQLAlchemyLayoutRepository:
    return SQLAlchemyLayoutRepository(session)


def get_state_projector(request: Request) -> StateProjector:
    return request.app.state.projector


EventRepoDep = Annotated[SQLAlchemyEventRepository, Depends(get_event_repository)]
EntityRepoDep = Annotated[SQLAlchemyEntityRepository, Depends(get_entity_repository)]
CursorRepoDep = Annotated[SQLAlchemyCursorRepository, Depends(get_cursor_repository)]
LayoutRepoDep = Annotated[SQLAlchemyLayoutRepository, Depends(get_layout_repository)]
StateProjectorDep = Annotated[StateProjector, Depends(get_state_projector)]
