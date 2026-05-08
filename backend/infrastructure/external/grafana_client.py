"""Async Grafana HTTP client using httpx.

Replaces the previous sync requests+pandas implementation with a fully async
httpx client that returns native Python dicts instead of DataFrames.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class GrafanaError(RuntimeError):
    """Raised for any non-2xx response or query-level error from Grafana."""


class GrafanaClient:
    """Async Grafana HTTP client focused on Loki data extraction.

    Parameters
    ----------
    base_url:
        Root URL of the Grafana instance.
    token:
        Service Account token (Bearer header).
    timeout:
        Per-request timeout in seconds.
    """

    DEFAULT_TIMEOUT = 60

    def __init__(self, base_url: str, token: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    async def list_datasources(self) -> list[dict]:
        return await self._get_json("/api/datasources")

    async def get_datasource_by_uid(self, uid: str) -> dict:
        return await self._get_json(f"/api/datasources/uid/{uid}")

    # ------------------------------------------------------------------
    # Query payload builders
    # ------------------------------------------------------------------

    @staticmethod
    def build_loki_query(
        uid: str,
        expr: str,
        *,
        ref_id: str = "A",
        max_lines: int = 1000,
        query_type: str = "range",
        direction: str = "backward",
        step_ms: int | None = None,
    ) -> dict:
        payload: dict = {
            "refId": ref_id,
            "datasource": {"type": "loki", "uid": uid},
            "expr": expr,
            "queryType": query_type,
            "maxLines": max_lines,
            "direction": direction,
        }
        if step_ms is not None:
            payload["intervalMs"] = step_ms
        return payload

    @staticmethod
    def build_prometheus_query(
        uid: str,
        expr: str,
        *,
        ref_id: str = "A",
        interval_ms: int = 15_000,
        max_data_points: int = 1000,
        instant: bool = False,
        format_: str = "time_series",
    ) -> dict:
        return {
            "refId": ref_id,
            "datasource": {"type": "prometheus", "uid": uid},
            "expr": expr,
            "instant": instant,
            "range": not instant,
            "intervalMs": interval_ms,
            "maxDataPoints": max_data_points,
            "format": format_,
        }

    # ------------------------------------------------------------------
    # Core query method
    # ------------------------------------------------------------------

    async def query(
        self,
        queries: list[dict],
        from_: str = "now-24h",
        to: str = "now",
    ) -> dict:
        """POST one or more queries to ``/api/ds/query``."""
        if not queries:
            raise ValueError("`queries` must contain at least one entry")

        payload = {"queries": queries, "from": str(from_), "to": str(to)}

        try:
            resp = await self._client.post("/api/ds/query", json=payload)
        except httpx.HTTPError as exc:
            raise GrafanaError(f"Network error talking to Grafana: {exc}") from exc

        if resp.status_code >= 400:
            raise GrafanaError(f"POST /api/ds/query returned {resp.status_code}: {resp.text[:500]}")

        try:
            return resp.json()
        except ValueError as exc:
            raise GrafanaError(f"Grafana returned non-JSON body: {resp.text[:200]}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_json(self, path: str) -> Any:
        try:
            resp = await self._client.get(path)
        except httpx.HTTPError as exc:
            raise GrafanaError(f"Network error fetching {path}: {exc}") from exc
        if resp.status_code >= 400:
            raise GrafanaError(f"GET {path} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()
