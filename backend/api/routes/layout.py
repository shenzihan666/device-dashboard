"""Layout (node positions) API routes."""

from __future__ import annotations

import time

from fastapi import APIRouter

from backend.api.dependencies import LayoutRepoDep
from backend.api.schemas.common import APIResponse
from backend.api.schemas.layout import (
    LayoutClearResponse,
    LayoutResponse,
    LayoutSaveRequest,
    LayoutSaveResponse,
    NodePosition,
)

router = APIRouter(prefix="/api", tags=["layout"])

_NANO = 1_000_000_000


@router.get("/layout", response_model=APIResponse[LayoutResponse])
async def get_layout(
    layout_repo: LayoutRepoDep,
) -> APIResponse[LayoutResponse]:
    positions = await layout_repo.get_positions()
    return APIResponse(data=LayoutResponse(positions=[NodePosition(**p) for p in positions]))


@router.put("/layout", response_model=APIResponse[LayoutSaveResponse])
async def save_layout(
    body: LayoutSaveRequest,
    layout_repo: LayoutRepoDep,
) -> APIResponse[LayoutSaveResponse]:
    now_ns = int(time.time() * _NANO)
    items = [p.model_dump() for p in body.positions]
    await layout_repo.upsert_positions(items, now_ns)
    return APIResponse(data=LayoutSaveResponse(saved=len(items)))


@router.delete("/layout", response_model=APIResponse[LayoutClearResponse])
async def reset_layout(
    layout_repo: LayoutRepoDep,
) -> APIResponse[LayoutClearResponse]:
    await layout_repo.clear()
    return APIResponse(data=LayoutClearResponse())
