"""REST API routes for the connection dashboard."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Query, Request

from backend.state import StateProjector
from backend.store import EventStore

_NANO = 1_000_000_000

router = APIRouter(prefix="/api")

_store: EventStore | None = None
_state: StateProjector | None = None


def init_api(store: EventStore, state: StateProjector) -> None:
    global _store, _state
    _store = store
    _state = state


@router.get("/state")
async def get_state(at: str | None = None) -> dict[str, Any]:
    """Return the current graph state (or reconstructed at a past timestamp)."""
    assert _store is not None and _state is not None

    if at is None or at == "now":
        return _state.get_snapshot()

    # Reconstruct state at a specific timestamp
    try:
        at_ns = int(float(at) * _NANO) if "." in at else int(at)
    except ValueError:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
        at_ns = int(dt.replace(tzinfo=timezone.utc).timestamp() * _NANO)

    replay = StateProjector(offline_grace_ns=_state.offline_grace_ns)
    events = _store.query_events_up_to(at_ns)
    replay.rebuild_from_events(events)
    return replay.get_snapshot()


@router.get("/events")
async def get_events(
    from_ns: int | None = Query(None, alias="from"),
    to_ns: int | None = Query(None, alias="to"),
    kinds: str | None = None,
    host: str | None = None,
    serial: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    assert _store is not None
    kind_list = kinds.split(",") if kinds else None
    return _store.query_events(
        from_ns=from_ns,
        to_ns=to_ns,
        kinds=kind_list,
        host=host,
        serial=serial,
        limit=limit,
    )


@router.get("/entities")
async def get_entities(kind: str | None = None) -> list[dict[str, Any]]:
    assert _store is not None
    return _store.get_entities(kind=kind)


@router.get("/density")
async def get_density(
    from_ns: int | None = Query(None, alias="from"),
    to_ns: int | None = Query(None, alias="to"),
    buckets: int = 100,
) -> list[dict[str, Any]]:
    assert _store is not None
    if from_ns is None or to_ns is None:
        mn, mx = _store.get_time_range()
        from_ns = from_ns or mn or 0
        to_ns = to_ns or mx or int(time.time() * _NANO)
    return _store.get_event_density(from_ns, to_ns, buckets)


@router.get("/time_range")
async def get_time_range() -> dict[str, Any]:
    assert _store is not None
    mn, mx = _store.get_time_range()
    return {"min_ns": mn, "max_ns": mx}


# ── Layout (node positions) ───────────────────────────────────────────


@router.get("/layout")
async def get_layout() -> dict[str, Any]:
    """Return all saved node positions."""
    assert _store is not None
    positions = _store.get_layout()
    return {"positions": positions}


@router.put("/layout")
async def save_layout(request: Request) -> dict[str, Any]:
    """Upsert one or more node positions."""
    assert _store is not None
    body = await request.json()
    items = body if isinstance(body, list) else [body]
    now_ns = int(time.time() * _NANO)
    _store.upsert_positions(items, now_ns)
    return {"saved": len(items)}


@router.delete("/layout")
async def reset_layout() -> dict[str, Any]:
    """Clear all saved node positions (reset to auto-layout)."""
    assert _store is not None
    _store.clear_layout()
    return {"cleared": True}
