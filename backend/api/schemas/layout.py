"""Pydantic schemas for layout (node positions) endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NodePosition(BaseModel):
    node_id: str
    x: float
    y: float


class LayoutResponse(BaseModel):
    positions: list[NodePosition]


class LayoutSaveRequest(BaseModel):
    positions: list[NodePosition] = Field(..., min_length=1)


class LayoutSaveResponse(BaseModel):
    saved: int


class LayoutClearResponse(BaseModel):
    cleared: bool = True
