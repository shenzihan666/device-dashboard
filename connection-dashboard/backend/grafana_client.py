"""
grafana_client.py
=================

A thin, well-typed wrapper around the Grafana HTTP API designed for ad-hoc
data analysis. It targets two endpoints:

    GET  /api/datasources           -> discover the UIDs you can query
    POST /api/ds/query              -> the unified backend query endpoint

The unified `/api/ds/query` endpoint accepts a list of per-datasource queries
plus a global time range (`from` / `to`) which can be Grafana relative
strings such as "now-24h" or epoch milliseconds. Reference:

    https://grafana.com/docs/grafana/latest/developers/http_api/data_source/#query-a-data-source

Each query returns one or more "frames". A frame has a schema (list of
fields) and a column-major data block (`data.values`). This module converts
those frames into pandas DataFrames so the rest of your analysis pipeline
can stay framework agnostic.

Authentication is via a Service Account token (Bearer header). On Grafana
Cloud the token starts with `glsa_` and lives in `.env` as `API_TOKEN`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd
import requests


class GrafanaError(RuntimeError):
    """Raised for any non-2xx response or query-level error from Grafana."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class GrafanaClient:
    """Minimal Grafana HTTP client focused on data extraction.

    Parameters
    ----------
    base_url:
        Root URL of the Grafana instance, e.g. ``https://mynameisi.grafana.net``.
        A trailing slash is stripped so URL joining stays predictable.
    token:
        Service Account token. Sent as ``Authorization: Bearer <token>``.
    timeout:
        Per-request timeout in seconds. Queries against Loki / Mimir over a
        long range can be slow, so 60s is a sensible default.
    """

    DEFAULT_TIMEOUT = 60

    def __init__(self, base_url: str, token: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # A persistent Session reuses the underlying TCP connection which is
        # noticeably faster when issuing several queries in a row.
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def list_datasources(self) -> list[dict]:
        """List every datasource the token can read.

        Requires the ``datasources:read`` permission on the service account.
        """
        return self._get_json(f"{self.base_url}/api/datasources")

    def get_datasource_by_uid(self, uid: str) -> dict:
        """Fetch a single datasource definition by UID."""
        return self._get_json(f"{self.base_url}/api/datasources/uid/{uid}")

    # ------------------------------------------------------------------
    # Query payload builders
    # ------------------------------------------------------------------
    # Each builder returns a single dict that you append into the
    # ``queries`` list passed to :meth:`query`. They exist so callers don't
    # need to remember the field names that each datasource expects.

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
        """Build a PromQL / MetricsQL (Mimir) query payload."""
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
        """Build a LogQL query payload.

        ``query_type`` can be ``"range"`` (logs over a window) or
        ``"instant"`` (snapshot). For metric queries built with LogQL you
        usually want ``"range"``.

        ``direction`` is ``"backward"`` (newest-first) or ``"forward"``;
        only meaningful for raw log queries, ignored for metric queries.

        ``step_ms`` overrides the bucket size used by metric queries (e.g.
        ``count_over_time``). If unset, Grafana picks one from the time
        range and panel width.

        Note: only ``intervalMs`` is sent -- adding ``step`` alongside it
        causes Grafana Cloud's Loki plugin to return HTTP 500.
        """
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
    def build_sql_query(
        uid: str,
        raw_sql: str,
        *,
        ref_id: str = "A",
        format_: str = "table",
        datasource_type: str = "postgres",
    ) -> dict:
        """Build a SQL query payload.

        ``datasource_type`` should match the actual plugin id, e.g.
        ``"postgres"``, ``"mysql"``, ``"mssql"``, ``"grafana-bigquery-datasource"``.
        """
        return {
            "refId": ref_id,
            "datasource": {"type": datasource_type, "uid": uid},
            "rawSql": raw_sql,
            "format": format_,
        }

    # ------------------------------------------------------------------
    # Core query method
    # ------------------------------------------------------------------

    def query(
        self,
        queries: list[dict],
        from_: str = "now-24h",
        to: str = "now",
    ) -> dict:
        """POST one or more queries to ``/api/ds/query``.

        Parameters
        ----------
        queries:
            A list of query dicts. Build them with the ``build_*`` helpers
            above or hand-craft them.
        from_, to:
            Either Grafana relative time strings (``"now-24h"``, ``"now-5m"``)
            or epoch milliseconds as strings/ints. The same window applies
            to every query in the batch.

        Returns
        -------
        dict
            The raw JSON response. Use :func:`response_to_dataframes` to
            convert it into pandas DataFrames keyed by ``refId``.
        """
        if not queries:
            raise ValueError("`queries` must contain at least one entry")

        payload = {"queries": queries, "from": str(from_), "to": str(to)}
        url = f"{self.base_url}/api/ds/query"

        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise GrafanaError(f"Network error talking to Grafana: {exc}") from exc

        # Grafana returns 200 even when *some* refIds errored; per-query
        # errors are surfaced inside the JSON body and inspected later.
        if resp.status_code >= 400:
            raise GrafanaError(f"POST /api/ds/query returned {resp.status_code}: {resp.text[:500]}")

        try:
            return resp.json()
        except ValueError as exc:  # pragma: no cover - defensive
            raise GrafanaError(f"Grafana returned non-JSON body: {resp.text[:200]}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_json(self, url: str) -> Any:
        try:
            resp = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise GrafanaError(f"Network error fetching {url}: {exc}") from exc
        if resp.status_code >= 400:
            raise GrafanaError(f"GET {url} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()


# ---------------------------------------------------------------------------
# Frame -> DataFrame conversion
# ---------------------------------------------------------------------------


def _column_label(field: dict) -> str:
    """Compose a unique, human-readable column label for a frame field.

    Prometheus and Loki ship the metric name + label set inside
    ``field.labels``; appending those keeps multiple series distinguishable
    when several frames are merged into one DataFrame.
    """
    name = field.get("name") or field.get("config", {}).get("displayNameFromDS") or "value"
    labels = field.get("labels") or {}
    if labels:
        suffix = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{suffix}}}"
    return name


def frame_to_dataframe(frame: dict) -> pd.DataFrame:
    """Convert one Grafana data frame into a pandas DataFrame.

    Time fields (epoch milliseconds) are converted to UTC timestamps so the
    resulting DataFrame is immediately usable for time-series analysis.
    Empty frames return an empty DataFrame instead of raising.
    """
    schema = frame.get("schema") or {}
    fields = schema.get("fields") or []
    columns = (frame.get("data") or {}).get("values") or []

    if not fields or not columns:
        return pd.DataFrame()

    series: dict[str, pd.Series] = {}
    for field, values in zip(fields, columns):
        label = _column_label(field)
        if field.get("type") == "time":
            # Grafana ships timestamps as epoch milliseconds.
            series[label] = pd.to_datetime(values, unit="ms", utc=True)
        else:
            series[label] = pd.Series(values)

    return pd.DataFrame(series)


def response_to_dataframes(response: dict) -> dict[str, pd.DataFrame]:
    """Convert every refId in a ``/api/ds/query`` response into a DataFrame.

    Each refId can carry multiple frames (one per series for Prometheus,
    one per stream for Loki, ...). When all frames share a time column we
    outer-merge on it to produce a wide time-indexed DataFrame; otherwise
    we concatenate row-wise.

    Per-query errors reported inside ``results[refId].error`` are raised
    as :class:`GrafanaError` so callers see them eagerly.
    """
    out: dict[str, pd.DataFrame] = {}
    results = (response or {}).get("results") or {}

    for ref_id, payload in results.items():
        # Grafana <=10 may use "error", >=11 sometimes uses "errors": [...].
        if payload.get("error"):
            raise GrafanaError(f"Query {ref_id!r} failed: {payload['error']}")
        if payload.get("errors"):
            raise GrafanaError(f"Query {ref_id!r} failed: {payload['errors']}")

        frames: Iterable[dict] = payload.get("frames") or []
        dfs = [frame_to_dataframe(f) for f in frames]
        dfs = [d for d in dfs if not d.empty]

        if not dfs:
            out[ref_id] = pd.DataFrame()
            continue

        if len(dfs) == 1:
            out[ref_id] = dfs[0]
            continue

        # Try to merge frames on a shared time column.
        time_cols_first = [c for c in dfs[0].columns if dfs[0][c].dtype.kind == "M"]
        share_time = bool(time_cols_first) and all(
            any(d[c].dtype.kind == "M" for c in d.columns) for d in dfs
        )

        if share_time:
            time_col = time_cols_first[0]
            merged = dfs[0]
            for d in dfs[1:]:
                # Pick this frame's first datetime column to merge against.
                d_time = next(c for c in d.columns if d[c].dtype.kind == "M")
                if d_time != time_col:
                    d = d.rename(columns={d_time: time_col})
                merged = merged.merge(d, on=time_col, how="outer")
            merged = merged.sort_values(time_col).reset_index(drop=True)
            out[ref_id] = merged
        else:
            out[ref_id] = pd.concat(dfs, ignore_index=True)

    return out
