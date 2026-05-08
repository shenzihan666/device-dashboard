# API reference

Base URL is the same origin as the UI in production (`/`), or `http://localhost:8090` when hitting the backend directly. The Vite dev server proxies `/api` and `/ws` to port **8090**.

## Response envelope

Successful REST responses use a unified JSON shape:

```json
{
  "success": true,
  "data": { },
  "error": null,
  "error_code": null,
  "meta": null
}
```

Errors return `success: false` with `error` and `error_code` (and HTTP 4xx/5xx as appropriate). Validation errors from FastAPI use the same envelope.

## REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/state` | Current graph snapshot inside `data`; optional query `?at=<nanoseconds>` for replay |
| GET | `/api/events` | Recent events (query params: `from`, `to`, `kinds`, `host`, `serial`, `limit`) |
| GET | `/api/entities` | Optional `?kind=` filter; entity rows in `data` |
| GET | `/api/time_range` | Time range for the timeline (`data.min_ns`, `data.max_ns`) |
| GET | `/api/density` | Histogram buckets for the timeline |
| GET | `/api/status` | Poller status, WebSocket client count, time range, and poll config |
| GET | `/api/layout` | Saved positions: `data.positions` as `[{ node_id, x, y }]` |
| PUT | `/api/layout` | Body `{ "positions": [{ "node_id", "x", "y" }, ...] }` (at least one position) |
| DELETE | `/api/layout` | Clear saved positions (revert to auto-layout on next load) |

## WebSocket

| URL | Description |
|-----|-------------|
| `WS /ws/live` | Pushes `{ type: "event", payload: ... }` in live mode |

## Trace drill-through

When LangSmith is configured, event details may include a link to `/api/langsmith/trace?request_id=...` for trace inspection. Missing traces return HTTP 404 with the standard error envelope.
