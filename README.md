# WeCom AI Connection Dashboard

Real-time dashboard tracking WeCom client (enterprise WeChat) connections to AI servers.

Polls Grafana Loki (`wecom-sidecar-logs`), parses structured log lines into connection events, persists to SQLite, and pushes updates via WebSocket to a browser SPA with:

- **Live workflow-style graph** — AI Server, desktop/device, and host as card nodes ([React Flow](https://reactflow.dev/) / `@xyflow/react`), dot background, controls, and minimap
- **View / Edit layout** — default view is read-only; **Edit** enables dragging nodes; positions persist in SQLite via `GET/PUT/DELETE /api/layout`
- **Event feed** — chronological right-side panel with switch / offline / error events
- **Timeline scrubber** — replay any past window; drag the scrubber to seek state and events

## Documentation

Structured docs live under **[docs/](docs/README.md)**:

- [Overview](docs/overview.md) · [Getting started](docs/getting-started.md) · [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md) · [Frontend](docs/frontend.md) · [API reference](docs/api.md) · [Development](docs/development.md)

## Quick start (production)

```bash
cp .env.example .env           # fill in API_TOKEN (required), LANGSMITH_API_KEY (optional)
uv sync
cd frontend && npm install && npm run build && cd ..
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090
```

Open `http://localhost:8090/`.

## Development (hot reload)

```bash
# Terminal A (repo root)
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090

# Terminal B
cd frontend && npm install && npm run dev    # http://localhost:5173
```

Vite proxies `/api` and `/ws` to port **8090**.

## Git hooks (pre-commit)

See [docs/development.md](docs/development.md) for full hook setup. Manual run:

```bash
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
```

## Out of scope (v1)

- Authentication / multi-tenant
- HTTPS (terminate at reverse proxy)
- Mobile layout
- Alerting / paging on switches
