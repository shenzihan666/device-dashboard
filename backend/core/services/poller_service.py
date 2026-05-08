"""Background poller service: pulls Grafana Loki, parses, persists, broadcasts.

Uses injected repository and service ports rather than concrete implementations.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

from backend.config import Settings
from backend.core.domain.events import AI_SERVER_OBSERVED, Event
from backend.core.ports.repositories import (
    CursorRepository,
    EntityRepository,
    EventRepository,
)
from backend.core.ports.services import BroadcasterPort, GrafanaClientPort
from backend.core.services.parser import parse_row
from backend.core.services.state_projector import StateProjector

logger = structlog.get_logger(__name__)

_NANO = 1_000_000_000

LOKI_QUERIES: dict[str, dict[str, Any]] = {
    "A": {
        "expr": '{job="wecom-sidecar-logs"} |~ "AI Server: http"',
        "max_lines": 5000,
    },
    "B": {
        "expr": '{job="wecom-sidecar-logs"} |~ "AIHealthChecker"',
        "max_lines": 500,
    },
    "C": {
        "expr": '{job="wecom-sidecar-logs"} |~ "Server disconnected|Cannot connect"',
        "max_lines": 500,
    },
    "D": {
        "expr": '{job="wecom-sidecar-logs"} |~ "metrics_logger:_emit"',
        "max_lines": 2000,
    },
    "E": {
        "expr": '{job="wecom-sidecar-logs"} |~ "serial=[A-Z0-9]"',
        "max_lines": 200,
    },
    "F": {
        "expr": '{job="wecom-sidecar-logs"} |~ "priority users|No red dot users|Queue empty"',
        "max_lines": 500,
    },
}


class PollerService:
    """Background Loki poller that drives the whole data pipeline."""

    def __init__(
        self,
        settings: Settings,
        event_repo: EventRepository,
        entity_repo: EntityRepository,
        cursor_repo: CursorRepository,
        state: StateProjector,
        broadcaster: BroadcasterPort,
        grafana_client: GrafanaClientPort,
    ) -> None:
        self._settings = settings
        self._event_repo = event_repo
        self._entity_repo = entity_repo
        self._cursor_repo = cursor_repo
        self._state = state
        self._broadcaster = broadcaster
        self._grafana_client = grafana_client
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Start the polling loop as an asyncio task."""
        self._running = True
        logger.info(
            "poller_starting",
            interval_s=self._settings.poll_interval_s,
            backfill_hours=self._settings.backfill_hours,
        )
        await self._backfill()
        asyncio.create_task(self._poll_loop())
        asyncio.create_task(self._offline_check_loop())

    async def stop(self) -> None:
        self._running = False

    async def _backfill(self) -> None:
        """Load historical data on first start."""
        time_range = await self._event_repo.get_time_range()
        has_data = time_range[0] is not None

        if has_data:
            logger.info("rebuilding_state_from_stored_events")
            events = await self._event_repo.query(limit=100000, order="ASC")
            self._state.rebuild_from_events(events)
            return

        logger.info("backfill_starting", hours=self._settings.backfill_hours)
        backfill_from_ns = int((time.time() - self._settings.backfill_hours * 3600) * _NANO)
        from_ms = backfill_from_ns // 1_000_000

        for ref, spec in LOKI_QUERIES.items():
            await self._fetch_and_process(ref, spec, from_str=str(from_ms))
            await self._cursor_repo.set(ref, int(time.time() * _NANO))

        logger.info("backfill_complete")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("poller_tick_failed")
            await asyncio.sleep(self._settings.poll_interval_s)

    async def _offline_check_loop(self) -> None:
        while self._running:
            await asyncio.sleep(30)
            try:
                synths = self._state.check_offline()
                for ev in synths:
                    await self._event_repo.insert(ev)
                    await self._broadcast_event(ev)
            except Exception:
                logger.exception("offline_check_failed")

    async def _tick(self) -> None:
        now_ns = int(time.time() * _NANO)
        for ref, spec in LOKI_QUERIES.items():
            cursor_ns = await self._cursor_repo.get(ref)
            if cursor_ns:
                safe_from_ns = cursor_ns - 2 * _NANO
                from_str = str(safe_from_ns // 1_000_000)
            else:
                from_str = f"now-{self._settings.backfill_hours}h"

            await self._fetch_and_process(ref, spec, from_str=from_str)
            await self._cursor_repo.set(ref, now_ns)

    async def _fetch_and_process(self, ref: str, spec: dict[str, Any], from_str: str) -> None:
        query = self._grafana_client.build_loki_query(
            uid=self._settings.loki_datasource_uid,
            expr=spec["expr"],
            ref_id=ref,
            query_type="range",
            max_lines=spec["max_lines"],
            direction="forward",
        )
        try:
            raw = await self._grafana_client.query([query], from_str, "now")
        except Exception as exc:
            logger.warning("loki_query_failed", ref=ref, error=str(exc))
            return

        frames = self._extract_frames(raw, ref)
        if not frames:
            return

        new_count = 0
        for row_data in frames:
            line = row_data.get("line", "")
            ts_ns = row_data.get("ts_ns", int(time.time() * _NANO))
            labels = row_data.get("labels")

            event = parse_row(line, ts_ns, labels, ref)
            if event is None:
                continue

            row_id = await self._event_repo.insert(event)
            if row_id is None:
                continue

            new_count += 1

            if event.device_serial:
                await self._entity_repo.upsert("device", event.device_serial, ts_ns)
            if event.host:
                await self._entity_repo.upsert("host", event.host, ts_ns)
            if event.ai_url and event.kind == AI_SERVER_OBSERVED:
                await self._entity_repo.upsert("server", event.ai_url, ts_ns)

            synths = self._state.process(event)
            for se in synths:
                await self._event_repo.insert(se)
                await self._broadcast_event(se)

            await self._broadcast_event(event)

        if new_count > 0:
            logger.info("events_inserted", ref=ref, count=new_count)

    def _extract_frames(self, raw: dict, ref: str) -> list[dict[str, Any]]:
        """Extract log rows from Grafana response without pandas."""
        results = (raw or {}).get("results", {})
        payload = results.get(ref)
        if not payload:
            return []

        if payload.get("error") or payload.get("errors"):
            logger.warning("grafana_query_error", ref=ref, error=payload.get("error"))
            return []

        rows: list[dict[str, Any]] = []
        for frame in payload.get("frames", []):
            schema = frame.get("schema", {})
            fields = schema.get("fields", [])
            values = (frame.get("data") or {}).get("values", [])

            if not fields or not values:
                continue

            field_names = [f.get("name", "") for f in fields]
            num_rows = len(values[0]) if values else 0

            for i in range(num_rows):
                row_dict: dict[str, Any] = {}
                for j, name in enumerate(field_names):
                    row_dict[name] = values[j][i] if j < len(values) else None

                line = str(row_dict.get("Line", ""))
                ts_ns_raw = row_dict.get("tsNs")
                ts_ns = int(ts_ns_raw) if ts_ns_raw is not None else int(time.time() * _NANO)

                rows.append(
                    {
                        "line": line,
                        "ts_ns": ts_ns,
                        "labels": row_dict.get("labels"),
                    }
                )

        return rows

    async def _broadcast_event(self, event: Event) -> None:
        await self._broadcaster.broadcast(
            {
                "type": "event",
                "payload": event.to_dict(),
            }
        )
