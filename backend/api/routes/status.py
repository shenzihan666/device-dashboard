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
    broadcaster = getattr(request.app.state, "broadcaster", None)

    registry = getattr(request.app.state, "heartbeat_registry", None)

    data = {
        "ws_clients": broadcaster.client_count if broadcaster else 0,
        "heartbeat_clients": registry.connected_count if registry else 0,
        "time_range": {"min_ns": mn, "max_ns": mx},
        "config": {
            "offline_grace_s": settings.offline_grace_s,
            "heartbeat_grace_s": settings.heartbeat_grace_s,
        },
    }
    return APIResponse(data=data)
