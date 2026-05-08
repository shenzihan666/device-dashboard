"""WebSocket broadcaster: fans out new events to all connected clients."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class Broadcaster:
    """Simple pub-sub for WebSocket clients."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
        logger.info("ws_client_connected", total=len(self._clients))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)
        logger.info("ws_client_disconnected", remaining=len(self._clients))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client."""
        if not self._clients:
            return
        text = json.dumps(message, ensure_ascii=False, default=str)
        async with self._lock:
            stale: list[WebSocket] = []
            for ws in self._clients:
                try:
                    await ws.send_text(text)
                except Exception:
                    stale.append(ws)
            for ws in stale:
                self._clients.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._clients)
