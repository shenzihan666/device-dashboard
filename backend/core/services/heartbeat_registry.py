"""Heartbeat registry: tracks connected brain servers and WeCom clients."""

from __future__ import annotations

import asyncio
import socket
import time
from typing import Any
from urllib.parse import urlparse

import structlog
from fastapi import WebSocket

from backend.infrastructure.websocket.broadcaster import Broadcaster

logger = structlog.get_logger(__name__)

_NANO = 1_000_000_000
_LOCALHOST_ALIASES = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _is_local(host: str) -> bool:
    return host.lower() in _LOCALHOST_ALIASES


def _match_brain_url(brain_url: str, bs_instance_id: str, bs_name: str) -> bool:
    """Check whether *brain_url* points to the given brain server.

    Uses URL host+port comparison with localhost normalisation instead of
    brittle substring matching.
    """
    try:
        parsed = urlparse(brain_url)
        url_host = parsed.hostname or ""
        url_port = parsed.port
    except Exception:
        return False

    if not url_host or url_port is None:
        return False

    # instance_id is typically "hostname:port"
    iid_host, iid_port = "", None
    if ":" in bs_instance_id:
        parts = bs_instance_id.rsplit(":", 1)
        iid_host = parts[0]
        try:
            iid_port = int(parts[1])
        except ValueError:
            pass
    else:
        iid_host = bs_instance_id

    # name is typically just the hostname
    bs_hostname = bs_name or iid_host

    # Ports must match
    if url_port != iid_port:
        return False

    # Exact host match
    if url_host == iid_host or url_host == bs_hostname:
        return True

    # Localhost normalisation: if the URL uses localhost/127.0.0.1 and the
    # brain server reports the same machine's hostname, treat them as matching.
    if _is_local(url_host):
        try:
            local_hostnames = {socket.gethostname(), socket.getfqdn()}
            if iid_host in local_hostnames or bs_hostname in local_hostnames:
                return True
        except Exception:
            pass

    return False


