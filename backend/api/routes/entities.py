"""Entity API routes."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import EntityRepoDep
from backend.api.schemas.common import APIResponse
from backend.api.schemas.entities import EntityResponse

router = APIRouter(prefix="/api", tags=["entities"])


@router.get("/entities", response_model=APIResponse[list[EntityResponse]])
async def get_entities(
    entity_repo: EntityRepoDep,
    kind: str | None = None,
) -> APIResponse[list[EntityResponse]]:
    rows = await entity_repo.get_all(kind=kind)
    entities = [EntityResponse(**r) for r in rows]
    return APIResponse(data=entities)
