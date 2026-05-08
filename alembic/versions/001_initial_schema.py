"""Initial schema - events, entities, cursors, node_positions.

Revision ID: 001
Revises: None
Create Date: 2026-05-08
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts_ns", sa.BigInteger, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("host", sa.Text, nullable=True),
        sa.Column("device_serial", sa.Text, nullable=True),
        sa.Column("ai_url", sa.Text, nullable=True),
        sa.Column("prev_ai_url", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("request_id", sa.Text, nullable=True),
        sa.Column("session_id", sa.Text, nullable=True),
        sa.Column("raw_line", sa.Text, nullable=True),
        sa.Column("payload_json", sa.Text, nullable=True),
    )
    op.create_index("events_ts", "events", ["ts_ns"])
    op.create_index("events_kind_ts", "events", ["kind", "ts_ns"])
    op.create_index("events_serial_ts", "events", ["device_serial", "ts_ns"])
    op.create_unique_constraint(
        "events_dedupe", "events", ["ts_ns", "kind", "host", "device_serial", "ai_url"]
    )

    op.create_table(
        "entities",
        sa.Column("kind", sa.Text, primary_key=True),
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("first_seen_ns", sa.BigInteger, nullable=False),
        sa.Column("last_seen_ns", sa.BigInteger, nullable=False),
        sa.Column("meta_json", sa.Text, nullable=True),
    )

    op.create_table(
        "cursors",
        sa.Column("ref", sa.Text, primary_key=True),
        sa.Column("ts_ns", sa.BigInteger, nullable=False),
    )

    op.create_table(
        "node_positions",
        sa.Column("node_id", sa.Text, primary_key=True),
        sa.Column("x", sa.Float, nullable=False),
        sa.Column("y", sa.Float, nullable=False),
        sa.Column("updated_ns", sa.BigInteger, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("node_positions")
    op.drop_table("cursors")
    op.drop_table("entities")
    op.drop_table("events")
