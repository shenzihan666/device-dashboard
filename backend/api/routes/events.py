"""Event query API routes."""

from __future__ import annotations

import time

from fastapi import APIRouter, Query

from backend.api.dependencies import EventRepoDep
from backend.api.schemas.common import APIResponse
from backend.api.schemas.events import DensityBucket, EventResponse, TimeRangeResponse

router = APIRouter(prefix="/api", tags=["events"])

_NANO = 1_000_000_000


@router.get("/events", response_model=APIResponse[list[EventResponse]])
async def get_events(
    event_repo: EventRepoDep,
    from_ns: int | None = Query(None, alias="from"),
    to_ns: int | None = Query(None, alias="to"),
    kinds: str | None = None,
    host: str | None = None,
    serial: str | None = None,
    limit: int = Query(default=500, ge=1, le=10000),
) -> APIResponse[list[EventResponse]]:
    kind_list = kinds.split(",") if kinds else None
    rows = await event_repo.query(
        from_ns=from_ns,
        to_ns=to_ns,
        kinds=kind_list,
        host=host,
        serial=serial,
        limit=limit,
    )
    events = [EventResponse(**r) for r in rows]
    return APIResponse(data=events)


@router.get("/density", response_model=APIResponse[list[DensityBucket]])
async def get_density(
    event_repo: EventRepoDep,
    from_ns: int | None = Query(None, alias="from"),
    to_ns: int | None = Query(None, alias="to"),
    buckets: int = Query(default=100, ge=1, le=1000),
) -> APIResponse[list[DensityBucket]]:
    if from_ns is None or to_ns is None:
        mn, mx = await event_repo.get_time_range()
        from_ns = from_ns or mn or 0
        to_ns = to_ns or mx or int(time.time() * _NANO)
    rows = await event_repo.get_density(from_ns, to_ns, buckets)
    data = [DensityBucket(**r) for r in rows]
    return APIResponse(data=data)


@router.get("/time_range", response_model=APIResponse[TimeRangeResponse])
async def get_time_range(
    event_repo: EventRepoDep,
) -> APIResponse[TimeRangeResponse]:
    mn, mx = await event_repo.get_time_range()
    return APIResponse(data=TimeRangeResponse(min_ns=mn, max_ns=mx))
