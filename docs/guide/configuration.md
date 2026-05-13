# Configuration

Copy `.env.example` to `.env` and adjust values. The backend loads them via **pydantic-settings** (`backend/config.py`) at startup (including from `.env`).

Environment variable names follow the usual uppercase convention; they map to the `Settings` fields below.

| Variable | Default | Description |
|----------|---------|-------------|
| `OFFLINE_GRACE_S` | `90` | Seconds without activity before a device is marked offline |
| `DB_URL` | `sqlite+aiosqlite:///…/data/events.db` | Async SQLAlchemy database URL (project-relative `data/events.db` by default) |
| `LOG_LEVEL` | `INFO` | Root log level |
| `LOG_FORMAT` | `console` | `console` (human-readable) or `json` (structured logs) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins; use a JSON array in `.env` when overriding (e.g. `["http://localhost:5173"]`) |

Secrets and local overrides should stay in `.env` (gitignored). See the repository `.env.example` for the canonical template.

## Runtime toggles (database)

**Data source** switch (`point_to_point_enabled`) is stored in the **`app_settings`** table and read at startup. Default is **on** until you change it via the UI or `PUT /api/settings`. It survives process restarts independently of `.env`.

## Migrations

Schema is managed with **Alembic** (`alembic/`). For a fresh database you can run `uv run alembic upgrade head`; the app also ensures tables exist on startup for local development.
