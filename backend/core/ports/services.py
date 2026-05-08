"""Service port protocols for external integrations."""

from __future__ import annotations

from typing import Any, Protocol


class GrafanaClientPort(Protocol):
    """Port for querying Grafana/Loki."""

    def build_loki_query(
        self,
        uid: str,
        expr: str,
        *,
        ref_id: str = "A",
        max_lines: int = 1000,
        query_type: str = "range",
        direction: str = "backward",
    ) -> dict: ...

    async def query(self, queries: list[dict], from_: str = "now-24h", to: str = "now") -> dict: ...


class LangSmithClientPort(Protocol):
    """Port for LangSmith trace lookups."""

    async def lookup_trace(self, request_id: str) -> dict[str, Any] | None: ...


class BroadcasterPort(Protocol):
    """Port for real-time event broadcasting (WebSocket)."""

    async def broadcast(self, message: dict[str, Any]) -> None: ...

    @property
    def client_count(self) -> int: ...
