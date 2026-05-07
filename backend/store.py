"""SQLite persistence: events, entities, cursors.

All public methods are sync (using sqlite3 directly) since the poller runs
in a background thread and the FastAPI endpoints are thin wrappers.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from backend.events import Event

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY,
    ts_ns         INTEGER NOT NULL,
    kind          TEXT    NOT NULL,
    host          TEXT,
    device_serial TEXT,
    ai_url        TEXT,
    prev_ai_url   TEXT,
    status        TEXT,
    latency_ms    INTEGER,
    request_id    TEXT,
    session_id    TEXT,
    raw_line      TEXT,
    payload_json  TEXT
);

CREATE INDEX IF NOT EXISTS events_ts        ON events(ts_ns);
CREATE INDEX IF NOT EXISTS events_kind_ts   ON events(kind, ts_ns);
CREATE INDEX IF NOT EXISTS events_serial_ts ON events(device_serial, ts_ns);
CREATE UNIQUE INDEX IF NOT EXISTS events_dedupe
    ON events(ts_ns, kind, host, device_serial, ai_url);

CREATE TABLE IF NOT EXISTS entities (
    kind          TEXT NOT NULL,
    id            TEXT NOT NULL,
    first_seen_ns INTEGER NOT NULL,
    last_seen_ns  INTEGER NOT NULL,
    meta_json     TEXT,
    PRIMARY KEY (kind, id)
);

CREATE TABLE IF NOT EXISTS cursors (
    ref   TEXT PRIMARY KEY,
    ts_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS node_positions (
    node_id    TEXT PRIMARY KEY,
    x          REAL NOT NULL,
    y          REAL NOT NULL,
    updated_ns INTEGER NOT NULL
);
"""


