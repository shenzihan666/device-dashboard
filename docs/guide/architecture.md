# Architecture

## Overview

The backend is a Python FastAPI application following **Clean Architecture** principles. It consists of three concentric layers with strict dependency rules:

```
Presentation (API) → Domain (Core) ← Infrastructure (Adapters)
```

The **domain layer** defines interfaces (Protocols); the **infrastructure layer** provides concrete implementations. The **presentation layer** composes everything via FastAPI's dependency injection system.

## Layer Responsibilities

### Core (Domain) Layer — `backend/core/`

Zero framework dependencies. Contains:

- **`domain/events.py`** — `Event` dataclass + kind constants (the central domain entity)
- **`domain/models.py`** — Value objects (`DeviceState`, `HostState`, `ServerState`, `GraphSnapshot`)
- **`ports/repositories.py`** — Protocol interfaces for database access (`EventRepository`, `EntityRepository`, `LayoutRepository`, `CursorRepository`)
- **`ports/services.py`** — Protocol interfaces for external services (`GrafanaClientPort`, `LangSmithClientPort`, `BroadcasterPort`)
- **`services/state_projector.py`** — In-memory CQRS-style projection: processes events, detects switches, offline/online transitions
- **`services/parser.py`** — Regex/JSON parsers for 5 log-line shapes
- **`services/poller_service.py`** — Background polling orchestration (Loki → parse → persist → project → broadcast)

### Infrastructure Layer — `backend/infrastructure/`

Concrete implementations of domain ports:

- **`database/models.py`** — SQLAlchemy 2.0 ORM table definitions
- **`database/session.py`** — Async engine and session factory
- **`database/repositories/`** — Repository implementations using SQLAlchemy async sessions
- **`external/grafana_client.py`** — Async httpx-based Grafana/Loki HTTP client
- **`external/langsmith_client.py`** — LangSmith trace lookup adapter
- **`websocket/broadcaster.py`** — WebSocket pub-sub fan-out

### Presentation (API) Layer — `backend/api/`

HTTP/WebSocket interface:

- **`routes/`** — FastAPI routers split by resource (events, state, entities, layout, status, langsmith, websocket)
- **`schemas/`** — Pydantic models for request validation and response serialization
- **`dependencies.py`** — `Depends()` providers wiring repositories and services
- **`middleware.py`** — Request ID correlation, response timing, CORS
- **`exception_handlers.py`** — Custom exception hierarchy → unified JSON error responses

## Data Flow

```
Grafana Loki → GrafanaClient (httpx async)
    → PollerService._fetch_and_process()
        → parser.parse_row() → Event dataclass
        → EventRepository.insert() → SQLite (via SQLAlchemy)
        → EntityRepository.upsert()
        → StateProjector.process() → synthetic events
        → Broadcaster.broadcast() → WebSocket clients
```

## Key Design Decisions

1. **Protocol-based DI** — Domain defines `Protocol` interfaces; infrastructure implements them. Easily mockable for testing.
2. **Async-first** — `aiosqlite` + SQLAlchemy async + `httpx.AsyncClient`. No thread-pool workarounds.
3. **Repository per aggregate** — Separate repos for events, entities, layout, cursors. Each has a focused interface.
4. **App factory pattern** — `create_app()` builds the FastAPI app; `lifespan` manages resource lifecycle.
5. **Unified response envelope** — All endpoints return `APIResponse[T]` with `success`, `data`, `error`, `error_code`, `meta`.
6. **Structured logging** — `structlog` with `request_id` correlation across all log entries.
7. **Fail-fast config** — `pydantic-settings` validates all environment variables at startup.

## Database

- **Engine**: SQLite via `aiosqlite` (configurable via `DB_URL`)
- **ORM**: SQLAlchemy 2.0 with `mapped_column` declarative style
- **Migrations**: Alembic with async engine support
- **Schema**: 4 tables (`events`, `entities`, `cursors`, `node_positions`)

## Configuration

All settings are managed via `backend/config.py` using `pydantic-settings`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAFANA_URL` | `https://mynameisi.grafana.net` | Grafana instance URL |
| `API_TOKEN` | `""` | Service account token for Grafana |
| `LOKI_DATASOURCE_UID` | `grafanacloud-logs` | Loki datasource UID |
| `LANGSMITH_API_KEY` | `""` | LangSmith API key |
| `POLL_INTERVAL_S` | `10` | Polling interval in seconds |
| `BACKFILL_HOURS` | `24` | Hours of history to backfill |
| `OFFLINE_GRACE_S` | `90` | Grace period before marking offline |
| `DB_URL` | `sqlite+aiosqlite:///data/events.db` | Database connection URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `console` | `"json"` for production, `"console"` for dev |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
