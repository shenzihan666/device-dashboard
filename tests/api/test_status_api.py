"""API contract tests for status endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_status(client: AsyncClient):
    resp = await client.get("/api/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "ws_clients" in body["data"]
    assert "heartbeat_clients" in body["data"]
    assert "time_range" in body["data"]
    assert "config" in body["data"]
    assert body["data"]["ws_clients"] == 0
    assert body["data"]["heartbeat_clients"] == 0
