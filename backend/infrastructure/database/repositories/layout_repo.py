"""SQLAlchemy implementation of LayoutRepository."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.models import NodePositionModel


class SQLAlchemyLayoutRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_positions(self) -> list[dict[str, Any]]:
        stmt = select(NodePositionModel).order_by(NodePositionModel.node_id)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [{"node_id": r.node_id, "x": r.x, "y": r.y} for r in rows]

    async def upsert_positions(self, items: list[dict[str, Any]], now_ns: int) -> None:
        for item in items:
            stmt = sqlite_insert(NodePositionModel).values(
                node_id=item["node_id"],
                x=item["x"],
                y=item["y"],
                updated_ns=now_ns,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["node_id"],
                set_={
                    "x": item["x"],
                    "y": item["y"],
                    "updated_ns": now_ns,
                },
            )
            await self._session.execute(stmt)
        await self._session.commit()

    async def clear(self) -> None:
        await self._session.execute(delete(NodePositionModel))
        await self._session.commit()
