"""System status API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from backend.api.dependencies import EventRepoDep, SettingsDep
from backend.api.schemas.common import APIResponse

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=APIResponse[dict[str, Any]])
async def get_status(
    request: Request,
    event_repo: EventRepoDep,
    settings: SettingsDep,
) -> APIResponse[dict[str, Any]]:
    mn, mx = await event_repo.get_time_range()
    poller = getattr(request.app.state, "poller", None)
    broadcaster = getattr(request.app.state, "broadcaster", None)

    data = {
        "poller_running": poller.is_running if poller else False,
        "ws_clients": broadcaster.client_count if broadcaster else 0,
        "time_range": {"min_ns": mn, "max_ns": mx},
        "config": {
            "poll_interval_s": settings.poll_interval_s,
            "backfill_hours": settings.backfill_hours,
            "offline_grace_s": settings.offline_grace_s,
        },
    }
    return APIResponse(data=data)
