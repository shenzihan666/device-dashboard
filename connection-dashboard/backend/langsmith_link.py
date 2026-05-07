"""LangSmith drill-through: request_id -> trace URL/metadata."""

from __future__ import annotations

import logging
from typing import Any

from backend import config

logger = logging.getLogger(__name__)


async def lookup_trace(request_id: str) -> dict[str, Any] | None:
    """Find a LangSmith run by request_id and return summary info."""
    if not config.LANGSMITH_API_KEY:
        return None

    try:
        from langsmith import Client

        client = Client(api_key=config.LANGSMITH_API_KEY)
        runs = list(client.list_runs(
            filter=f'has(metadata, {{"request_id": "{request_id}"}})',
            limit=1,
        ))

        if not runs:
            runs = list(client.list_runs(
                filter=f'eq(inputs.request_id, "{request_id}")',
                limit=1,
            ))

        if not runs:
            return None

        r = runs[0]
        latency = None
        if r.start_time and r.end_time:
            latency = (r.end_time - r.start_time).total_seconds()

        return {
            "run_id": str(r.id),
            "name": r.name,
            "status": r.status,
            "latency_s": latency,
            "error": r.error,
            "trace_url": getattr(r, "url", None),
        }
    except Exception:
        logger.exception("LangSmith lookup failed for request_id=%s", request_id)
        return None
