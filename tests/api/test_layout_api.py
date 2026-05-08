"""API contract tests for layout endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_layout_empty(client: AsyncClient):
    resp = await client.get("/api/layout")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["positions"] == []


@pytest.mark.asyncio
async def test_save_layout(client: AsyncClient):
    payload = {
        "positions": [
            {"node_id": "node1", "x": 100.0, "y": 200.0},
            {"node_id": "node2", "x": 300.0, "y": 400.0},
        ]
    }
    resp = await client.put("/api/layout", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["saved"] == 2


@pytest.mark.asyncio
async def test_save_and_retrieve_layout(client: AsyncClient):
    payload = {"positions": [{"node_id": "n1", "x": 10.0, "y": 20.0}]}
    await client.put("/api/layout", json=payload)

    resp = await client.get("/api/layout")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]["positions"]) == 1
    assert body["data"]["positions"][0]["node_id"] == "n1"
    assert body["data"]["positions"][0]["x"] == 10.0


@pytest.mark.asyncio
async def test_clear_layout(client: AsyncClient):
    payload = {"positions": [{"node_id": "n1", "x": 10.0, "y": 20.0}]}
    await client.put("/api/layout", json=payload)

    resp = await client.delete("/api/layout")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["cleared"] is True

    resp = await client.get("/api/layout")
    body = resp.json()
    assert body["data"]["positions"] == []


@pytest.mark.asyncio
async def test_save_layout_empty_positions_rejected(client: AsyncClient):
    resp = await client.put("/api/layout", json={"positions": []})
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_save_layout_invalid_body(client: AsyncClient):
    resp = await client.put("/api/layout", json={"bad": "data"})
    assert resp.status_code == 422
