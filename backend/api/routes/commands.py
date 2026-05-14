"""REST API for sending remote commands to WeCom clients via WebSocket."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/commands", tags=["commands"])


class CommandResult(BaseModel):
    success: bool
    message: str


async def _send_and_respond(
    request: Request, instance_id: str, action: str, serial: str
) -> CommandResult:
    registry = getattr(request.app.state, "heartbeat_registry", None)
    if registry is None:
        raise HTTPException(status_code=503, detail="Heartbeat registry not available")

    command = {"action": action, "serial": serial}

    try:
        result = await registry.send_command(instance_id, command, timeout=60.0)
        return CommandResult(
            success=result.get("success", False),
            message=result.get("message", ""),
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Command timed out")


@router.post("/wecom/{instance_id}/device/{serial}/start", response_model=CommandResult)
async def device_start(request: Request, instance_id: str, serial: str):
    return await _send_and_respond(request, instance_id, "device_start", serial)


@router.post("/wecom/{instance_id}/device/{serial}/stop", response_model=CommandResult)
async def device_stop(request: Request, instance_id: str, serial: str):
    return await _send_and_respond(request, instance_id, "device_stop", serial)


@router.post("/wecom/{instance_id}/device/{serial}/pause", response_model=CommandResult)
async def device_pause(request: Request, instance_id: str, serial: str):
    return await _send_and_respond(request, instance_id, "device_pause", serial)


@router.post("/wecom/{instance_id}/device/{serial}/resume", response_model=CommandResult)
async def device_resume(request: Request, instance_id: str, serial: str):
    return await _send_and_respond(request, instance_id, "device_resume", serial)


@router.post("/wecom/{instance_id}/device/{serial}/restart", response_model=CommandResult)
async def device_restart(request: Request, instance_id: str, serial: str):
    return await _send_and_respond(request, instance_id, "device_restart", serial)


@router.post("/wecom/{instance_id}/wecom-app/{serial}/restart", response_model=CommandResult)
async def wecom_app_restart(request: Request, instance_id: str, serial: str):
    return await _send_and_respond(request, instance_id, "app_restart", serial)
