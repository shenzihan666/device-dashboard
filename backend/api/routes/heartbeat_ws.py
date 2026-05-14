"""WebSocket endpoint for heartbeat clients (brain servers and WeCom clients)."""

from __future__ import annotations

import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["heartbeat"])


@router.websocket("/ws/heartbeat")
async def websocket_heartbeat(ws: WebSocket) -> None:
    await ws.accept()
    registry = ws.app.state.heartbeat_registry

    instance_id: str | None = None
    accepted = False
    try:
        # First message must be a heartbeat with instance_id and instance_type
        raw = await ws.receive_text()
        data = json.loads(raw)
        instance_id = data.get("instance_id")
        instance_type = data.get("instance_type")

        if not instance_id or instance_type not in ("wecom_client", "brain_server"):
            await ws.send_text(json.dumps({"type": "error", "message": "invalid first heartbeat"}))
            await ws.close()
            return

        accepted = await registry.on_connect(instance_id, instance_type, ws)
        if not accepted:
            await ws.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": "duplicate instance_id; existing connection is active",
                    }
                )
            )
            await ws.close()
            return

        await ws.send_text(json.dumps({"type": "welcome", "instance_id": instance_id}))

        # Process the first heartbeat
        await registry.on_heartbeat(instance_id, data)
        await ws.send_text(json.dumps({"type": "ack"}))

        # Continue receiving heartbeats and events
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("heartbeat_invalid_json", instance_id=instance_id)
                await ws.send_text(json.dumps({"type": "error", "message": "invalid json"}))
                continue
            msg_type = data.get("type", "heartbeat")
            if msg_type == "event":
                await registry.on_event(instance_id, data)
            elif msg_type == "heartbeat":
                await registry.on_heartbeat(instance_id, data)
            elif msg_type == "command_result":
                registry.on_command_result(data)
            # Silently ignore unknown types for forward compatibility
            await ws.send_text(json.dumps({"type": "ack"}))

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("heartbeat_ws_error", instance_id=instance_id, error=str(exc))
    finally:
        if instance_id and accepted:
            await registry.on_disconnect(instance_id, ws)
