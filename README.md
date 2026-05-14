# WeCom AI Connection Dashboard

Real-time dashboard tracking WeCom client (enterprise WeChat) connections to AI servers.

Receives real-time heartbeat events via WebSocket (`/ws/heartbeat`) from WeCom clients and brain servers; also supports manual file uploads. Events persist to SQLite and push over WebSocket to a browser SPA with:

- **Live workflow-style graph** — BrainServer, WeComClient, and WeComDevice as card nodes ([React Flow](https://reactflow.dev/) / `@xyflow/react`), dot background, controls, and minimap; **shell UI** uses a minimal light (Vercel-style) chrome around the canvas ([frontend theming](docs/guide/frontend.md#theming))
- **View / Edit layout** — default view is read-only; **Edit** enables dragging nodes; positions persist in SQLite via `GET/PUT/DELETE /api/layout`
- **Event feed** — chronological right-side panel with device launch/stop/AI-request/red-dot events
- **Timeline scrubber** — replay any past window; drag the scrubber to seek state and events

## Documentation

Structured docs live under **[docs/](docs/README.md)**:

- [Overview](docs/guide/overview.md) · [Getting started](docs/guide/getting-started.md) · [Configuration](docs/guide/configuration.md)
- [Architecture](docs/guide/architecture.md) · [Frontend](docs/guide/frontend.md) · [API reference](docs/guide/api.md) · [Development](docs/guide/development.md)

## Quick start (production)

```bash
cp .env.example .env
uv sync
cd frontend && npm install && npm run build && cd ..
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090
```

Open `http://localhost:8090/`.

## Development (hot reload)

```bash
# Terminal A (repo root)
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090 --reload

# Terminal B
cd frontend && npm install && npm run dev    # http://localhost:5173
```

Vite proxies `/api` and `/ws` to port **8090**.

## Backend Architecture (v2)

The backend follows **Clean Architecture** with three layers:

```
backend/
├── core/               # Domain layer (zero framework dependencies)
│   ├── domain/         # Entities, value objects, event kinds
│   ├── ports/          # Protocol interfaces (repositories, services)
│   └── services/       # Domain services (StateProjector, Parser)
├── infrastructure/     # Adapters implementing domain ports
│   ├── database/       # SQLAlchemy ORM + async repositories
│   └── websocket/      # WebSocket broadcaster
├── api/                # Presentation layer
│   ├── routes/         # FastAPI routers split by resource
│   ├── schemas/        # Pydantic request/response models
│   ├── dependencies.py # FastAPI Depends() DI providers
│   ├── middleware.py   # Request ID, timing, CORS
│   └── exception_handlers.py  # Unified error responses
├── config.py           # pydantic-settings typed configuration
├── logging_config.py   # structlog setup (JSON/console)
└── main.py             # App factory + lifespan
```

Key improvements over v1:
- **SQLAlchemy 2.0 async** + Alembic migrations (replaces raw `sqlite3`)
- **FastAPI `Depends()`** for all services (replaces module-level globals)
- **Pydantic schemas** for all request/response validation
- **Unified `APIResponse` envelope** across all endpoints
- **structlog** with correlation IDs (replaces `logging.basicConfig`)
- **Custom exception hierarchy** with proper HTTP status codes

## Database Migrations

```bash
# Apply migrations
uv run alembic upgrade head

# Auto-generate a new migration after model changes
uv run alembic revision --autogenerate -m "description"
```

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/       # Domain logic only
uv run pytest tests/api/        # HTTP contract tests
uv run pytest tests/integration/ # Repository + DB tests
```

## Git hooks (pre-commit)

See [docs/guide/development.md](docs/guide/development.md) for full hook setup. Manual run:

```bash
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
```

## Out of scope (v2)

- Authentication / multi-tenant
- HTTPS (terminate at reverse proxy)
- Mobile layout
- Alerting / paging on switches
