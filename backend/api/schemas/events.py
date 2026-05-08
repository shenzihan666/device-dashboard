"""Pydantic schemas for event-related endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventResponse(BaseModel):
    id: int
    ts_ns: int
    kind: str
    host: str | None = None
    device_serial: str | None = None
    ai_url: str | None = None
    prev_ai_url: str | None = None
    status: str | None = None
    latency_ms: int | None = None
    request_id: str | None = None
    session_id: str | None = None
    raw_line: str | None = None
    payload_json: Any | None = None


class EventQueryParams(BaseModel):
    from_ns: int | None = Field(None, alias="from")
    to_ns: int | None = Field(None, alias="to")
    kinds: str | None = None
    host: str | None = None
    serial: str | None = None
    limit: int = Field(default=500, ge=1, le=10000)

    model_config = {"populate_by_name": True}


class TimeRangeResponse(BaseModel):
    min_ns: int | None = None
    max_ns: int | None = None


class DensityBucket(BaseModel):
    ts_ns: int
    count: int
