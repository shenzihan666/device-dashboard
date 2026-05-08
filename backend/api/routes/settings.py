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
    if body.grafana_enabled is not None:
        updates["grafana_enabled"] = str(body.grafana_enabled).lower()
    if body.langsmith_enabled is not None:
        updates["langsmith_enabled"] = str(body.langsmith_enabled).lower()

    if updates:
        now_ns = int(time.time() * _NANO)
        await repo.set_many(updates, now_ns)

    state = await load_effective(repo)

    poller_manager = getattr(request.app.state, "poller_manager", None)
    if poller_manager is not None:
        await poller_manager.apply(state)
        request.app.state.poller = poller_manager.poller

    return APIResponse(data=AppSettingsResponse(**state.to_dict()))
