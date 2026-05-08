"""API contract tests for entity endpoints."""

import pytest
from httpx import AsyncClient

from backend.infrastructure.database.repositories.entity_repo import SQLAlchemyEntityRepository


@pytest.mark.asyncio
async def test_get_entities_empty(client: AsyncClient):
    resp = await client.get("/api/entities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"] == []


@pytest.mark.asyncio
async def test_get_entities_with_data(client: AsyncClient, db_session):
    repo = SQLAlchemyEntityRepository(db_session)
    await repo.upsert("device", "ABC123", 100_000_000_000)
    await repo.upsert("host", "DESKTOP-TEST", 100_000_000_000)

    resp = await client.get("/api/entities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_get_entities_filter_by_kind(client: AsyncClient, db_session):
    repo = SQLAlchemyEntityRepository(db_session)
    await repo.upsert("device", "ABC123", 100_000_000_000)
    await repo.upsert("host", "DESKTOP-TEST", 100_000_000_000)

    resp = await client.get("/api/entities?kind=device")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["kind"] == "device"
