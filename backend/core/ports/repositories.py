"""Repository protocols defining the contract between domain and infrastructure."""

from __future__ import annotations

from typing import Any, Protocol

from backend.core.domain.events import Event


class EventRepository(Protocol):
    async def insert(self, event: Event) -> int | None:
        """Insert an event. Returns row id or None if duplicate."""
        ...

    async def insert_batch(self, events: list[Event]) -> int:
        """Bulk insert events. Returns count of newly inserted rows."""
        ...

    async def query(
        self,
        *,
        from_ns: int | None = None,
        to_ns: int | None = None,
        kinds: list[str] | None = None,
        host: str | None = None,
        serial: str | None = None,
        limit: int = 500,
        order: str = "DESC",
    ) -> list[dict[str, Any]]: ...

    async def query_up_to(self, ts_ns: int, limit: int = 50000) -> list[dict[str, Any]]:
        """All events up to a timestamp, ascending. Used for state reconstruction."""
        ...

    async def get_time_range(self) -> tuple[int | None, int | None]:
        """Return (min_ts_ns, max_ts_ns) across all events."""
        ...

    async def get_density(
        self, from_ns: int, to_ns: int, buckets: int = 100
    ) -> list[dict[str, Any]]: ...

    async def get_latest_hb_state(self, ts_ns: int) -> list[dict[str, Any]]:
        """Get heartbeat instances connected at the given timestamp."""
        ...


class EntityRepository(Protocol):
    async def upsert(
        self, kind: str, entity_id: str, ts_ns: int, meta: dict | None = None
    ) -> None: ...

    async def get_all(self, kind: str | None = None) -> list[dict[str, Any]]: ...


class LayoutRepository(Protocol):
    async def get_positions(self) -> list[dict[str, Any]]: ...

    async def upsert_positions(self, items: list[dict[str, Any]], now_ns: int) -> None: ...

    async def clear(self) -> None: ...


class CursorRepository(Protocol):
    async def get(self, ref: str) -> int | None: ...

    async def set(self, ref: str, ts_ns: int) -> None: ...
