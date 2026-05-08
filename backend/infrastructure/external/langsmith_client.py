"""LangSmith trace lookup client."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class LangSmithClient:
    """Adapter for LangSmith trace lookups."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def lookup_trace(self, request_id: str) -> dict[str, Any] | None:
        """Find a LangSmith run by request_id and return summary info."""
        if not self._api_key:
            return None

        try:
            from langsmith import Client

            client = Client(api_key=self._api_key)
            runs = list(
                client.list_runs(
                    filter=f'has(metadata, {{"request_id": "{request_id}"}})',
                    limit=1,
                )
            )

            if not runs:
                runs = list(
                    client.list_runs(
                        filter=f'eq(inputs.request_id, "{request_id}")',
                        limit=1,
                    )
                )

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
            logger.exception("langsmith_lookup_failed", request_id=request_id)
            return None
