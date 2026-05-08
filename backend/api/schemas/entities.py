"""Pydantic schemas for entity-related endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EntityResponse(BaseModel):
    kind: str
    id: str
    first_seen_ns: int
    last_seen_ns: int
    meta_json: Any | None = None
