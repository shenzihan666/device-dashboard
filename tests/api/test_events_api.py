"""API contract tests for event endpoints."""

import pytest
from httpx import AsyncClient

from backend.core.domain.events import AI_SERVER_OBSERVED, Event
from backend.infrastructure.database.repositories.event_repo import SQLAlchemyEventRepository


@pytest.mark.asyncio
async def test_get_events_empty(client: AsyncClient):
    resp = await client.get("/api/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"] == []


@pytest.mark.asyncio
async def test_get_events_with_data(client: AsyncClient, db_session):
    repo = SQLAlchemyEventRepository(db_session)
    await repo.insert(
        Event(
            ts_ns=1000000000,
            kind=AI_SERVER_OBSERVED,
            host="DESKTOP-TEST",
            device_serial="ABC123",
            ai_url="http://10.0.0.1:8000/chat",
        )
    )

    resp = await client.get("/api/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["kind"] == AI_SERVER_OBSERVED


@pytest.mark.asyncio
async def test_get_events_limit(client: AsyncClient, db_session):
    repo = SQLAlchemyEventRepository(db_session)
    for i in range(5):
        await repo.insert(
            Event(
                ts_ns=1000000000 + i,
                kind=AI_SERVER_OBSERVED,
                host="DESKTOP-TEST",
                device_serial=f"DEV{i:03d}",
                ai_url="http://10.0.0.1:8000/chat",
            )
        )

    resp = await client.get("/api/events?limit=3")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 3


@pytest.mark.asyncio
async def test_get_events_invalid_limit(client: AsyncClient):
    resp = await client.get("/api/events?limit=0")
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_get_time_range_empty(client: AsyncClient):
    resp = await client.get("/api/time_range")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["min_ns"] is None
    assert body["data"]["max_ns"] is None


@pytest.mark.asyncio
async def test_get_time_range_with_data(client: AsyncClient, db_session):
    repo = SQLAlchemyEventRepository(db_session)
    await repo.insert(Event(ts_ns=100, kind="test", host="h1", device_serial="d1", ai_url="u1"))
    await repo.insert(Event(ts_ns=500, kind="test2", host="h2", device_serial="d2", ai_url="u2"))

    resp = await client.get("/api/time_range")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["min_ns"] == 100
    assert body["data"]["max_ns"] == 500


@pytest.mark.asyncio
async def test_get_density(client: AsyncClient, db_session):
    repo = SQLAlchemyEventRepository(db_session)
    await repo.insert(Event(ts_ns=100, kind="test", host="h1", device_serial="d1", ai_url="u1"))

    resp = await client.get("/api/density?from=0&to=1000&buckets=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
