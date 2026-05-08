"""LangSmith trace lookup API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.api.dependencies import SettingsDep
from backend.api.exception_handlers import NotFoundError
from backend.api.schemas.common import APIResponse
from backend.infrastructure.external.langsmith_client import LangSmithClient

router = APIRouter(prefix="/api", tags=["langsmith"])


@router.get("/langsmith/trace", response_model=APIResponse[dict[str, Any]])
async def langsmith_trace(
    request_id: str,
    settings: SettingsDep,
) -> APIResponse[dict[str, Any]]:
    client = LangSmithClient(settings.langsmith_api_key)
    result = await client.lookup_trace(request_id)
    if result is None:
        raise NotFoundError("trace", request_id)
    return APIResponse(data=result)