class EventStore:
    """Thread-safe SQLite store for connection events."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    @property
    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── Insert ───────────────────────────────────────────────────────────

    def insert_event(self, ev: Event) -> int | None:
        """Insert an event. Returns the row id, or None if it was a duplicate."""
        payload_str = json.dumps(ev.payload, ensure_ascii=False) if ev.payload else None
        try:
            cur = self._conn.execute(
                """INSERT OR IGNORE INTO events
                   (ts_ns, kind, host, device_serial, ai_url, prev_ai_url,
                    status, latency_ms, request_id, session_id, raw_line, payload_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    ev.ts_ns,
                    ev.kind,
                    ev.host,
                    ev.device_serial,
                    ev.ai_url,
                    ev.prev_ai_url,
                    ev.status,
                    ev.latency_ms,
                    ev.request_id,
                    ev.session_id,
                    ev.raw_line,
                    payload_str,
                ),
            )
            self._conn.commit()
            return cur.lastrowid if cur.rowcount > 0 else None
        except sqlite3.IntegrityError:
            return None

    def insert_events(self, events: list[Event]) -> int:
        """Bulk insert, returns count of newly inserted rows."""
        inserted = 0
        for ev in events:
            if self.insert_event(ev) is not None:
                inserted += 1
        return inserted

    # ── Entity upsert ────────────────────────────────────────────────────

    def upsert_entity(
        self, kind: str, entity_id: str, ts_ns: int, meta: dict | None = None
    ) -> None:
        meta_str = json.dumps(meta, ensure_ascii=False) if meta else None
        self._conn.execute(
            """INSERT INTO entities (kind, id, first_seen_ns, last_seen_ns, meta_json)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(kind, id) DO UPDATE SET
                   last_seen_ns = MAX(excluded.last_seen_ns, entities.last_seen_ns),
                   meta_json = COALESCE(excluded.meta_json, entities.meta_json)""",
            (kind, entity_id, ts_ns, ts_ns, meta_str),
        )
        self._conn.commit()

    # ── Cursor ───────────────────────────────────────────────────────────

    def get_cursor(self, ref: str) -> int | None:
        row = self._conn.execute("SELECT ts_ns FROM cursors WHERE ref = ?", (ref,)).fetchone()
        return row["ts_ns"] if row else None

    def set_cursor(self, ref: str, ts_ns: int) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO cursors (ref, ts_ns) VALUES (?, ?)",
            (ref, ts_ns),
        )
        self._conn.commit()

    # ── Queries ──────────────────────────────────────────────────────────

    def query_events(
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
        clauses: list[str] = []
        params: list[Any] = []
        if from_ns is not None:
            clauses.append("ts_ns >= ?")
            params.append(from_ns)
        if to_ns is not None:
            clauses.append("ts_ns <= ?")
            params.append(to_ns)
        if kinds:
            placeholders = ",".join("?" for _ in kinds)
            clauses.append(f"kind IN ({placeholders})")
            params.extend(kinds)
        if host:
            clauses.append("host = ?")
            params.append(host)
        if serial:
            clauses.append("device_serial = ?")
            params.append(serial)

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM events{where} ORDER BY ts_ns {order} LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def query_events_up_to(self, ts_ns: int, limit: int = 50000) -> list[dict[str, Any]]:
        """All events up to a timestamp, ascending. Used for state reconstruction."""
        rows = self._conn.execute(
            "SELECT * FROM events WHERE ts_ns <= ? ORDER BY ts_ns ASC LIMIT ?",
            (ts_ns, limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_entities(self, kind: str | None = None) -> list[dict[str, Any]]:
        if kind:
            rows = self._conn.execute(
                "SELECT * FROM entities WHERE kind = ? ORDER BY last_seen_ns DESC", (kind,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM entities ORDER BY kind, last_seen_ns DESC"
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_event_density(
        self, from_ns: int, to_ns: int, buckets: int = 100
    ) -> list[dict[str, Any]]:
        """Return event counts per time bucket for the timeline histogram."""
        bucket_size = max(1, (to_ns - from_ns) // buckets)
        rows = self._conn.execute(
            """SELECT (ts_ns / ?) * ? AS bucket_ns, COUNT(*) AS cnt
               FROM events
               WHERE ts_ns >= ? AND ts_ns <= ?
               GROUP BY bucket_ns
               ORDER BY bucket_ns""",
            (bucket_size, bucket_size, from_ns, to_ns),
        ).fetchall()
        return [{"ts_ns": r["bucket_ns"], "count": r["cnt"]} for r in rows]

    def get_time_range(self) -> tuple[int | None, int | None]:
        """Return (min_ts_ns, max_ts_ns) across all events."""
        row = self._conn.execute("SELECT MIN(ts_ns) AS mn, MAX(ts_ns) AS mx FROM events").fetchone()
        if row and row["mn"] is not None:
            return (row["mn"], row["mx"])
        return (None, None)

    # ── Layout (node positions) ─────────────────────────────────────────

    def get_layout(self) -> list[dict[str, Any]]:
        """Return all saved node positions."""
        rows = self._conn.execute(
            "SELECT node_id, x, y FROM node_positions ORDER BY node_id"
        ).fetchall()
        return [{"node_id": r["node_id"], "x": r["x"], "y": r["y"]} for r in rows]

    def upsert_positions(self, items: list[dict[str, Any]], now_ns: int) -> None:
        """Batch upsert node positions."""
        for item in items:
            self._conn.execute(
                """INSERT INTO node_positions (node_id, x, y, updated_ns)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(node_id) DO UPDATE SET
                       x = excluded.x,
                       y = excluded.y,
                       updated_ns = excluded.updated_ns""",
                (item["node_id"], item["x"], item["y"], now_ns),
            )
        self._conn.commit()

    def clear_layout(self) -> None:
        """Delete all saved node positions (reset layout)."""
        self._conn.execute("DELETE FROM node_positions")
        self._conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        if d.get("payload_json"):
            try:
                d["payload_json"] = json.loads(d["payload_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d
