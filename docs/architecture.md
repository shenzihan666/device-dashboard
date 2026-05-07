# Architecture

## High-level diagram

```
Browser (React + Vite)  ←── WebSocket ──→  FastAPI backend  ←── HTTP ──→  Grafana Loki
         ↕                                        ↕
  React Flow graph                         SQLite (events + layout)
  event feed + timeline
```

## Backend

- **FastAPI** application (`backend/`) serves JSON APIs, WebSocket pushes, and optionally the built frontend from `frontend/dist`.
- **SQLite** stores ingested events and saved node positions for the graph (see [API reference](./api.md)).

## Frontend

- **Vite + React 19** SPA under `frontend/`.
- **React Flow** (`@xyflow/react`) renders nodes and edges; **Dagre** computes default positions when no saved layout exists (see [Frontend](./frontend.md)).

## Data path

1. Sidecar logs land in **Loki**.
2. The backend polls Loki, parses lines into **connection events**, updates **state snapshots** (servers, hosts, devices, edges).
3. The UI polls or replays `/api/state` and subscribes to `/ws/live` for incremental updates.
