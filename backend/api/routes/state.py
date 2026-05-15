"""State snapshot API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from backend.api.dependencies import AppSettingsRepoDep, EventRepoDep, StateProjectorDep
from backend.api.schemas.common import APIResponse
from backend.core.services.app_settings import load_effective
from backend.core.services.heartbeat_registry import _match_brain_url
from backend.core.services.state_projector import StateProjector

router = APIRouter(prefix="/api", tags=["state"])

_NANO = 1_000_000_000


@router.get("/state", response_model=APIResponse[dict[str, Any]])
async def get_state(
    state: StateProjectorDep,
    event_repo: EventRepoDep,
    settings_repo: AppSettingsRepoDep,
    request: Request,
    at: str | None = None,
) -> APIResponse[dict[str, Any]]:
    """Return the current graph state (or reconstructed at a past timestamp)."""
    app_settings = await load_effective(settings_repo)

    if at is None or at == "now":
        snapshot = state.get_snapshot()

        # Merge heartbeat data if point-to-point is enabled
        registry = getattr(request.app.state, "heartbeat_registry", None)
        if registry and app_settings.point_to_point_enabled:
            hb = registry.get_snapshot()
            snapshot["brain_servers"] = hb["brain_servers"]
            snapshot["wecom_clients"] = hb["wecom_clients"]
            snapshot["heartbeat_edges"] = hb["heartbeat_edges"]

        # Only show point-to-point data now
        if not app_settings.point_to_point_enabled:
            snapshot["brain_servers"] = []
            snapshot["wecom_clients"] = []
            snapshot["heartbeat_edges"] = []

        snapshot["data_sources"] = {
            "point_to_point_enabled": app_settings.point_to_point_enabled,
        }
        return APIResponse(data=snapshot)

    try:
        at_ns = int(float(at) * _NANO) if "." in at else int(at)
    except ValueError:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
        at_ns = int(dt.replace(tzinfo=timezone.utc).timestamp() * _NANO)

    replay = StateProjector(offline_grace_ns=state.offline_grace_ns)
    events = await event_repo.query_up_to(at_ns)
    replay.rebuild_from_events(events)
    snapshot = replay.get_snapshot()

    # Reconstruct p2p connection state from targeted query
    if app_settings.point_to_point_enabled:
        hb_rows = await event_repo.get_latest_hb_state(at_ns)
        brain_servers: list[dict] = []
        wecom_clients: list[dict] = []

        for row in hb_rows:
            payload = row.get("payload_json", {}) or {}
            instance_type = payload.get("instance_type", "")
            instance_id = row["instance_id"]

            if instance_type == "brain_server":
                brain_servers.append(
                    {
                        "instance_id": instance_id,
                        "name": payload.get("name", instance_id),
                        "version": payload.get("version", ""),
                        "worker_count": payload.get("worker_count", 0),
                        "total_handled": 0,
                        "avg_inflight": 0.0,
                        "health_status": "unknown",
                        "memory_mb": None,
                        "cpu_pct": None,
                        "last_heartbeat_ns": row["ts_ns"],
                        "online": True,
                    }
                )
            elif instance_type == "wecom_client":
                wecom_clients.append(
                    {
                        "instance_id": instance_id,
                        "name": payload.get("name", instance_id),
                        "version": payload.get("version", ""),
                        "brain_url": payload.get("brain_url", ""),
                        "device_count": 0,
                        "devices": [],
                        "health_status": "unknown",
                        "ai_reachable": False,
                        "ai_response_ms": None,
                        "last_heartbeat_ns": row["ts_ns"],
                        "online": True,
                    }
                )

        # Build heartbeat edges
        heartbeat_edges: list[dict] = []
        for wc in wecom_clients:
            brain_url = wc.get("brain_url", "")
            if not brain_url:
                continue
            for bs in brain_servers:
                if _match_brain_url(brain_url, bs["instance_id"], bs.get("name", "")):
                    heartbeat_edges.append(
                        {
                            "from": f"wecom_client::{wc['instance_id']}",
                            "to": f"brain_server::{bs['instance_id']}",
                            "type": "heartbeat",
                            "status": "online",
                        }
                    )
                    break

        snapshot["brain_servers"] = brain_servers
        snapshot["wecom_clients"] = wecom_clients
        snapshot["heartbeat_edges"] = heartbeat_edges

    snapshot["data_sources"] = {
        "point_to_point_enabled": app_settings.point_to_point_enabled,
    }
    return APIResponse(data=snapshot)
