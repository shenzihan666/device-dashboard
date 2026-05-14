"""App-settings API routes (data-source toggles)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

from backend.api.dependencies import AppSettingsRepoDep
from backend.api.schemas.common import APIResponse
from backend.api.schemas.settings import AppSettingsResponse, AppSettingsUpdateRequest
from backend.core.services.app_settings import load_effective

router = APIRouter(prefix="/api", tags=["settings"])

_NANO = 1_000_000_000


@router.get("/settings", response_model=APIResponse[AppSettingsResponse])
async def get_settings(
    repo: AppSettingsRepoDep,
) -> APIResponse[AppSettingsResponse]:
    state = await load_effective(repo)
    return APIResponse(data=AppSettingsResponse(**state.to_dict()))


@router.put("/settings", response_model=APIResponse[AppSettingsResponse])
async def update_settings(
    body: AppSettingsUpdateRequest,
    repo: AppSettingsRepoDep,
    request: Request,
) -> APIResponse[AppSettingsResponse]:
    updates: dict[str, str] = {}
    if body.point_to_point_enabled is not None:
        updates["point_to_point_enabled"] = str(body.point_to_point_enabled).lower()

    if updates:
        now_ns = int(time.time() * _NANO)
        await repo.set_many(updates, now_ns)

    state = await load_effective(repo)

    heartbeat_manager = getattr(request.app.state, "heartbeat_manager", None)
    if heartbeat_manager is not None:
        await heartbeat_manager.apply(state)

    return APIResponse(data=AppSettingsResponse(**state.to_dict()))
