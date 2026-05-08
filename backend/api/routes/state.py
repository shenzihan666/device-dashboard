"""State snapshot API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.api.dependencies import EventRepoDep, StateProjectorDep
from backend.api.schemas.common import APIResponse
from backend.core.services.state_projector import StateProjector

router = APIRouter(prefix="/api", tags=["state"])

_NANO = 1_000_000_000


@router.get("/state", response_model=APIResponse[dict[str, Any]])
async def get_state(
    state: StateProjectorDep,
    event_repo: EventRepoDep,
    at: str | None = None,
) -> APIResponse[dict[str, Any]]:
    """Return the current graph state (or reconstructed at a past timestamp)."""
    if at is None or at == "now":
        return APIResponse(data=state.get_snapshot())

    try:
        at_ns = int(float(at) * _NANO) if "." in at else int(at)
    except ValueError:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
        at_ns = int(dt.replace(tzinfo=timezone.utc).timestamp() * _NANO)

    replay = StateProjector(offline_grace_ns=state.offline_grace_ns)
    events = await event_repo.query_up_to(at_ns)
    replay.rebuild_from_events(events)
    return APIResponse(data=replay.get_snapshot())
