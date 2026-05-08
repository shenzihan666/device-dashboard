# Configuration

Copy `.env.example` to `.env` and adjust values. The backend loads them via **pydantic-settings** (`backend/config.py`) at startup (including from `.env`).

Environment variable names follow the usual uppercase convention; they map to the `Settings` fields below.

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TOKEN` | *(empty)* | Grafana service account token (`glsa_...`). When unset, the Loki poller does not start (offline/demo mode). |
| `GRAFANA_URL` | `https://mynameisi.grafana.net` | Grafana instance base URL |
| `LOKI_DATASOURCE_UID` | `grafanacloud-logs` | Loki datasource UID |
| `LANGSMITH_API_KEY` | *(optional)* | Enables LangSmith trace lookup from `/api/langsmith/trace` |
| `POLL_INTERVAL_S` | `10` | Seconds between Loki polls |
| `BACKFILL_HOURS` | `24` | Hours of history to load on first start |
| `OFFLINE_GRACE_S` | `90` | Seconds without activity before a device is marked offline |
| `DB_URL` | `sqlite+aiosqlite:///…/data/events.db` | Async SQLAlchemy database URL (project-relative `data/events.db` by default) |
| `LOG_LEVEL` | `INFO` | Root log level |
| `LOG_FORMAT` | `console` | `console` (human-readable) or `json` (structured logs) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins; use a JSON array in `.env` when overriding (e.g. `["http://localhost:5173"]`) |

Secrets and local overrides should stay in `.env` (gitignored). See the repository `.env.example` for the canonical template.

## Migrations

Schema is managed with **Alembic** (`alembic/`). For a fresh database you can run `uv run alembic upgrade head`; the app also ensures tables exist on startup for local development.
