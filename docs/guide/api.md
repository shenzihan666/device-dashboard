# API reference

Base URL is the same origin as the UI in production (`/`), or `http://localhost:8090` when hitting the backend directly. The Vite dev server proxies `/api` and `/ws` to port **8090**.

## REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/state` | Current graph snapshot; optional query `?at=<nanoseconds>` for replay |
| GET | `/api/events` | Recent events (supports query params as implemented by the backend) |
| GET | `/api/time_range` | Time range for the timeline |
| GET | `/api/density` | Histogram buckets for the timeline |
| GET | `/api/layout` | Saved positions: `{ positions: [{ node_id, x, y }] }` |
| PUT | `/api/layout` | Upsert one or more positions (JSON array or object) |
| DELETE | `/api/layout` | Clear saved positions (revert to auto-layout on next load) |

## WebSocket

| URL | Description |
|-----|-------------|
| `WS /ws/live` | Pushes `{ type: "event", payload: ... }` in live mode |

## Trace drill-through

When LangSmith is configured, event details may include a link to `/api/langsmith/trace?request_id=...` for trace inspection.
