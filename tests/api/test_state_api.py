"""API contract tests for state endpoint."""

import pytest
from httpx import AsyncClient

from backend.core.domain.events import AI_SERVER_OBSERVED, Event
from backend.core.services.state_projector import StateProjector


@pytest.mark.asyncio
async def test_get_state_empty(client: AsyncClient):
    resp = await client.get("/api/state")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["devices"] == []
    assert body["data"]["servers"] == []
    assert body["data"]["hosts"] == []
    assert body["data"]["edges"] == []


@pytest.mark.asyncio
async def test_get_state_with_data(client: AsyncClient, state_projector: StateProjector):
    event = Event(
        ts_ns=100_000_000_000,
        kind=AI_SERVER_OBSERVED,
        host="DESKTOP-TEST",
        device_serial="ABC123",
        ai_url="http://10.0.0.1:8000/chat",
    )
    state_projector.process(event)

    resp = await client.get("/api/state")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]["devices"]) == 1
    assert body["data"]["devices"][0]["serial"] == "ABC123"
    assert len(body["data"]["servers"]) == 1


@pytest.mark.asyncio
async def test_get_state_at_timestamp(client: AsyncClient, db_session):
    from backend.infrastructure.database.repositories.event_repo import SQLAlchemyEventRepository

    repo = SQLAlchemyEventRepository(db_session)
    await repo.insert(
        Event(
            ts_ns=100_000_000_000,
            kind=AI_SERVER_OBSERVED,
            host="DESKTOP-TEST",
            device_serial="ABC123",
            ai_url="http://10.0.0.1:8000/chat",
        )
    )

    resp = await client.get("/api/state?at=100000000000")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]["devices"]) == 1
