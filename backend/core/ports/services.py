"""Service port protocols for external integrations."""

from __future__ import annotations

from typing import Any, Protocol


class BroadcasterPort(Protocol):
    """Port for real-time event broadcasting (WebSocket)."""

    async def broadcast(self, message: dict[str, Any]) -> None: ...

    @property
    def client_count(self) -> int: ...
