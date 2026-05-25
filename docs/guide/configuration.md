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

### File uploads

Uploaded files are stored under `uploads/` (override with `UPLOAD_DIR` if you add a custom path in settings). Configure retention and quotas via:

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_RETENTION_DAYS` | `30` | Delete uploaded files older than this many days (mtime); orphan CAS blobs are GC'd after link count drops |
| `UPLOAD_QUOTA_PER_IDENTITY_GB` | `5` | Per device/host identity cumulative quota; excess uploads return HTTP 413 |
| `UPLOAD_DISK_WATERMARK_PCT` | `85` | Reject new uploads when disk usage on the upload partition reaches this % (HTTP 507) |
| `UPLOAD_DISK_EMERGENCY_PCT` | `95` | During sweeps, delete oldest date directories until usage falls below the watermark |
| `UPLOAD_COMPRESS_KINDS` | `[".log", ".jsonl"]` | Extensions gzip-compressed on ingest unless the client already sent `Content-Encoding: gzip` |
| `UPLOAD_DEDUP_ENABLED` | `true` | Store blobs by SHA-256 and hardlink per upload path |
| `UPLOAD_SWEEPER_INTERVAL_MIN` | `60` | Background retention sweeper interval in minutes |

Also see `upload_max_size_mb` (100) and `upload_allowed_extensions` in `backend/config.py`.

Secrets and local overrides should stay in `.env` (gitignored). See the repository `.env.example` for the canonical template.

## Runtime toggles (database)

**Data source** switch (`point_to_point_enabled`) is stored in the **`app_settings`** table and read at startup. Default is **on** until you change it via the UI or `PUT /api/settings`. It survives process restarts independently of `.env`.

## Migrations

Schema is managed with **Alembic** (`alembic/`). For a fresh database you can run `uv run alembic upgrade head`; the app also ensures tables exist on startup for local development.
