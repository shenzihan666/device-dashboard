"""SQLAlchemy implementation of EntityRepository."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.models import EntityModel


class SQLAlchemyEntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, kind: str, entity_id: str, ts_ns: int, meta: dict | None = None) -> None:
        meta_str = json.dumps(meta, ensure_ascii=False) if meta else None
        stmt = sqlite_insert(EntityModel).values(
            kind=kind,
            id=entity_id,
            first_seen_ns=ts_ns,
            last_seen_ns=ts_ns,
            meta_json=meta_str,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["kind", "id"],
            set_={
                "last_seen_ns": func_max(EntityModel.last_seen_ns, ts_ns),
                "meta_json": meta_str if meta_str else EntityModel.meta_json,
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_all(self, kind: str | None = None) -> list[dict[str, Any]]:
        stmt = select(EntityModel)
        if kind:
            stmt = stmt.where(EntityModel.kind == kind)
        stmt = stmt.order_by(EntityModel.last_seen_ns.desc())
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._model_to_dict(r) for r in rows]

    @staticmethod
    def _model_to_dict(model: EntityModel) -> dict[str, Any]:
        d: dict[str, Any] = {
            "kind": model.kind,
            "id": model.id,
            "first_seen_ns": model.first_seen_ns,
            "last_seen_ns": model.last_seen_ns,
            "meta_json": None,
        }
        if model.meta_json:
            try:
                d["meta_json"] = json.loads(model.meta_json)
            except (json.JSONDecodeError, TypeError):
                d["meta_json"] = model.meta_json
        return d


def func_max(column, value):
    """SQLite-compatible MAX for ON CONFLICT SET."""
    from sqlalchemy import case, literal

    return case((column > literal(value), column), else_=literal(value))
