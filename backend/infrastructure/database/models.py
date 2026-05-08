"""SQLAlchemy ORM models mapping to the connection dashboard schema."""

from __future__ import annotations

from sqlalchemy import BigInteger, Float, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts_ns: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    host: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_serial: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    prev_ai_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("events_ts", "ts_ns"),
        Index("events_kind_ts", "kind", "ts_ns"),
        Index("events_serial_ts", "device_serial", "ts_ns"),
        UniqueConstraint("ts_ns", "kind", "host", "device_serial", "ai_url", name="events_dedupe"),
    )


class EntityModel(Base):
    __tablename__ = "entities"

    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    first_seen_ns: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_seen_ns: Mapped[int] = mapped_column(BigInteger, nullable=False)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CursorModel(Base):
    __tablename__ = "cursors"

    ref: Mapped[str] = mapped_column(Text, primary_key=True)
    ts_ns: Mapped[int] = mapped_column(BigInteger, nullable=False)


class NodePositionModel(Base):
    __tablename__ = "node_positions"

    node_id: Mapped[str] = mapped_column(Text, primary_key=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    updated_ns: Mapped[int] = mapped_column(BigInteger, nullable=False)
