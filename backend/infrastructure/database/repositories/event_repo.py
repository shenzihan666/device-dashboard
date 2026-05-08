"""SQLAlchemy implementation of EventRepository and CursorRepository."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.events import Event
from backend.infrastructure.database.models import CursorModel, EventModel


class SQLAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, event: Event) -> int | None:
        payload_str = json.dumps(event.payload, ensure_ascii=False) if event.payload else None
        stmt = sqlite_insert(EventModel).values(
            ts_ns=event.ts_ns,
            kind=event.kind,
            host=event.host,
            device_serial=event.device_serial,
            ai_url=event.ai_url,
            prev_ai_url=event.prev_ai_url,
            status=event.status,
            latency_ms=event.latency_ms,
            request_id=event.request_id,
            session_id=event.session_id,
            raw_line=event.raw_line,
            payload_json=payload_str,
        )
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["ts_ns", "kind", "host", "device_serial", "ai_url"]
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        if result.rowcount > 0:
            return result.inserted_primary_key[0] if result.inserted_primary_key else 1
        return None

    async def insert_batch(self, events: list[Event]) -> int:
        inserted = 0
        for ev in events:
            if await self.insert(ev) is not None:
                inserted += 1
        return inserted

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
    ) -> list[dict[str, Any]]:
        stmt = select(EventModel)

        if from_ns is not None:
            stmt = stmt.where(EventModel.ts_ns >= from_ns)
        if to_ns is not None:
            stmt = stmt.where(EventModel.ts_ns <= to_ns)
        if kinds:
            stmt = stmt.where(EventModel.kind.in_(kinds))
        if host:
            stmt = stmt.where(EventModel.host == host)
        if serial:
            stmt = stmt.where(EventModel.device_serial == serial)

        if order.upper() == "ASC":
            stmt = stmt.order_by(EventModel.ts_ns.asc())
        else:
            stmt = stmt.order_by(EventModel.ts_ns.desc())

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._model_to_dict(r) for r in rows]

    async def query_up_to(self, ts_ns: int, limit: int = 50000) -> list[dict[str, Any]]:
        stmt = (
            select(EventModel)
            .where(EventModel.ts_ns <= ts_ns)
            .order_by(EventModel.ts_ns.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._model_to_dict(r) for r in rows]

    async def get_time_range(self) -> tuple[int | None, int | None]:
        stmt = select(func.min(EventModel.ts_ns), func.max(EventModel.ts_ns))
        result = await self._session.execute(stmt)
        row = result.one()
        return (row[0], row[1])

    async def get_density(
        self, from_ns: int, to_ns: int, buckets: int = 100
    ) -> list[dict[str, Any]]:
        bucket_size = max(1, (to_ns - from_ns) // buckets)
        stmt = text(
            "SELECT (ts_ns / :bucket_size) * :bucket_size AS bucket_ns, COUNT(*) AS cnt "
            "FROM events WHERE ts_ns >= :from_ns AND ts_ns <= :to_ns "
            "GROUP BY bucket_ns ORDER BY bucket_ns"
        )
        result = await self._session.execute(
            stmt, {"bucket_size": bucket_size, "from_ns": from_ns, "to_ns": to_ns}
        )
        return [{"ts_ns": row[0], "count": row[1]} for row in result.fetchall()]

    @staticmethod
    def _model_to_dict(model: EventModel) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": model.id,
            "ts_ns": model.ts_ns,
            "kind": model.kind,
            "host": model.host,
            "device_serial": model.device_serial,
            "ai_url": model.ai_url,
            "prev_ai_url": model.prev_ai_url,
            "status": model.status,
            "latency_ms": model.latency_ms,
            "request_id": model.request_id,
            "session_id": model.session_id,
            "raw_line": model.raw_line,
            "payload_json": None,
        }
        if model.payload_json:
            try:
                d["payload_json"] = json.loads(model.payload_json)
            except (json.JSONDecodeError, TypeError):
                d["payload_json"] = model.payload_json
        return d


class SQLAlchemyCursorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, ref: str) -> int | None:
        stmt = select(CursorModel.ts_ns).where(CursorModel.ref == ref)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def set(self, ref: str, ts_ns: int) -> None:
        stmt = sqlite_insert(CursorModel).values(ref=ref, ts_ns=ts_ns)
        stmt = stmt.on_conflict_do_update(index_elements=["ref"], set_={"ts_ns": ts_ns})
        await self._session.execute(stmt)
        await self._session.commit()