class HeartbeatRegistry:
    """In-memory registry of heartbeat-connected instances."""

    def __init__(
        self,
        offline_grace_ns: int,
        broadcaster: Broadcaster,
    ) -> None:
        self._offline_grace_ns = offline_grace_ns
        self._broadcaster = broadcaster

        self._instances: dict[str, dict] = {}
        self._instance_types: dict[str, str] = {}
        self._last_seen: dict[str, int] = {}
        self._online: dict[str, bool] = {}
        self._websockets: dict[str, WebSocket] = {}

        self._checker_task: asyncio.Task | None = None

    async def start_offline_checker(self, interval_s: int) -> None:
        """Start background task that checks for offline instances."""
        self._checker_task = asyncio.create_task(self._offline_check_loop(interval_s))

    async def stop(self) -> None:
        if self._checker_task:
            self._checker_task.cancel()
            try:
                await self._checker_task
            except asyncio.CancelledError:
                pass
            self._checker_task = None

    def clear(self) -> None:
        """Drop all tracked instances from memory."""
        self._instances.clear()
        self._instance_types.clear()
        self._last_seen.clear()
        self._online.clear()
        self._websockets.clear()

    async def on_connect(
        self, instance_id: str, instance_type: str, ws: WebSocket
    ) -> bool:
        """Register a new connection.  Returns True if accepted, False if rejected.

        If another WebSocket is already registered for the same instance_id,
        only replace it when the existing connection is stale (no heartbeat
        within the grace period).  This prevents a misbehaving duplicate from
        evicting a healthy persistent connection.
        """
        old_ws = self._websockets.get(instance_id)
        if old_ws is not None and old_ws is not ws:
            now_ns = int(time.time() * _NANO)
            last_ns = self._last_seen.get(instance_id, 0)
            age_ns = now_ns - last_ns

            if age_ns < self._offline_grace_ns:
                logger.warning(
                    "heartbeat_duplicate_rejected",
                    instance_id=instance_id,
                    age_s=age_ns / _NANO,
                )
                return False

            # Existing connection is stale — replace it
            logger.info("heartbeat_replacing_stale_connection", instance_id=instance_id)
            try:
                await old_ws.close()
            except Exception:
                pass

        self._websockets[instance_id] = ws
        self._instance_types[instance_id] = instance_type
        self._online[instance_id] = True
        logger.info(
            "heartbeat_connected",
            instance_id=instance_id,
            instance_type=instance_type,
        )
        return True

    async def on_heartbeat(self, instance_id: str, data: dict) -> None:
        """Process an incoming heartbeat message."""
        now_ns = int(time.time() * _NANO)
        self._instances[instance_id] = data
        self._last_seen[instance_id] = now_ns
        was_online = self._online.get(instance_id, False)
        self._online[instance_id] = True

        if not was_online:
            logger.info("heartbeat_instance_online", instance_id=instance_id)

        await self._broadcaster.broadcast(
            {"type": "heartbeat_update", "instance_id": instance_id}
        )

    async def on_disconnect(self, instance_id: str, ws: WebSocket | None = None) -> None:
        """Handle client disconnection.

        If *ws* is provided, only remove the entry when the registered
        WebSocket matches (prevents a rejected duplicate from clearing the
        legitimate connection's registration).
        """
        if ws is not None:
            registered = self._websockets.get(instance_id)
            if registered is not ws:
                return
        self._websockets.pop(instance_id, None)
        logger.info("heartbeat_disconnected", instance_id=instance_id)

    def get_snapshot(self) -> dict[str, Any]:
        """Return current state as a dict for merging into /api/state."""
        brain_servers: list[dict] = []
        wecom_clients: list[dict] = []
        heartbeat_edges: list[dict] = []

        for iid, data in self._instances.items():
            itype = self._instance_types.get(iid, "")
            online = self._online.get(iid, False)

            if itype == "brain_server":
                health = data.get("health", {})
                brain_servers.append(
                    {
                        "instance_id": iid,
                        "name": data.get("name", iid),
                        "version": data.get("version", ""),
                        "worker_count": data.get("worker_count", 0),
                        "total_handled": data.get("total_handled", 0),
                        "avg_inflight": data.get("avg_inflight", 0.0),
                        "health_status": health.get("status", "unknown"),
                        "memory_mb": health.get("memory_mb"),
                        "cpu_pct": health.get("cpu_pct"),
                        "last_heartbeat_ns": self._last_seen.get(iid, 0),
                        "online": online,
                    }
                )
            elif itype == "wecom_client":
                health = data.get("health", {})
                devices = data.get("devices", [])
                wecom_clients.append(
                    {
                        "instance_id": iid,
                        "name": data.get("name", iid),
                        "version": data.get("version", ""),
                        "brain_url": data.get("brain_url", ""),
                        "device_count": data.get("device_count", 0),
                        "devices": devices,
                        "health_status": health.get("status", "unknown"),
                        "ai_reachable": health.get("ai_reachable", False),
                        "ai_response_ms": health.get("ai_response_ms"),
                        "last_heartbeat_ns": self._last_seen.get(iid, 0),
                        "online": online,
                    }
                )

        # Build edges: wecom_client -> brain_server
        for wc in wecom_clients:
            brain_url = wc.get("brain_url", "")
            if not brain_url:
                continue
            for bs in brain_servers:
                if _match_brain_url(
                    brain_url, bs["instance_id"], bs.get("name", "")
                ):
                    heartbeat_edges.append(
                        {
                            "from": f"wecom_client::{wc['instance_id']}",
                            "to": f"brain_server::{bs['instance_id']}",
                            "type": "heartbeat",
                            "status": "offline"
                            if not wc["online"] or not bs["online"]
                            else "online",
                        }
                    )
                    break

        return {
            "brain_servers": brain_servers,
            "wecom_clients": wecom_clients,
            "heartbeat_edges": heartbeat_edges,
        }

    @property
    def connected_count(self) -> int:
        return sum(1 for v in self._online.values() if v)

    async def _offline_check_loop(self, interval_s: int) -> None:
        """Periodically check for instances that stopped sending heartbeats."""
        while True:
            await asyncio.sleep(interval_s)
            now_ns = int(time.time() * _NANO)
            newly_offline: list[str] = []

            for iid, last_ns in list(self._last_seen.items()):
                if self._online.get(iid) and (now_ns - last_ns) > self._offline_grace_ns:
                    self._online[iid] = False
                    newly_offline.append(iid)

            if newly_offline:
                logger.info(
                    "heartbeat_instances_offline",
                    count=len(newly_offline),
                    instance_ids=newly_offline,
                )
                await self._broadcaster.broadcast(
                    {"type": "heartbeat_update", "offline": newly_offline}
                )
