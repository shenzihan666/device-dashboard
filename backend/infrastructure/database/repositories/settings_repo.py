"""SQLAlchemy implementation of the app-settings key/value store."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.models import AppSettingModel


class SQLAlchemySettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> dict[str, str]:
        stmt = select(AppSettingModel)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return {r.key: r.value for r in rows}

    async def set_many(self, items: dict[str, str], now_ns: int) -> None:
        for key, value in items.items():
            stmt = sqlite_insert(AppSettingModel).values(
                key=key,
                value=value,
                updated_ns=now_ns,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"],
                set_={"value": value, "updated_ns": now_ns},
            )
            await self._session.execute(stmt)
        await self._session.commit()
