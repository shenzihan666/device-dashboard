# Deployment

| Field | Value |
|-------|-------|
| **Author** | Team |
| **Last updated** | 2026-05-08 |
| **Audience** | Ops / Dev |
| **Frequency** | Per-release |

## Purpose

Step-by-step procedure for deploying the connection dashboard to a production or staging environment, and rolling back if needed.

## Prerequisites

- SSH or shell access to the target host.
- Python 3.11+ with [uv](https://docs.astral.sh/uv/) installed.
- Node.js and npm for building the frontend.
- A valid `.env` file with `API_TOKEN` set (see [Configuration](../guide/configuration.md)).
- Network access to the Grafana Loki instance.

## Procedure

### Step 1: Pull Latest Code

```bash
cd /opt/connection-dashboard    # or your deployment path
git fetch origin master
git checkout master
git pull origin master
```

### Step 2: Install Backend Dependencies

```bash
uv sync
```

Verify with `uv run python -c "import backend"`.

### Step 3: Build Frontend

```bash
cd frontend
npm ci
npm run build
cd ..
```

Verify `frontend/dist/index.html` exists.

### Step 4: Apply Environment Configuration

```bash
cp .env.example .env    # only on first deploy
# Edit .env with production values:
#   API_TOKEN=glsa_...
#   GRAFANA_URL=https://your-instance.grafana.net
#   POLL_INTERVAL_S=10
#   BACKFILL_HOURS=24
#   DB_URL=sqlite+aiosqlite:///data/events.db   # optional override
```

See [Configuration](../guide/configuration.md) for all variables.

### Step 4b: Database schema (optional)

On upgrades, apply Alembic migrations when you rely on versioned schema instead of startup auto-create:

```bash
uv run alembic upgrade head
```

### Step 5: Start the Application

```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090
```

For process management, wrap with systemd, supervisor, or Docker.

### Step 6: Verify

- Open `http://<host>:8090/` in a browser.
- Confirm the graph loads with live data.
- Check the WebSocket indicator shows "LIVE".
- Verify events appear in the feed within one poll interval.

## Rollback

If the deployment fails:

```bash
git checkout <previous-tag-or-commit>
uv sync
cd frontend && npm ci && npm run build && cd ..
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090
```

SQLite data is preserved across deployments. Roll back the Git revision first; re-run `uv run alembic upgrade head` only if the target revision expects a newer schema.

## Verification

| Check | Expected |
|-------|----------|
| `curl http://localhost:8090/api/state` | JSON envelope: `success` true and `data` containing `servers`, `devices`, `hosts`, `edges` |
| `curl http://localhost:8090/api/time_range` | JSON envelope: `data.min_ns` and `data.max_ns` (may be `null` when empty) |
| Browser → graph canvas | Nodes render; edges connect tiers |
| Browser → WebSocket status | Shows "LIVE" (green) |

## Related

- [Getting started](../guide/getting-started.md)
- [Configuration](../guide/configuration.md)
- [Troubleshooting](./troubleshooting.md)
