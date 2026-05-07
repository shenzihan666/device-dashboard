# WeCom AI Connection Dashboard

Real-time dashboard tracking WeCom client (enterprise WeChat) connections to AI servers.

Polls Grafana Loki (`wecom-sidecar-logs`) every 10 seconds, parses structured log lines into connection events, persists to SQLite, and pushes updates via WebSocket to a browser SPA with:

- **Live workflow-style graph** — three tiers as card nodes: AI Server / PC Host / Device (serial), rendered with [React Flow](https://reactflow.dev/) (`@xyflow/react`), dot background, controls, and minimap
- **View / Edit layout** — default view is read-only; **Edit** enables dragging nodes; positions persist in SQLite via `GET/PUT/DELETE /api/layout`
- **Event feed** — chronological right-side panel with switch / offline / error events
- **Timeline scrubber** — replay any past window; drag the scrubber to seek state and events

## Quick start (production)

Build the frontend, then run the API (serves `frontend/dist` when present):

```bash
cd connection-dashboard
cp .env.example .env           # fill in API_TOKEN (required), LANGSMITH_API_KEY (optional)
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8090
```

Open `http://localhost:8090/` in a browser.

## Development (hot reload)

Run backend and Vite dev server in two terminals (Vite proxies `/api` and `/ws` to port 8090):

```bash
# Terminal A
cd connection-dashboard
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8090

# Terminal B
cd connection-dashboard/frontend
npm install
npm run dev    # http://localhost:5173
```

## Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `API_TOKEN` | *(required)* | Grafana service account token (`glsa_...`) |
| `GRAFANA_URL` | `https://mynameisi.grafana.net` | Grafana instance |
| `LOKI_DATASOURCE_UID` | `grafanacloud-logs` | Loki datasource UID |
| `LANGSMITH_API_KEY` | *(optional)* | Enables "Open in LangSmith" links |
| `POLL_INTERVAL_S` | `10` | Seconds between Loki polls |
| `BACKFILL_HOURS` | `24` | Hours of history to load on first start |
| `OFFLINE_GRACE_S` | `90` | Seconds without activity before flagging device offline |

## REST API (selected)

| Method | Path | Description |
|---|---|---|
| GET | `/api/state` | Current graph snapshot (optional `?at=` for replay) |
| GET | `/api/events` | Recent events |
| GET | `/api/layout` | Saved node positions `{ positions: [{ node_id, x, y }] }` |
| PUT | `/api/layout` | Upsert positions (JSON array or single object) |
| DELETE | `/api/layout` | Clear saved positions (reset to auto-layout) |
| WS | `/ws/live` | Push `{ type: "event", payload: ... }` in live mode |

## Architecture

```
Browser (React + Vite)  ←── WebSocket ──→  FastAPI backend  ←── HTTP ──→  Grafana Loki
         ↕                                        ↕
  React Flow graph                         SQLite (events + node_positions)
  event feed + timeline
```

## Out of scope (v1)

- Authentication / multi-tenant
- HTTPS (terminate at reverse proxy)
- Mobile layout
- Alerting / paging on switches
