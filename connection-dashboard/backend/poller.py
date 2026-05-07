"""Asyncio background task: polls Grafana Loki, parses, persists, broadcasts."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from backend import config
from backend.events import AI_SERVER_OBSERVED, HOST_DEVICE_MAP, Event
from backend.grafana_client import GrafanaClient, GrafanaError, response_to_dataframes
from backend.parser import parse_row
from backend.state import StateProjector
from backend.store import EventStore
from backend.ws import Broadcaster

logger = logging.getLogger(__name__)

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
}


class Poller:
    """Background Loki poller that drives the whole data pipeline."""

    def __init__(
        self,
        store: EventStore,
        state: StateProjector,
        broadcaster: Broadcaster,
    ) -> None:
        self.store = store
        self.state = state
        self.broadcaster = broadcaster
        self._client: GrafanaClient | None = None
        self._running = False

    def _get_client(self) -> GrafanaClient:
        if self._client is None:
            self._client = GrafanaClient(config.GRAFANA_URL, config.API_TOKEN)
        return self._client

    async def start(self) -> None:
        """Start the polling loop as an asyncio task."""
        self._running = True
        logger.info(
            "Poller starting: interval=%ds, backfill=%dh",
            config.POLL_INTERVAL_S,
            config.BACKFILL_HOURS,
        )
        await self._backfill()
        asyncio.create_task(self._poll_loop())
        asyncio.create_task(self._offline_check_loop())

    async def stop(self) -> None:
        self._running = False

    async def _backfill(self) -> None:
        """Load historical data on first start."""
        has_data = self.store.get_time_range()[0] is not None
        if has_data:
            logger.info("Database already has data, rebuilding state from stored events")
            events = self.store.query_events(limit=100000, order="ASC")
            self.state.rebuild_from_events(events)
            return

        logger.info("First start: backfilling %d hours of history", config.BACKFILL_HOURS)
        backfill_from_ns = int(
            (time.time() - config.BACKFILL_HOURS * 3600) * _NANO
        )
        from_ms = backfill_from_ns // 1_000_000

        for ref, spec in LOKI_QUERIES.items():
            await self._fetch_and_process(ref, spec, from_str=str(from_ms))
            self.store.set_cursor(ref, int(time.time() * _NANO))

        logger.info("Backfill complete")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("Poller tick failed")
            await asyncio.sleep(config.POLL_INTERVAL_S)

    async def _offline_check_loop(self) -> None:
        while self._running:
            await asyncio.sleep(30)
            try:
                synths = self.state.check_offline()
                for ev in synths:
                    self.store.insert_event(ev)
                    await self._broadcast_event(ev)
            except Exception:
                logger.exception("Offline check failed")

    async def _tick(self) -> None:
        now_ns = int(time.time() * _NANO)
        for ref, spec in LOKI_QUERIES.items():
            cursor_ns = self.store.get_cursor(ref)
            if cursor_ns:
                # Subtract 2s buffer to avoid "end before start" when cursor ≈ now
                safe_from_ns = cursor_ns - 2 * _NANO
                from_str = str(safe_from_ns // 1_000_000)
            else:
                from_str = f"now-{config.BACKFILL_HOURS}h"

            await self._fetch_and_process(ref, spec, from_str=from_str)
            self.store.set_cursor(ref, now_ns)

    async def _fetch_and_process(
        self, ref: str, spec: dict[str, Any], from_str: str
    ) -> None:
        client = self._get_client()
        query = client.build_loki_query(
            uid=config.LOKI_UID,
            expr=spec["expr"],
            ref_id=ref,
            query_type="range",
            max_lines=spec["max_lines"],
            direction="forward",
        )
        try:
            raw = await asyncio.to_thread(
                client.query, [query], from_str, "now"
            )
        except GrafanaError as exc:
            logger.warning("Loki query %s failed: %s", ref, exc)
            return

        df = response_to_dataframes(raw).get(ref)
        if df is None or df.empty:
            return

        new_count = 0
        for _, row in df.iterrows():
            line = str(row.get("Line", ""))
            ts_ns_raw = row.get("tsNs")
            labels = row.get("labels")

            if ts_ns_raw is not None:
                ts_ns = int(ts_ns_raw)
            else:
                ts_ns = int(time.time() * _NANO)

            event = parse_row(line, ts_ns, labels, ref)
            if event is None:
                continue

            row_id = self.store.insert_event(event)
            if row_id is None:
                continue

            new_count += 1

            # Update entities
            if event.device_serial:
                self.store.upsert_entity("device", event.device_serial, ts_ns)
            if event.host:
                self.store.upsert_entity("host", event.host, ts_ns)
            if event.ai_url and event.kind == AI_SERVER_OBSERVED:
                self.store.upsert_entity("server", event.ai_url, ts_ns)

            # State projection
            synths = self.state.process(event)
            for se in synths:
                self.store.insert_event(se)
                await self._broadcast_event(se)

            await self._broadcast_event(event)

        if new_count > 0:
            logger.info("Ref %s: inserted %d new events", ref, new_count)

    async def _broadcast_event(self, event: Event) -> None:
        await self.broadcaster.broadcast({
            "type": "event",
            "payload": event.to_dict(),
        })
